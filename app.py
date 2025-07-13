#!/usr/bin/env python3
"""
Sapyyn Patient Referral System
A web application for managing patient referrals and documents
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
import uuid
import qrcode
from io import BytesIO
import base64
from datetime import datetime
import json
import random
import string
import requests

app = Flask(__name__)
app.secret_key = 'sapyyn-patient-referral-system-2024'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configuration
UPLOAD_FOLDER = 'patient-referral'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database initialization
def init_db():
    """Initialize the SQLite database"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Users table - Enhanced for multiple user types
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'patient',
            user_type TEXT DEFAULT 'patient',
            practice_name TEXT,
            license_number TEXT,
            specialty TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            four_digit_code TEXT UNIQUE,
            is_active BOOLEAN DEFAULT 1,
            subscription_plan TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Referrals table - Enhanced with 4-digit code support
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            referral_id TEXT UNIQUE NOT NULL,
            four_digit_code TEXT,
            patient_name TEXT NOT NULL,
            patient_email TEXT,
            patient_phone TEXT,
            referring_doctor TEXT,
            target_doctor TEXT,
            medical_condition TEXT,
            urgency_level TEXT DEFAULT 'normal',
            status TEXT DEFAULT 'pending',
            notes TEXT,
            qr_code TEXT,
            reward_points INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referral_id INTEGER,
            user_id INTEGER,
            file_type TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (referral_id) REFERENCES referrals (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Rewards table for tracking reward points and redemptions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            referral_id INTEGER,
            points_earned INTEGER DEFAULT 0,
            points_used INTEGER DEFAULT 0,
            reward_type TEXT,
            reward_description TEXT,
            api_provider TEXT,
            api_transaction_id TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (referral_id) REFERENCES referrals (id)
        )
    ''')
    
    # Subscription plans table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscription_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_name TEXT UNIQUE NOT NULL,
            plan_type TEXT NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            billing_cycle TEXT DEFAULT 'monthly',
            features TEXT,
            max_referrals INTEGER DEFAULT -1,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # API configurations for rewards
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_name TEXT UNIQUE NOT NULL,
            api_key TEXT,
            api_secret TEXT,
            base_url TEXT,
            is_enabled BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default subscription plans
    cursor.execute('''
        INSERT OR IGNORE INTO subscription_plans (plan_name, plan_type, price, billing_cycle, features, max_referrals)
        VALUES 
        ('Free', 'basic', 0.00, 'monthly', 'Basic referral system, 5 referrals per month', 5),
        ('Professional', 'pro', 29.99, 'monthly', 'Unlimited referrals, Analytics, Priority support', -1),
        ('Enterprise', 'enterprise', 99.99, 'monthly', 'All features, Custom branding, API access, Dedicated support', -1)
    ''')
    
    # Insert default API providers
    cursor.execute('''
        INSERT OR IGNORE INTO api_configs (provider_name, base_url, is_enabled)
        VALUES 
        ('Tango', 'https://api.tangocard.com', 0),
        ('Tremendous', 'https://api.tremendous.com', 0),
        ('Zapier', 'https://hooks.zapier.com', 0),
        ('n8n', 'http://localhost:5678', 0),
        ('SMS-it', 'https://api.sms-it.com', 0)
    ''')
    
    conn.commit()
    conn.close()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_qr_code(data):
    """Generate QR code for referral"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode()

def generate_four_digit_code():
    """Generate unique 4-digit code for referrals"""
    while True:
        code = ''.join(random.choices(string.digits, k=4))
        # Check if code already exists
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE four_digit_code = ?', (code,))
        if not cursor.fetchone():
            conn.close()
            return code
        conn.close()

def calculate_reward_points(referral_type, user_role):
    """Calculate reward points based on referral type and user role"""
    point_mapping = {
        'dentist': {'referral_sent': 10, 'referral_completed': 25},
        'specialist': {'referral_received': 5, 'referral_completed': 15},
        'patient': {'referral_completed': 5}
    }
    return point_mapping.get(user_role, {}).get(referral_type, 0)

def send_reward_api_request(provider, reward_data):
    """Send reward request to third-party API providers"""
    try:
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        cursor.execute('SELECT api_key, api_secret, base_url FROM api_configs WHERE provider_name = ? AND is_enabled = 1', (provider,))
        config = cursor.fetchone()
        conn.close()
        
        if not config:
            return {'status': 'error', 'message': f'{provider} API not configured'}
        
        api_key, api_secret, base_url = config
        
        # Basic implementation - would need specific API endpoints for each provider
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # This is a placeholder - actual implementation would vary by provider
        response = requests.post(f'{base_url}/rewards', json=reward_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return {'status': 'success', 'data': response.json()}
        else:
            return {'status': 'error', 'message': f'API request failed: {response.status_code}'}
            
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/pricing')
def pricing():
    """Pricing page"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subscription_plans WHERE is_active = 1 ORDER BY price ASC')
    plans = cursor.fetchall()
    conn.close()
    return render_template('pricing.html', plans=plans)

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@app.route('/resources')
def resources():
    """Resources page"""
    return render_template('resources.html')

@app.route('/referrals')
def referrals_info():
    """Referrals information page"""
    return render_template('referrals_info.html')

@app.route('/surgicalInstruction')
def surgical_instruction():
    """Surgical instruction page"""
    return render_template('surgical_instruction.html')

# Portal routes
@app.route('/portal/dentist')
def dentist_portal():
    """Dentist portal"""
    if 'user_id' not in session or session.get('user_type') != 'dentist':
        return redirect(url_for('login'))
    return render_template('portals/dentist.html')

@app.route('/portal/specialist')
def specialist_portal():
    """Specialist portal"""
    if 'user_id' not in session or session.get('user_type') != 'specialist':
        return redirect(url_for('login'))
    return render_template('portals/specialist.html')

@app.route('/portal/patient')
def patient_portal():
    """Patient portal"""
    if 'user_id' not in session or session.get('user_type') != 'patient':
        return redirect(url_for('login'))
    return render_template('portals/patient.html')

@app.route('/admin')
def admin_portal():
    """Admin portal"""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin/dashboard.html')

@app.route('/admin/dentist')
def dentist_admin_portal():
    """Dentist admin portal"""
    if 'user_id' not in session or session.get('role') not in ['admin', 'dentist_admin']:
        return redirect(url_for('login'))
    return render_template('admin/dentist_admin.html')

@app.route('/admin/specialist')
def specialist_admin_portal():
    """Specialist admin portal"""
    if 'user_id' not in session or session.get('role') not in ['admin', 'specialist_admin']:
        return redirect(url_for('login'))
    return render_template('admin/specialist_admin.html')

# Quick referral with 4-digit code
@app.route('/quick-referral', methods=['POST'])
def quick_referral():
    """Quick referral using 4-digit code"""
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        
        if len(code) != 4 or not code.isdigit():
            return jsonify({'status': 'error', 'message': 'Invalid 4-digit code'})
        
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, full_name, practice_name FROM users WHERE four_digit_code = ? AND is_active = 1', (code,))
        doctor = cursor.fetchone()
        conn.close()
        
        if doctor:
            return jsonify({
                'status': 'success', 
                'doctor': {
                    'id': doctor[0],
                    'name': doctor[1],
                    'practice': doctor[2]
                }
            })
        else:
            return jsonify({'status': 'error', 'message': 'Doctor not found with this code'})

@app.route('/rewards')
def rewards():
    """Rewards dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get user's total rewards
    cursor.execute('''
        SELECT SUM(points_earned) - COALESCE(SUM(points_used), 0) as total_points
        FROM rewards 
        WHERE user_id = ?
    ''', (session['user_id'],))
    total_points = cursor.fetchone()[0] or 0
    
    # Get recent rewards
    cursor.execute('''
        SELECT points_earned, points_used, reward_type, reward_description, created_at
        FROM rewards 
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 10
    ''', (session['user_id'],))
    recent_rewards = cursor.fetchall()
    
    conn.close()
    
    return render_template('rewards.html', total_points=total_points, recent_rewards=recent_rewards)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, password_hash, full_name, role, user_type, four_digit_code 
            FROM users WHERE username = ? AND is_active = 1
        ''', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['full_name'] = user[3]
            session['role'] = user[4]
            session['user_type'] = user[5]
            session['four_digit_code'] = user[6]
            flash('Login successful!', 'success')
            
            # Redirect to appropriate portal based on user type
            if user[5] == 'dentist':
                return redirect(url_for('dentist_portal'))
            elif user[5] == 'specialist':
                return redirect(url_for('specialist_portal'))
            elif user[4] == 'admin':
                return redirect(url_for('admin_portal'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        user_type = request.form.get('user_type', 'patient')
        practice_name = request.form.get('practice_name', '')
        license_number = request.form.get('license_number', '')
        specialty = request.form.get('specialty', '')
        phone = request.form.get('phone', '')
        
        password_hash = generate_password_hash(password)
        four_digit_code = generate_four_digit_code() if user_type in ['dentist', 'specialist'] else None
        
        try:
            conn = sqlite3.connect('sapyyn.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, role, user_type, 
                                 practice_name, license_number, specialty, phone, four_digit_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, full_name, user_type, user_type,
                  practice_name, license_number, specialty, phone, four_digit_code))
            conn.commit()
            conn.close()
            
            flash('Registration successful! Please login.', 'success')
            if four_digit_code:
                flash(f'Your 4-digit referral code is: {four_digit_code}', 'info')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get user's referrals
    cursor.execute('''
        SELECT r.*, COUNT(d.id) as document_count
        FROM referrals r
        LEFT JOIN documents d ON r.id = d.referral_id
        WHERE r.user_id = ?
        GROUP BY r.id
        ORDER BY r.created_at DESC
    ''', (session['user_id'],))
    referrals = cursor.fetchall()
    
    # Get recent documents
    cursor.execute('''
        SELECT file_type, file_name, upload_date
        FROM documents
        WHERE user_id = ?
        ORDER BY upload_date DESC
        LIMIT 5
    ''', (session['user_id'],))
    recent_documents = cursor.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', referrals=referrals, recent_documents=recent_documents)

@app.route('/referral/new', methods=['GET', 'POST'])
def new_referral():
    """Create new referral"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        referral_id = str(uuid.uuid4())[:8]
        patient_name = request.form['patient_name']
        referring_doctor = request.form['referring_doctor']
        target_doctor = request.form['target_doctor']
        medical_condition = request.form['medical_condition']
        urgency_level = request.form['urgency_level']
        notes = request.form['notes']
        
        # Generate QR code with referral info
        qr_data = f"Referral ID: {referral_id}\nPatient: {patient_name}\nCondition: {medical_condition}"
        qr_code = generate_qr_code(qr_data)
        
        try:
            conn = sqlite3.connect('sapyyn.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO referrals (user_id, referral_id, patient_name, referring_doctor, 
                                     target_doctor, medical_condition, urgency_level, notes, qr_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], referral_id, patient_name, referring_doctor, 
                  target_doctor, medical_condition, urgency_level, notes, qr_code))
            conn.commit()
            conn.close()
            
            flash('Referral created successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Error creating referral: {str(e)}', 'error')
    
    return render_template('new_referral.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """File upload handler"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        file_type = request.form.get('file_type', 'supporting_documents')
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{file_type}_{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            file.save(file_path)
            
            # Save to database
            conn = sqlite3.connect('sapyyn.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO documents (user_id, file_type, file_name, file_path, file_size)
                VALUES (?, ?, ?, ?, ?)
            ''', (session['user_id'], file_type, filename, file_path, os.path.getsize(file_path)))
            conn.commit()
            conn.close()
            
            flash('File uploaded successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid file type', 'error')
    
    return render_template('upload.html')

@app.route('/documents')
def view_documents():
    """View user documents"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, file_type, file_name, file_size, upload_date
        FROM documents
        WHERE user_id = ?
        ORDER BY upload_date DESC
    ''', (session['user_id'],))
    documents = cursor.fetchall()
    conn.close()
    
    return render_template('documents.html', documents=documents)

@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Count referrals by status
    cursor.execute('''
        SELECT status, COUNT(*) 
        FROM referrals 
        WHERE user_id = ? 
        GROUP BY status
    ''', (session['user_id'],))
    status_counts = dict(cursor.fetchall())
    
    # Count documents by type
    cursor.execute('''
        SELECT file_type, COUNT(*) 
        FROM documents 
        WHERE user_id = ? 
        GROUP BY file_type
    ''', (session['user_id'],))
    document_counts = dict(cursor.fetchall())
    
    conn.close()
    
    return jsonify({
        'status_counts': status_counts,
        'document_counts': document_counts
    })

@app.route('/api/redeem-reward', methods=['POST'])
def redeem_reward():
    """API endpoint for reward redemption"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    provider = data.get('provider')
    reward_type = data.get('reward_type')
    points = data.get('points', 0)
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Check if user has enough points
    cursor.execute('''
        SELECT SUM(points_earned) - COALESCE(SUM(points_used), 0) as available_points
        FROM rewards 
        WHERE user_id = ?
    ''', (session['user_id'],))
    available_points = cursor.fetchone()[0] or 0
    
    if available_points < points:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Insufficient points'})
    
    # Process reward redemption
    try:
        # Call external API
        reward_data = {
            'user_id': session['user_id'],
            'reward_type': reward_type,
            'points': points,
            'user_email': session.get('email', '')
        }
        
        api_response = send_reward_api_request(provider, reward_data)
        
        if api_response['status'] == 'success':
            # Record the redemption
            cursor.execute('''
                INSERT INTO rewards (user_id, points_used, reward_type, reward_description, api_provider, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], points, reward_type, f'{reward_type} via {provider}', provider, 'completed'))
            conn.commit()
            
            result = {'status': 'success', 'message': 'Reward redeemed successfully'}
        else:
            result = {'status': 'error', 'message': api_response['message']}
            
    except Exception as e:
        result = {'status': 'error', 'message': str(e)}
    
    conn.close()
    return jsonify(result)

@app.route('/admin/api-config', methods=['GET', 'POST'])
def admin_api_config():
    """Admin page for API configuration"""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        provider = request.form['provider']
        api_key = request.form['api_key']
        api_secret = request.form.get('api_secret', '')
        base_url = request.form['base_url']
        is_enabled = request.form.get('is_enabled') == 'on'
        
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE api_configs 
            SET api_key = ?, api_secret = ?, base_url = ?, is_enabled = ?, updated_at = CURRENT_TIMESTAMP
            WHERE provider_name = ?
        ''', (api_key, api_secret, base_url, is_enabled, provider))
        conn.commit()
        conn.close()
        
        flash(f'{provider} API configuration updated successfully!', 'success')
        return redirect(url_for('admin_api_config'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM api_configs ORDER BY provider_name')
    api_configs = cursor.fetchall()
    conn.close()
    
    return render_template('admin/api_config.html', api_configs=api_configs)

@app.route('/admin/users')
def admin_users():
    """Admin page for user management"""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, email, full_name, user_type, practice_name, four_digit_code, 
               subscription_plan, is_active, created_at
        FROM users 
        ORDER BY created_at DESC
    ''')
    users = cursor.fetchall()
    conn.close()
    
    return render_template('admin/users.html', users=users)

@app.route('/admin/analytics')
def admin_analytics():
    """Admin analytics dashboard"""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get analytics data
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM referrals')
    total_referrals = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM documents')
    total_documents = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT user_type, COUNT(*) 
        FROM users 
        WHERE is_active = 1 
        GROUP BY user_type
    ''')
    users_by_type = dict(cursor.fetchall())
    
    cursor.execute('''
        SELECT status, COUNT(*) 
        FROM referrals 
        GROUP BY status
    ''')
    referrals_by_status = dict(cursor.fetchall())
    
    conn.close()
    
    analytics_data = {
        'total_users': total_users,
        'total_referrals': total_referrals,
        'total_documents': total_documents,
        'users_by_type': users_by_type,
        'referrals_by_status': referrals_by_status
    }
    
    return render_template('admin/analytics.html', data=analytics_data)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)