"""
Referral and Reward Management Module
"""
import os
import sqlite3
import uuid
import hashlib
import qrcode
import json
from datetime import datetime
from io import BytesIO
import base64
from flask import request, jsonify, session, render_template, redirect, url_for, flash

# Reward issuers
class RewardIssuer:
    """Base class for reward issuers"""
    def issue_reward(self, advocate_id, amount, campaign_id, event_id):
        """Issue a reward to an advocate"""
        raise NotImplementedError("Subclasses must implement issue_reward")

class StripeGiftCardIssuer(RewardIssuer):
    """Issue rewards as Stripe gift cards"""
    def issue_reward(self, advocate_id, amount, campaign_id, event_id):
        """Issue a Stripe gift card"""
        # In a real implementation, this would call the Stripe API
        # For now, just log the reward
        print(f"Issuing Stripe gift card of ${amount} to advocate {advocate_id}")
        
        # Create reward record
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO rewards (advocate_id, campaign_id, event_id, reward_type, amount, status)
            VALUES (?, ?, ?, 'GIFT_CARD', ?, 'ISSUED')
        ''', (advocate_id, campaign_id, event_id, amount))
        
        reward_id = cursor.lastrowid
        
        # Update reward status
        cursor.execute('''
            UPDATE rewards
            SET fulfilled_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (reward_id,))
        
        conn.commit()
        conn.close()
        
        # Send email notification
        self._send_reward_email(advocate_id, amount, 'gift card')
        
        return reward_id
    
    def _send_reward_email(self, advocate_id, amount, reward_type):
        """Send reward email to advocate"""
        # In a real implementation, this would use the existing send_email function
        # For now, just log the email
        print(f"Sending reward email to advocate {advocate_id} for ${amount} {reward_type}")

class AccountCreditIssuer(RewardIssuer):
    """Issue rewards as account credits"""
    def issue_reward(self, advocate_id, amount, campaign_id, event_id):
        """Issue an account credit"""
        # Create reward record
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO rewards (advocate_id, campaign_id, event_id, reward_type, amount, status)
            VALUES (?, ?, ?, 'CREDIT', ?, 'ISSUED')
        ''', (advocate_id, campaign_id, event_id, amount))
        
        reward_id = cursor.lastrowid
        
        # Update user account credit (would be in a separate table in a real implementation)
        # For now, just log the credit
        print(f"Adding ${amount} credit to advocate {advocate_id}")
        
        # Update reward status
        cursor.execute('''
            UPDATE rewards
            SET fulfilled_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (reward_id,))
        
        conn.commit()
        conn.close()
        
        # Send email notification
        self._send_reward_email(advocate_id, amount, 'account credit')
        
        return reward_id
    
    def _send_reward_email(self, advocate_id, amount, reward_type):
        """Send reward email to advocate"""
        # In a real implementation, this would use the existing send_email function
        print(f"Sending reward email to advocate {advocate_id} for ${amount} {reward_type}")

class ManualSwagIssuer(RewardIssuer):
    """Issue rewards as manual swag items"""
    def issue_reward(self, advocate_id, amount, campaign_id, event_id):
        """Queue a manual swag reward"""
        # Create reward record
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO rewards (advocate_id, campaign_id, event_id, reward_type, amount, status)
            VALUES (?, ?, ?, 'SWAG', ?, 'PENDING')
        ''', (advocate_id, campaign_id, event_id, amount))
        
        reward_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Notify admin about pending swag reward
        print(f"Notifying admin about pending swag reward for advocate {advocate_id}")
        
        return reward_id

# Reward engine
class RewardEngine:
    """Reward engine for processing referral rewards"""
    def __init__(self):
        self.issuers = {
            'GIFT_CARD': StripeGiftCardIssuer(),
            'CREDIT': AccountCreditIssuer(),
            'SWAG': ManualSwagIssuer()
        }
    
    def process_reward(self, event_id):
        """Process a reward for a referral event"""
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        # Get event details
        cursor.execute('''
            SELECT e.id, e.code_id, e.referred_patient_id, e.status,
                   c.advocate_id, c.campaign_id,
                   camp.reward_type, camp.reward_value
            FROM referral_events e
            JOIN referral_codes c ON e.code_id = c.id
            JOIN referral_campaigns camp ON c.campaign_id = camp.id
            WHERE e.id = ?
        ''', (event_id,))
        
        event = cursor.fetchone()
        if not event:
            conn.close()
            return None
        
        event_id, code_id, referred_patient_id, status, advocate_id, campaign_id, reward_type, reward_value = event
        
        # Check if event is eligible for reward
        if status != 'CONVERTED':
            conn.close()
            return None
        
        # Check if reward already issued
        cursor.execute('''
            SELECT id FROM rewards
            WHERE event_id = ?
        ''', (event_id,))
        
        if cursor.fetchone():
            conn.close()
            return None
        
        # Check for tiered rewards
        reward_amount = self._calculate_tiered_reward(advocate_id, campaign_id, reward_value)
        
        conn.close()
        
        # Issue reward using appropriate issuer
        issuer = self.issuers.get(reward_type)
        if not issuer:
            print(f"Unknown reward type: {reward_type}")
            return None
        
        return issuer.issue_reward(advocate_id, reward_amount, campaign_id, event_id)
    
    def _calculate_tiered_reward(self, advocate_id, campaign_id, base_reward):
        """Calculate tiered reward based on number of successful referrals"""
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        # Count successful referrals by this advocate for this campaign
        cursor.execute('''
            SELECT COUNT(*) FROM referral_events e
            JOIN referral_codes c ON e.code_id = c.id
            WHERE c.advocate_id = ? AND c.campaign_id = ? AND e.status = 'CONVERTED'
        ''', (advocate_id, campaign_id))
        
        referral_count = cursor.fetchone()[0]
        conn.close()
        
        # Apply tiered rewards
        # This is a simple example; real implementation would be more sophisticated
        if referral_count >= 10:
            return base_reward * 1.5  # 50% bonus for 10+ referrals
        elif referral_count >= 5:
            return base_reward * 1.2  # 20% bonus for 5+ referrals
        else:
            return base_reward

# Fraud detection
class FraudDetector:
    """Detect potential fraud in referral system"""
    def check_referral(self, code_id, referred_patient_id, ip_addr, user_agent):
        """Check if a referral might be fraudulent"""
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        fraud_score = 0
        fraud_reasons = []
        
        # Check for multiple sign-ups from same IP
        cursor.execute('''
            SELECT COUNT(*) FROM referral_events
            WHERE ip_addr = ? AND created_at > datetime('now', '-1 day')
        ''', (ip_addr,))
        
        ip_count = cursor.fetchone()[0]
        if ip_count > 3:
            fraud_score += 2
            fraud_reasons.append(f"Multiple sign-ups ({ip_count}) from same IP")
        
        # Check for advocate referring themselves
        cursor.execute('''
            SELECT advocate_id FROM referral_codes
            WHERE id = ?
        ''', (code_id,))
        
        advocate_id = cursor.fetchone()[0]
        if advocate_id == referred_patient_id:
            fraud_score += 5
            fraud_reasons.append("Advocate referring themselves")
        
        # Check for rapid-fire referrals
        cursor.execute('''
            SELECT COUNT(*) FROM referral_events
            WHERE code_id = ? AND created_at > datetime('now', '-1 hour')
        ''', (code_id,))
        
        recent_count = cursor.fetchone()[0]
        if recent_count > 5:
            fraud_score += 3
            fraud_reasons.append(f"Rapid-fire referrals ({recent_count} in last hour)")
        
        # Get campaign fraud threshold
        cursor.execute('''
            SELECT camp.fraud_threshold
            FROM referral_codes c
            JOIN referral_campaigns camp ON c.campaign_id = camp.id
            WHERE c.id = ?
        ''', (code_id,))
        
        result = cursor.fetchone()
        fraud_threshold = result[0] if result else 3
        
        # Update code if fraud threshold exceeded
        if fraud_score >= fraud_threshold:
            cursor.execute('''
                UPDATE referral_codes
                SET reward_status = 'FLAGGED'
                WHERE id = ?
            ''', (code_id,))
            conn.commit()
        
        conn.close()
        
        return {
            'score': fraud_score,
            'threshold': fraud_threshold,
            'flagged': fraud_score >= fraud_threshold,
            'reasons': fraud_reasons
        }

# Helper functions
def generate_referral_code():
    """Generate a unique referral code"""
    return ''.join(str(uuid.uuid4()).split('-')[0:2]).upper()

def generate_link_slug():
    """Generate a unique link slug for referral URLs"""
    return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:8]

def generate_qr_code(data):
    """Generate QR code for referral link"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode()

def create_referral_code(campaign_id, advocate_id):
    """Create a new referral code for an advocate"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Check if advocate already has a code for this campaign
    cursor.execute('''
        SELECT id, code, link_slug, qr_svg FROM referral_codes
        WHERE campaign_id = ? AND advocate_id = ?
    ''', (campaign_id, advocate_id))
    
    existing_code = cursor.fetchone()
    if existing_code:
        conn.close()
        return {
            'id': existing_code[0],
            'code': existing_code[1],
            'link_slug': existing_code[2],
            'qr_svg': existing_code[3]
        }
    
    # Generate new code
    code = generate_referral_code()
    link_slug = generate_link_slug()
    
    # Generate QR code
    base_url = os.environ.get('BASE_URL', 'http://localhost:5000')
    qr_data = f"{base_url}/r/{link_slug}"
    qr_svg = generate_qr_code(qr_data)
    
    # Insert code
    cursor.execute('''
        INSERT INTO referral_codes (campaign_id, advocate_id, code, link_slug, qr_svg)
        VALUES (?, ?, ?, ?, ?)
    ''', (campaign_id, advocate_id, code, link_slug, qr_svg))
    
    code_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        'id': code_id,
        'code': code,
        'link_slug': link_slug,
        'qr_svg': qr_svg
    }

def record_referral_event(code_id, referred_patient_id, status):
    """Record a referral event"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get IP and user agent
    ip_addr = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    
    # Insert event
    cursor.execute('''
        INSERT INTO referral_events (code_id, referred_patient_id, status, ip_addr, user_agent)
        VALUES (?, ?, ?, ?, ?)
    ''', (code_id, referred_patient_id, status, ip_addr, user_agent))
    
    event_id = cursor.lastrowid
    
    # Update code usage count
    cursor.execute('''
        UPDATE referral_codes
        SET usage_count = usage_count + 1
        WHERE id = ?
    ''', (code_id,))
    
    conn.commit()
    
    # Check for fraud
    fraud_detector = FraudDetector()
    fraud_result = fraud_detector.check_referral(code_id, referred_patient_id, ip_addr, user_agent)
    
    # If event is CONVERTED, process reward
    if status == 'CONVERTED':
        reward_engine = RewardEngine()
        reward_engine.process_reward(event_id)
    
    conn.close()
    
    return {
        'event_id': event_id,
        'fraud_result': fraud_result
    }

# API endpoints for referral campaigns
def get_campaigns():
    """Get list of referral campaigns"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Check if user is admin
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
    role = cursor.fetchone()[0]
    
    if role not in ['admin', 'dentist_admin', 'specialist_admin']:
        conn.close()
        return jsonify({'error': 'Access denied'}), 403
    
    # Get campaigns
    cursor.execute('''
        SELECT * FROM referral_campaigns
        ORDER BY created_at DESC
    ''')
    
    campaigns = []
    for row in cursor.fetchall():
        campaigns.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'start_date': row[3],
            'end_date': row[4],
            'advocate_role': row[5],
            'reward_type': row[6],
            'reward_value': float(row[7]),
            'reward_trigger': row[8],
            'max_referrals_per_advocate': row[9],
            'fraud_threshold': row[10],
            'is_active': bool(row[11]),
            'created_at': row[12],
            'updated_at': row[13]
        })
    
    conn.close()
    
    return jsonify({'campaigns': campaigns})

def get_campaign(campaign_id):
    """Get a specific campaign"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Check if user is admin
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
    role = cursor.fetchone()[0]
    
    if role not in ['admin', 'dentist_admin', 'specialist_admin']:
        conn.close()
        return jsonify({'error': 'Access denied'}), 403
    
    # Get campaign
    cursor.execute('''
        SELECT * FROM referral_campaigns
        WHERE id = ?
    ''', (campaign_id,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Campaign not found'}), 404
    
    campaign = {
        'id': row[0],
        'name': row[1],
        'description': row[2],
        'start_date': row[3],
        'end_date': row[4],
        'advocate_role': row[5],
        'reward_type': row[6],
        'reward_value': float(row[7]),
        'reward_trigger': row[8],
        'max_referrals_per_advocate': row[9],
        'fraud_threshold': row[10],
        'is_active': bool(row[11]),
        'created_at': row[12],
        'updated_at': row[13]
    }
    
    # Get campaign stats
    cursor.execute('''
        SELECT 
            COUNT(DISTINCT rc.id) as total_codes,
            COUNT(DISTINCT re.id) as total_events,
            SUM(CASE WHEN re.status = 'SIGNED_UP' THEN 1 ELSE 0 END) as signups,
            SUM(CASE WHEN re.status = 'CONVERTED' THEN 1 ELSE 0 END) as conversions,
            SUM(CASE WHEN r.status = 'ISSUED' THEN 1 ELSE 0 END) as rewards_issued,
            SUM(CASE WHEN r.status = 'PENDING' THEN 1 ELSE 0 END) as rewards_pending,
            SUM(CASE WHEN rc.reward_status = 'FLAGGED' THEN 1 ELSE 0 END) as fraud_flags,
            SUM(r.amount) as total_reward_value
        FROM referral_campaigns c
        LEFT JOIN referral_codes rc ON c.id = rc.campaign_id
        LEFT JOIN referral_events re ON rc.id = re.code_id
        LEFT JOIN rewards r ON re.id = r.event_id
        WHERE c.id = ?
        GROUP BY c.id
    ''', (campaign_id,))
    
    stats_row = cursor.fetchone()
    if stats_row:
        campaign['stats'] = {
            'total_codes': stats_row[0] or 0,
            'total_events': stats_row[1] or 0,
            'signups': stats_row[2] or 0,
            'conversions': stats_row[3] or 0,
            'rewards_issued': stats_row[4] or 0,
            'rewards_pending': stats_row[5] or 0,
            'fraud_flags': stats_row[6] or 0,
            'total_reward_value': float(stats_row[7] or 0)
        }
    else:
        campaign['stats'] = {
            'total_codes': 0,
            'total_events': 0,
            'signups': 0,
            'conversions': 0,
            'rewards_issued': 0,
            'rewards_pending': 0,
            'fraud_flags': 0,
            'total_reward_value': 0.0
        }
    
    conn.close()
    
    return jsonify({'campaign': campaign})

def create_campaign():
    """Create a new campaign"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Check CSRF token
    token = request.json.get('csrf_token')
    if not token or token != session.get('csrf_token'):
        return jsonify({'error': 'Invalid CSRF token'}), 403
    
    # Check if user is admin
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
    role = cursor.fetchone()[0]
    
    if role not in ['admin', 'dentist_admin', 'specialist_admin']:
        conn.close()
        return jsonify({'error': 'Access denied'}), 403
    
    # Get request data
    data = request.json
    name = data.get('name')
    description = data.get('description', '')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    advocate_role = data.get('advocate_role')
    reward_type = data.get('reward_type')
    reward_value = data.get('reward_value')
    reward_trigger = data.get('reward_trigger')
    max_referrals_per_advocate = data.get('max_referrals_per_advocate', -1)
    fraud_threshold = data.get('fraud_threshold', 3)
    is_active = data.get('is_active', True)
    
    # Validate required fields
    if not all([name, start_date, end_date, advocate_role, reward_type, reward_value, reward_trigger]):
        conn.close()
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate reward type
    valid_reward_types = ['GIFT_CARD', 'CREDIT', 'SWAG']
    if reward_type not in valid_reward_types:
        conn.close()
        return jsonify({'error': f'Invalid reward type. Must be one of: {", ".join(valid_reward_types)}'}), 400
    
    # Validate reward trigger
    valid_triggers = ['SIGNED_UP', 'CONVERTED']
    if reward_trigger not in valid_triggers:
        conn.close()
        return jsonify({'error': f'Invalid reward trigger. Must be one of: {", ".join(valid_triggers)}'}), 400
    
    # Insert campaign
    try:
        cursor.execute('''
            INSERT INTO referral_campaigns 
            (name, description, start_date, end_date, advocate_role, reward_type, 
             reward_value, reward_trigger, max_referrals_per_advocate, fraud_threshold, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, description, start_date, end_date, advocate_role, reward_type, 
              reward_value, reward_trigger, max_referrals_per_advocate, fraud_threshold, is_active))
        
        campaign_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Campaign created successfully',
            'id': campaign_id
        }), 201
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': f'Failed to create campaign: {str(e)}'}), 500

def update_campaign(campaign_id):
    """Update an existing campaign"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Check CSRF token
    token = request.json.get('csrf_token')
    if not token or token != session.get('csrf_token'):
        return jsonify({'error': 'Invalid CSRF token'}), 403
    
    # Check if user is admin
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
    role = cursor.fetchone()[0]
    
    if role not in ['admin', 'dentist_admin', 'specialist_admin']:
        conn.close()
        return jsonify({'error': 'Access denied'}), 403
    
    # Check if campaign exists
    cursor.execute('SELECT id FROM referral_campaigns WHERE id = ?', (campaign_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Campaign not found'}), 404
    
    # Get request data
    data = request.json
    
    # Build update query
    update_fields = []
    params = []
    
    if 'name' in data:
        update_fields.append('name = ?')
        params.append(data['name'])
    
    if 'description' in data:
        update_fields.append('description = ?')
        params.append(data['description'])
    
    if 'start_date' in data:
        update_fields.append('start_date = ?')
        params.append(data['start_date'])
    
    if 'end_date' in data:
        update_fields.append('end_date = ?')
        params.append(data['end_date'])
    
    if 'advocate_role' in data:
        update_fields.append('advocate_role = ?')
        params.append(data['advocate_role'])
    
    if 'reward_type' in data:
        # Validate reward type
        valid_reward_types = ['GIFT_CARD', 'CREDIT', 'SWAG']
        if data['reward_type'] not in valid_reward_types:
            conn.close()
            return jsonify({'error': f'Invalid reward type. Must be one of: {", ".join(valid_reward_types)}'}), 400
        
        update_fields.append('reward_type = ?')
        params.append(data['reward_type'])
    
    if 'reward_value' in data:
        update_fields.append('reward_value = ?')
        params.append(data['reward_value'])
    
    if 'reward_trigger' in data:
        # Validate reward trigger
        valid_triggers = ['SIGNED_UP', 'CONVERTED']
        if data['reward_trigger'] not in valid_triggers:
            conn.close()
            return jsonify({'error': f'Invalid reward trigger. Must be one of: {", ".join(valid_triggers)}'}), 400
        
        update_fields.append('reward_trigger = ?')
        params.append(data['reward_trigger'])
    
    if 'max_referrals_per_advocate' in data:
        update_fields.append('max_referrals_per_advocate = ?')
        params.append(data['max_referrals_per_advocate'])
    
    if 'fraud_threshold' in data:
        update_fields.append('fraud_threshold = ?')
        params.append(data['fraud_threshold'])
    
    if 'is_active' in data:
        update_fields.append('is_active = ?')
        params.append(data['is_active'])
    
    # Add updated_at timestamp
    update_fields.append('updated_at = CURRENT_TIMESTAMP')
    
    # If no fields to update, return error
    if not update_fields:
        conn.close()
        return jsonify({'error': 'No fields to update'}), 400
    
    # Update campaign
    try:
        query = f'UPDATE referral_campaigns SET {", ".join(update_fields)} WHERE id = ?'
        params.append(campaign_id)
        cursor.execute(query, params)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Campaign updated successfully'
        })
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': f'Failed to update campaign: {str(e)}'}), 500

def delete_campaign(campaign_id):
    """Delete a campaign"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Check CSRF token
    token = request.json.get('csrf_token')
    if not token or token != session.get('csrf_token'):
        return jsonify({'error': 'Invalid CSRF token'}), 403
    
    # Check if user is admin
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
    role = cursor.fetchone()[0]
    
    if role not in ['admin', 'dentist_admin', 'specialist_admin']:
        conn.close()
        return jsonify({'error': 'Access denied'}), 403
    
    # Check if campaign exists
    cursor.execute('SELECT id FROM referral_campaigns WHERE id = ?', (campaign_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Campaign not found'}), 404
    
    # Delete campaign
    try:
        # First delete related records
        cursor.execute('''
            DELETE FROM rewards
            WHERE campaign_id = ?
        ''', (campaign_id,))
        
        cursor.execute('''
            DELETE FROM referral_events
            WHERE code_id IN (SELECT id FROM referral_codes WHERE campaign_id = ?)
        ''', (campaign_id,))
        
        cursor.execute('''
            DELETE FROM referral_codes
            WHERE campaign_id = ?
        ''', (campaign_id,))
        
        # Finally delete campaign
        cursor.execute('''
            DELETE FROM referral_campaigns
            WHERE id = ?
        ''', (campaign_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Campaign deleted successfully'
        })
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': f'Failed to delete campaign: {str(e)}'}), 500

# API endpoints for referral codes
def get_advocate_codes():
    """Get referral codes for the current user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get user's role
    cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
    role = cursor.fetchone()[0]
    
    # Get active campaigns for this role
    cursor.execute('''
        SELECT c.id, c.name, c.description, c.reward_type, c.reward_value, c.reward_trigger
        FROM referral_campaigns c
        WHERE c.is_active = TRUE
        AND c.advocate_role = ?
        AND c.start_date <= datetime('now')
        AND c.end_date >= datetime('now')
    ''', (role,))
    
    campaigns = []
    for row in cursor.fetchall():
        campaign_id = row[0]
        
        # Get or create referral code for this campaign
        code_info = create_referral_code(campaign_id, session['user_id'])
        
        # Get referral stats
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT re.id) as total_referrals,
                SUM(CASE WHEN re.status = 'SIGNED_UP' THEN 1 ELSE 0 END) as signups,
                SUM(CASE WHEN re.status = 'CONVERTED' THEN 1 ELSE 0 END) as conversions,
                SUM(r.amount) as total_rewards
            FROM referral_codes rc
            LEFT JOIN referral_events re ON rc.id = re.code_id
            LEFT JOIN rewards r ON re.id = r.event_id
            WHERE rc.id = ?
        ''', (code_info['id'],))
        
        stats_row = cursor.fetchone()
        
        # Get base URL
        base_url = os.environ.get('BASE_URL', 'http://localhost:5000')
        
        campaigns.append({
            'id': campaign_id,
            'name': row[1],
            'description': row[2],
            'reward_type': row[3],
            'reward_value': float(row[4]),
            'reward_trigger': row[5],
            'code': code_info['code'],
            'link': f"{base_url}/r/{code_info['link_slug']}",
            'qr_svg': code_info['qr_svg'],
            'stats': {
                'total_referrals': stats_row[0] or 0,
                'signups': stats_row[1] or 0,
                'conversions': stats_row[2] or 0,
                'total_rewards': float(stats_row[3] or 0)
            }
        })
    
    conn.close()
    
    return jsonify({'campaigns': campaigns})

# Webhook endpoint for marking conversions
def webhook_appointment_completed():
    """Webhook endpoint for marking referrals as converted when appointments are completed"""
    # Verify webhook signature (in a real implementation)
    # ...
    
    data = request.json
    patient_id = data.get('patient_id')
    
    if not patient_id:
        return jsonify({'error': 'Missing patient_id'}), 400
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Find the most recent SIGNED_UP event for this patient
    cursor.execute('''
        SELECT e.id, e.code_id
        FROM referral_events e
        WHERE e.referred_patient_id = ? AND e.status = 'SIGNED_UP'
        ORDER BY e.created_at DESC
        LIMIT 1
    ''', (patient_id,))
    
    event = cursor.fetchone()
    if not event:
        conn.close()
        return jsonify({'message': 'No referral event found for this patient'}), 200
    
    event_id, code_id = event
    
    # Update event status to CONVERTED
    cursor.execute('''
        UPDATE referral_events
        SET status = 'CONVERTED', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (event_id,))
    
    conn.commit()
    conn.close()
    
    # Process reward
    reward_engine = RewardEngine()
    reward_id = reward_engine.process_reward(event_id)
    
    return jsonify({
        'success': True,
        'message': 'Appointment completed and referral converted',
        'event_id': event_id,
        'reward_processed': reward_id is not None
    })

# Register routes with Flask app
def register_routes(app):
    """Register routes with Flask app"""
    # API endpoints
    app.add_url_rule('/api/referral/campaigns', 'get_campaigns', get_campaigns, methods=['GET'])
    app.add_url_rule('/api/referral/campaigns/<int:campaign_id>', 'get_campaign', get_campaign, methods=['GET'])
    app.add_url_rule('/api/referral/campaigns', 'create_campaign', create_campaign, methods=['POST'])
    app.add_url_rule('/api/referral/campaigns/<int:campaign_id>', 'update_campaign', update_campaign, methods=['PUT'])
    app.add_url_rule('/api/referral/campaigns/<int:campaign_id>', 'delete_campaign', delete_campaign, methods=['DELETE'])
    app.add_url_rule('/api/referral/codes', 'get_advocate_codes', get_advocate_codes, methods=['GET'])
    app.add_url_rule('/webhooks/appointments/completed', 'webhook_appointment_completed', webhook_appointment_completed, methods=['POST'])
    
    # Page routes
    @app.route('/admin/campaigns')
    def admin_campaigns():
        """Admin campaigns management page"""
        if 'user_id' not in session or session.get('role') not in ['admin', 'dentist_admin', 'specialist_admin']:
            flash('Access denied. Administrator privileges required.', 'error')
            return redirect(url_for('login'))
        return render_template('admin/campaigns.html')
    
    @app.route('/share-and-earn')
    def share_and_earn():
        """Share and earn page for advocates"""
        if 'user_id' not in session:
            flash('Please log in to access the share and earn page.', 'error')
            return redirect(url_for('login'))
        return render_template('share_and_earn.html')
    
    @app.route('/r/<link_slug>')
    def referral_landing(link_slug):
        """Referral landing page"""
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        # Find referral code by link slug
        cursor.execute('''
            SELECT rc.id, rc.advocate_id, c.name, c.description
            FROM referral_codes rc
            JOIN referral_campaigns c ON rc.campaign_id = c.id
            WHERE rc.link_slug = ?
            AND c.is_active = TRUE
            AND c.start_date <= datetime('now')
            AND c.end_date >= datetime('now')
        ''', (link_slug,))
        
        code = cursor.fetchone()
        conn.close()
        
        if not code:
            flash('Invalid or expired referral link', 'error')
            return redirect(url_for('index'))
        
        # Store referral code in session
        session['referral_code_id'] = code[0]
        
        # Redirect to registration page with referral code
        return redirect(url_for('register', ref=link_slug))