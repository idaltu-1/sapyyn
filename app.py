"""
Sapyyn Patient Referral System - Main Application
"""

from flask import Flask, render_template, send_from_directory, redirect, url_for, request, session, flash, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from routes.nocode_routes import nocode_api
from controllers.nocodebackend_controller import nocodebackend_api
from controllers.promotion_controller import promotions
from controllers.admin_promotion_controller import admin_promotions
from config.app_config import get_config, INITIAL_ADMIN, generate_secure_password
from config.security import SecurityConfig
import os
import sqlite3
import uuid
import qrcode
import base64
from io import BytesIO
from datetime import datetime, timedelta
import stripe
import bleach
import re
import logging
from functools import wraps


# Initialize Flask app
app = Flask(__name__)

# Load configuration
config_class = get_config()
app.config.from_object(config_class)

# Initialize security features
csrf = CSRFProtect(app)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Apply configuration settings
app.secret_key = config_class.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = config_class.MAX_CONTENT_LENGTH

# Initialize security configuration
SecurityConfig.init_app(app)

# Stripe configuration
stripe.api_key = config_class.STRIPE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY = config_class.STRIPE_PUBLISHABLE_KEY

# Analytics configuration
ANALYTICS_CONFIG = {
    'GA4_MEASUREMENT_ID': config_class.GA4_MEASUREMENT_ID,
    'GTM_CONTAINER_ID': config_class.GTM_CONTAINER_ID,
    'HOTJAR_SITE_ID': config_class.HOTJAR_SITE_ID,
    'ENABLE_ANALYTICS': config_class.ENABLE_ANALYTICS,
    'ENVIRONMENT': config_class.FLASK_ENV
}

# Configuration
UPLOAD_FOLDER = config_class.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = config_class.ALLOWED_EXTENSIONS

# Domain-based access control configuration
ALLOWED_DOMAINS = {
    'healthcare.org',
    'medical.com', 
    'dental.org',
    'clinic.net',
    'hospital.org',
    'dentistry.edu',
    'orthodontics.com',
    'periodontics.org',
    'oralsurgery.net',
    'endodontics.com',
    'sapyyn.com',  # Allow for demo users
    'gmail.com',  # Allow for demo/testing
    'example.com'  # Allow for demo/testing
}

# Password complexity requirements
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIREMENTS = {
    'min_length': PASSWORD_MIN_LENGTH,
    'require_uppercase': True,
    'require_lowercase': True,
    'require_digit': True,
    'require_special': True
}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Domain and password validation functions
def is_email_domain_allowed(email):
    """Check if the email domain is in the allowed domains list"""
    if not email or '@' not in email:
        return False
    domain = email.split('@')[1].lower()
    return domain in ALLOWED_DOMAINS

def validate_password_complexity(password):
    """Validate password meets complexity requirements"""
    if not password:
        return False, "Password is required"
    
    if len(password) < PASSWORD_REQUIREMENTS['min_length']:
        return False, f"Password must be at least {PASSWORD_REQUIREMENTS['min_length']} characters long"
    
    if PASSWORD_REQUIREMENTS['require_uppercase'] and not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if PASSWORD_REQUIREMENTS['require_lowercase'] and not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if PASSWORD_REQUIREMENTS['require_digit'] and not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    if PASSWORD_REQUIREMENTS['require_special'] and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        return False, "Password must contain at least one special character"
    
    return True, "Password meets complexity requirements"

def get_user_by_username_or_email(username):
    """Get user by username or email"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Try to find by username first, then by email
    cursor.execute('SELECT id, username, password_hash, full_name, role, email FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    if not user and '@' in username:
        # If username looks like an email, try searching by email
        cursor.execute('SELECT id, username, password_hash, full_name, role, email FROM users WHERE email = ?', (username,))
        user = cursor.fetchone()
    
    conn.close()
    return user

# Database initialization
def init_db():
    """Initialize the SQLite database"""
    config_class = get_config()
    conn = sqlite3.connect(config_class.DATABASE_NAME)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'patient',
            is_verified BOOLEAN DEFAULT FALSE,
            fraud_score DECIMAL(5,2) DEFAULT 0.0,
            is_paused BOOLEAN DEFAULT FALSE,
            device_fingerprint TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Referrals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            referral_id TEXT UNIQUE NOT NULL,
            patient_name TEXT NOT NULL,
            referring_doctor TEXT,
            target_doctor TEXT,
            medical_condition TEXT,
            urgency_level TEXT DEFAULT 'normal',
            status TEXT DEFAULT 'pending',

            case_status TEXT DEFAULT 'pending',
            consultation_date TIMESTAMP,
            case_accepted_date TIMESTAMP,
            treatment_start_date TIMESTAMP,
            treatment_complete_date TIMESTAMP,
            rejection_reason TEXT,
            estimated_value DECIMAL(10,2),
            actual_value DECIMAL(10,2),
            notes TEXT,
            qr_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Add case acceptance tracking columns to referrals if they don't exist
    try:
        cursor.execute('ALTER TABLE referrals ADD COLUMN case_status TEXT DEFAULT "pending"')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE referrals ADD COLUMN consultation_date TIMESTAMP')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE referrals ADD COLUMN case_accepted_date TIMESTAMP')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE referrals ADD COLUMN treatment_start_date TIMESTAMP')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE referrals ADD COLUMN treatment_complete_date TIMESTAMP')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE referrals ADD COLUMN rejection_reason TEXT')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE referrals ADD COLUMN estimated_value DECIMAL(10,2)')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE referrals ADD COLUMN actual_value DECIMAL(10,2)')
    except sqlite3.OperationalError:
        pass
    
    # Add patient_id and dentist_id columns for new referrals module
    try:
        cursor.execute('ALTER TABLE referrals ADD COLUMN patient_id INTEGER')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE referrals ADD COLUMN dentist_id INTEGER')
    except sqlite3.OperationalError:
        pass
    
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
    
    # Reward Programs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reward_programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            program_type TEXT DEFAULT 'referral',
            status TEXT DEFAULT 'active',
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            created_by INTEGER,
            compliance_notes TEXT,
            legal_language TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Reward Tiers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reward_tiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER,
            tier_name TEXT NOT NULL,
            tier_level INTEGER DEFAULT 1,
            referrals_required INTEGER DEFAULT 1,
            reward_type TEXT DEFAULT 'points',
            reward_value DECIMAL(10,2),
            reward_description TEXT,
            fulfillment_type TEXT DEFAULT 'manual',
            fulfillment_config TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (program_id) REFERENCES reward_programs (id)
        )
    ''')
    
    # User Rewards table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            program_id INTEGER,
            tier_id INTEGER,
            referral_id INTEGER,
            points_earned DECIMAL(10,2) DEFAULT 0,
            reward_status TEXT DEFAULT 'pending',
            earned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            redeemed_date TIMESTAMP,
            fulfillment_status TEXT DEFAULT 'pending',
            fulfillment_notes TEXT,
            compliance_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (program_id) REFERENCES reward_programs (id),
            FOREIGN KEY (tier_id) REFERENCES reward_tiers (id),
            FOREIGN KEY (referral_id) REFERENCES referrals (id)
        )
    ''')
    
    # Reward Triggers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reward_triggers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER,
            trigger_type TEXT NOT NULL,
            trigger_condition TEXT,
            trigger_value TEXT,
            points_awarded DECIMAL(10,2),
            tier_advancement BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (program_id) REFERENCES reward_programs (id)
        )
    ''')
    
    # Reward Notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reward_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            notification_type TEXT,
            title TEXT,
            message TEXT,
            is_read BOOLEAN DEFAULT FALSE,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Compliance Audit Trail table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compliance_audit_trail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action_type TEXT,
            entity_type TEXT,
            entity_id INTEGER,
            action_details TEXT,
            ip_address TEXT,
            user_agent TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Gamification Achievements table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            icon TEXT,
            achievement_type TEXT,
            requirement_value INTEGER,
            points_value DECIMAL(10,2),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User Achievements table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            achievement_id INTEGER,
            earned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            progress INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (achievement_id) REFERENCES achievements (id)
        )
    ''')
    
    # Provider Codes table for 4-digit system
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS provider_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            provider_code TEXT UNIQUE NOT NULL,
            provider_type TEXT NOT NULL,
            practice_name TEXT,
            specialization TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Messages table for portal messaging
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            recipient_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            content TEXT NOT NULL,
            message_type TEXT DEFAULT 'general',
            referral_id INTEGER,
            is_read BOOLEAN DEFAULT FALSE,
            is_deleted_by_sender BOOLEAN DEFAULT FALSE,
            is_deleted_by_recipient BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read_at TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (recipient_id) REFERENCES users (id),
            FOREIGN KEY (referral_id) REFERENCES referrals (id)
        )
    ''')
    
    # Subscription Plans table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscription_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_name TEXT NOT NULL,
            plan_type TEXT NOT NULL,
            price_monthly DECIMAL(10,2),
            price_annual DECIMAL(10,2),
            features TEXT,
            max_referrals INTEGER,
            max_users INTEGER,
            storage_gb INTEGER,
            support_level TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User Subscriptions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan_id INTEGER,
            subscription_status TEXT DEFAULT 'active',
            billing_cycle TEXT DEFAULT 'monthly',
            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_date TIMESTAMP,
            auto_renew BOOLEAN DEFAULT TRUE,
            payment_method TEXT,
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            stripe_payment_method_id TEXT,
            trial_end_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (plan_id) REFERENCES subscription_plans (id)
        )
    ''')
    
    # Practice Management table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS practices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            practice_name TEXT NOT NULL,
            practice_type TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            admin_user_id INTEGER,
            subscription_id INTEGER,
            is_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_user_id) REFERENCES users (id),
            FOREIGN KEY (subscription_id) REFERENCES user_subscriptions (id)
        )
    ''')
    
    # Practice Members table (for multi-user practices)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS practice_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            practice_id INTEGER,
            user_id INTEGER,
            role TEXT,
            permissions TEXT,
            status TEXT DEFAULT 'active',
            invited_by INTEGER,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (practice_id) REFERENCES practices (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (invited_by) REFERENCES users (id)
        )
    ''')
    
    # Insert default subscription plans
    cursor.execute('''
        INSERT OR IGNORE INTO subscription_plans 
        (plan_name, plan_type, price_monthly, price_annual, features, max_referrals, max_users, storage_gb, support_level)
        VALUES 
        ('Basic', 'free', 0.00, 0.00, 'Up to 5 referrals/month, Basic messaging, Limited network access', 5, 1, 1, 'email'),
        ('Professional', 'practice', 49.99, 499.99, 'Unlimited referrals, Priority support, Full network access, QR codes, CE credits', -1, 3, 10, 'priority'),
        ('Enterprise', 'enterprise', 149.99, 1499.99, 'Everything in Professional, Multi-practice management, Advanced analytics, API access', -1, -1, 50, 'phone')
    ''')
    
    # User Profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            phone TEXT,
            license_number TEXT,
            specialization TEXT,
            practice_name TEXT,
            practice_address TEXT,
            years_experience TEXT,
            website TEXT,
            bio TEXT,
            account_type TEXT,
            avatar_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # User Preferences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            preference_key TEXT NOT NULL,
            preference_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, preference_key)
        )
    ''')
    
    # Add is_verified column to users table if it doesn't exist
    try:
        cursor.execute('''
            ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE
        ''')
    except sqlite3.OperationalError:
        # Column already exists, skip
        pass

    # Referring Doctor Profiles table for relationship management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referring_doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            practice_name TEXT,
            specialty TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            referral_count INTEGER DEFAULT 0,
            conversion_rate DECIMAL(5,2) DEFAULT 0.0,
            avg_case_value DECIMAL(10,2) DEFAULT 0.0,
            relationship_score INTEGER DEFAULT 0,
            last_referral_date TIMESTAMP,
            communication_preference TEXT DEFAULT 'email',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Case Conversion Tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS case_conversions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referral_id TEXT NOT NULL,
            stage TEXT NOT NULL,
            stage_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            assigned_to TEXT,
            response_time_hours INTEGER,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Team Productivity Metrics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE DEFAULT CURRENT_DATE,
            referrals_processed INTEGER DEFAULT 0,
            consultations_completed INTEGER DEFAULT 0,
            cases_accepted INTEGER DEFAULT 0,
            avg_response_time_hours DECIMAL(10,2) DEFAULT 0.0,
            revenue_generated DECIMAL(10,2) DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def scan_file_for_viruses(file_path):
    """
    Placeholder for virus scanning functionality.
    This function provides a hook for integrating with ClamAV or other antivirus solutions.
    
    Args:
        file_path (str): Path to the file to be scanned
        
    Returns:
        dict: Scan result with status and details
    """
    try:
        # Placeholder implementation
        # In a real implementation, you would:
        # 1. Use python-clamd to connect to ClamAV daemon
        # 2. Scan the file using clamd.scan_file(file_path)
        # 3. Return appropriate results
        
        # Example integration code (commented out):
        # import clamd
        # cd = clamd.ClamdUnixSocket()
        # scan_result = cd.scan(file_path)
        # if scan_result[file_path][0] == 'FOUND':
        #     return {
        #         'status': 'infected',
        #         'virus_name': scan_result[file_path][1],
        #         'message': f'Virus detected: {scan_result[file_path][1]}'
        #     }
        
        # For now, return clean status (placeholder)
        app.logger.info(f'Virus scan placeholder called for file: {file_path}')
        
        return {
            'status': 'clean',
            'virus_name': None,
            'message': 'File scanned successfully - no threats detected (placeholder)'
        }
        
    except Exception as e:
        app.logger.error(f'Virus scan error for {file_path}: {str(e)}')
        return {
            'status': 'error',
            'virus_name': None,
            'message': f'Scan error: {str(e)}'
        }

def get_file_mime_type(filename):
    """Get MIME type based on file extension"""
    import mimetypes
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'

def format_file_size(size_bytes):
    """Convert file size in bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

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

# Template context processor for analytics config
@app.context_processor
def inject_analytics_config():
    """Make analytics configuration available in templates"""
    return {
        'analytics_config': ANALYTICS_CONFIG,
        'ga4_id': ANALYTICS_CONFIG['GA4_MEASUREMENT_ID'],
        'gtm_id': ANALYTICS_CONFIG['GTM_CONTAINER_ID'],
        'hotjar_id': ANALYTICS_CONFIG['HOTJAR_SITE_ID'],
        'analytics_enabled': ANALYTICS_CONFIG['ENABLE_ANALYTICS']
    }

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/get_started_page')
def get_started_page():
    """Get started onboarding page"""
    return send_from_directory('static', 'getstarted_page.html')

@app.route('/api/complete_onboarding', methods=['POST'])
def complete_onboarding():
    """Complete the onboarding process and create user account"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['firstName', 'lastName', 'email', 'accountType']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        # Check if email already exists
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE email = ?', (data['email'],))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Create user account
        full_name = f"{data['firstName']} {data['lastName']}"
        password_hash = generate_password_hash('temp123')  # Temporary password - user should reset
        
        # Map account types to roles
        role_mapping = {
            'dentist': 'dentist',
            'specialist': 'specialist', 
            'hygienist': 'dentist',
            'practice-manager': 'dentist',
            'assistant': 'dentist',
            'student': 'patient'
        }
        
        role = role_mapping.get(data['accountType'], 'dentist')
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, role, created_at, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['email'],
            data['email'], 
            password_hash,
            full_name,
            role,
            datetime.now(),
            True  # Auto-verify onboarding users
        ))
        
        user_id = cursor.lastrowid
        
        # Add profile information
        cursor.execute('''
            INSERT INTO user_profiles (
                user_id, phone, license_number, specialization, practice_name, 
                practice_address, years_experience, website, bio, account_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            data.get('phone', ''),
            data.get('licenseNumber', ''),
            data.get('specialization', ''),
            data.get('practiceName', ''),
            data.get('practiceAddress', ''),
            data.get('yearsExperience', ''),
            data.get('website', ''),
            data.get('bio', ''),
            data['accountType']
        ))
        
        # Handle plan selection and create subscription
        selected_plan = data.get('selectedPlan', 'basic')
        
        if selected_plan == 'trial':
            # Get Professional plan details for trial
            cursor.execute('SELECT * FROM subscription_plans WHERE plan_name = ?', ('Professional',))
            plan = cursor.fetchone()
            
            if plan:
                # Calculate trial end date (14 days from now)
                trial_end = datetime.now() + timedelta(days=14)
                
                # Create trial subscription
                cursor.execute('''
                    INSERT INTO user_subscriptions 
                    (user_id, plan_id, subscription_status, trial_end_date, end_date, auto_renew)
                    VALUES (?, ?, 'trial', ?, ?, FALSE)
                ''', (user_id, plan[0], trial_end, trial_end))
                
                # Generate provider code for trial users
                provider_code = create_provider_code(
                    user_id, 
                    role,
                    data.get('practiceName', 'Practice'),
                    data.get('specialization', 'General')
                )
        
        elif selected_plan == 'basic':
            # Get Basic plan details
            cursor.execute('SELECT * FROM subscription_plans WHERE plan_name = ?', ('Basic',))
            plan = cursor.fetchone()
            
            if plan:
                # Create basic subscription (no end date for free plan)
                cursor.execute('''
                    INSERT INTO user_subscriptions 
                    (user_id, plan_id, subscription_status, auto_renew)
                    VALUES (?, ?, 'active', FALSE)
                ''', (user_id, plan[0]))
        
        # Save preferences if provided
        preferences = data.get('preferences', {})
        for pref_key, pref_value in preferences.items():
            cursor.execute('''
                INSERT INTO user_preferences (user_id, preference_key, preference_value)
                VALUES (?, ?, ?)
            ''', (user_id, pref_key, str(pref_value)))
        
        conn.commit()
        conn.close()
        
        # Set session for auto-login
        session['user_id'] = user_id
        session['username'] = data['email']
        session['full_name'] = full_name
        session['role'] = role
        session['email'] = data['email']
        
        return jsonify({
            'success': True, 
            'message': 'Account created successfully',
            'user_id': user_id,
            'redirect_url': '/dashboard'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login with domain-based restrictions"""
    provider_code = request.args.get('provider_code')
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Get user information (try both username and email)
        user = get_user_by_username_or_email(username)
        
        if user and check_password_hash(user[2], password):
            # Check domain restrictions for email-based logins
            user_email = user[5] if len(user) > 5 else None
            
            # If user has an email, check domain restrictions
            if user_email and not is_email_domain_allowed(user_email):
                flash('Access denied: Your email domain is not authorized for this portal. Please contact your administrator.', 'error')
                return render_template('login.html', provider_code=provider_code)
            
            # Successful login - set session
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['full_name'] = user[3]
            session['role'] = user[4]
            session['email'] = user_email
            
            conn = sqlite3.connect('sapyyn.db')
            cursor = conn.cursor()
            
            # Handle provider code after login
            if provider_code:
                # Get provider information
                cursor.execute('''
                    SELECT pc.user_id, pc.practice_name, pc.provider_type, pc.specialization, u.full_name
                    FROM provider_codes pc
                    JOIN users u ON pc.user_id = u.id
                    WHERE pc.provider_code = ? AND pc.is_active = TRUE
                ''', (provider_code,))
                provider_info = cursor.fetchone()
                
                if provider_info:
                    # Create referral connection for existing user
                    referral_id = str(uuid.uuid4())[:8]
                    cursor.execute('''
                        INSERT INTO referrals (user_id, referral_id, patient_name, target_doctor, 
                                             medical_condition, status, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (provider_info[0], referral_id, user[3], provider_info[4],
                          'Consultation request', 'pending', 
                          f'Patient connected using provider code {provider_code}'))
                    conn.commit()
                    
                    flash(f'Login successful! You have been connected to {provider_info[2]} {provider_info[4]} at {provider_info[1]}.', 'success')
                    conn.close()
                    return redirect(url_for('patient_portal'))
                else:
                    flash('Login successful, but the provider code was invalid.', 'warning')
            else:
                flash('Login successful!', 'success')
            
            conn.close()
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html', provider_code=provider_code)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    provider_code = request.args.get('provider_code')
    suggested_role = request.args.get('role', 'patient')
    provider_info = None
    
    # If provider code is provided, validate it and get provider information
    if provider_code:
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pc.user_id, pc.practice_name, pc.provider_type, pc.specialization, u.full_name
            FROM provider_codes pc
            JOIN users u ON pc.user_id = u.id
            WHERE pc.provider_code = ? AND pc.is_active = TRUE
        ''', (provider_code,))
        provider_info = cursor.fetchone()
        conn.close()
        
        if not provider_info:
            flash('Invalid provider code. Please check the code and try again.', 'error')
            provider_code = None
    
    if request.method == 'POST':
        signup_type = request.form.get('signup_type')
        
        if signup_type in ['inline', 'cta']:
            # Handle inline/CTA signup - simplified process
            email = request.form['email']
            full_name = request.form.get('full_name', email.split('@')[0])
            username = email
            password = request.form.get('password', 'temp_password_' + str(uuid.uuid4())[:8])
            role = request.form.get('role', 'dentist')  # Default to dentist for inline signups
            
            # Generate a more user-friendly password
            if password.startswith('temp_password_'):
                # Create a memorable password from email
                password = email.split('@')[0] + '123!'
            
        else:
            # Handle full registration form
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            full_name = request.form['full_name']
            role = request.form.get('role', 'patient')
        
        # Domain validation
        if not is_email_domain_allowed(email):
            flash('Registration denied: Your email domain is not authorized for this portal. Please use an authorized email domain or contact your administrator.', 'error')
            return render_template('register.html', 
                                 provider_code=provider_code, 
                                 provider_info=provider_info, 
                                 suggested_role=suggested_role)
        
        # Password complexity validation (skip for auto-generated passwords)
        if not password.startswith('temp_password_') and signup_type not in ['inline', 'cta']:
            is_valid, message = validate_password_complexity(password)
            if not is_valid:
                flash(f'Password validation failed: {message}', 'error')
                return render_template('register.html', 
                                     provider_code=provider_code, 
                                     provider_info=provider_info, 
                                     suggested_role=suggested_role)
        
        password_hash = generate_password_hash(password)
        
        try:
            conn = sqlite3.connect('sapyyn.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, full_name, role))
            
            user_id = cursor.lastrowid
            
            # If registering with a provider code, create a connection/referral
            if provider_code and provider_info:
                # Generate a referral for this patient-provider connection
                referral_id = str(uuid.uuid4())[:8]
                cursor.execute('''
                    INSERT INTO referrals (user_id, referral_id, patient_name, target_doctor, 
                                         medical_condition, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (provider_info[0], referral_id, full_name, provider_info[4],
                      'Initial consultation', 'pending', 
                      f'Patient registered using provider code {provider_code}'))
            
            # For inline signups, automatically start free trial
            if signup_type in ['inline', 'cta']:
                # Get trial plan
                cursor.execute('SELECT id FROM subscription_plans WHERE plan_name = ?', ('Free Trial',))
                trial_plan = cursor.fetchone()
                if trial_plan:
                    trial_end = datetime.now() + timedelta(days=14)
                    cursor.execute('''
                        INSERT INTO user_subscriptions 
                        (user_id, plan_id, subscription_status, trial_end_date, end_date, auto_renew)
                        VALUES (?, ?, 'trial', ?, ?, TRUE)
                    ''', (user_id, trial_plan[0], trial_end, trial_end))
                
                # Generate provider code
                provider_code_new = create_provider_code(
                    user_id, 
                    role,
                    'Professional Practice',
                    'General'
                )
            
            conn.commit()
            conn.close()
            
            if signup_type in ['inline', 'cta']:
                # For inline signups, automatically log them in and redirect to onboarding
                session['user_id'] = user_id
                session['username'] = username
                session['full_name'] = full_name
                session['role'] = role
                
                success_message = f'🎉 Welcome to Sapyyn! Your 14-day free trial has started.'
                if 'provider_code_new' in locals():
                    success_message += f' Your provider code is: {provider_code_new}'
                
                flash(success_message, 'success')
                return redirect(url_for('dashboard'))
            else:
                # For full registration, show success and redirect to login
                if provider_code and provider_info:
                    flash(f'Registration successful! You have been connected to {provider_info[2]} {provider_info[4]} at {provider_info[1]}. Please login.', 'success')
                else:
                    flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
                
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'error')
    
    return render_template('register.html', 
                         provider_code=provider_code, 
                         provider_info=provider_info, 
                         suggested_role=suggested_role)

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

# ============================================================================
# NEW REFERRAL MANAGEMENT API ROUTES
# ============================================================================

@app.route('/api/check-subscription')
def check_subscription():
    """Check if current user has active subscription"""
    if 'user_id' not in session:
        return jsonify({'has_subscription': False, 'message': 'Not authenticated'})
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Check for active subscription or trial
    cursor.execute('''
        SELECT us.subscription_status, us.trial_end_date, sp.plan_name
        FROM user_subscriptions us
        JOIN subscription_plans sp ON us.plan_id = sp.id
        WHERE us.user_id = ? AND us.subscription_status IN ('active', 'trial')
        ORDER BY us.created_at DESC LIMIT 1
    ''', (session['user_id'],))
    
    subscription = cursor.fetchone()
    conn.close()
    
    if subscription:
        status, trial_end, plan_name = subscription
        
        # Check if trial is still valid
        if status == 'trial' and trial_end:
            from datetime import datetime
            trial_end_date = datetime.fromisoformat(trial_end.replace('Z', '+00:00') if trial_end.endswith('Z') else trial_end)
            if trial_end_date < datetime.now():
                return jsonify({'has_subscription': False, 'message': 'Trial expired'})
        
        return jsonify({
            'has_subscription': True, 
            'subscription_status': status,
            'plan_name': plan_name
        })
    
    return jsonify({'has_subscription': False, 'message': 'No active subscription'})

@app.route('/api/provider-code/validate', methods=['POST'])
def validate_provider_code():
    """Validate a 6-character provider code (alphanumeric or numeric)"""
    data = request.get_json()
    provider_code = data.get('provider_code', '').upper().strip()
    
    # Validate format: exactly 6 characters, alphanumeric
    if not provider_code or len(provider_code) != 6 or not provider_code.isalnum():
        return jsonify({'valid': False, 'message': 'Provider code must be exactly 6 alphanumeric characters'})
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT pc.user_id, pc.practice_name, pc.provider_type, pc.specialization, u.full_name
        FROM provider_codes pc
        JOIN users u ON pc.user_id = u.id
        WHERE pc.provider_code = ? AND pc.is_active = TRUE
    ''', (provider_code,))
    
    provider = cursor.fetchone()
    conn.close()
    
    if provider:
        return jsonify({
            'valid': True,
            'provider': {
                'id': provider[0],
                'name': provider[4],
                'practice': provider[1],
                'type': provider[2],
                'specialty': provider[3]
            }
        })
    
    return jsonify({'valid': False, 'message': 'Provider code not found or inactive'})

def check_subscription_required(f):
    """Decorator to check if user has required subscription for referral features"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
        # Check subscription status
        subscription_check = check_subscription()
        subscription_data = subscription_check.get_json()
        
        if not subscription_data.get('has_subscription'):
            return jsonify({
                'success': False, 
                'message': 'Active subscription required for referral features',
                'requires_subscription': True,
                'redirect_url': '/start-free-trial'
            }), 403
        
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/api/referral/emergency', methods=['POST'])
@check_subscription_required
def create_emergency_referral():
    """Create emergency referral with priority processing"""
    try:
        # Generate unique referral ID
        referral_id = str(uuid.uuid4())[:8].upper()
        
        # Get form data
        patient_name = request.form.get('patient_name')
        urgency_level = request.form.get('urgency_level', 'urgent')
        referring_doctor = request.form.get('referring_doctor', session.get('full_name'))
        target_specialty = request.form.get('target_specialty')
        emergency_details = request.form.get('emergency_details')
        contact_number = request.form.get('contact_number')
        
        # Validation
        if not all([patient_name, target_specialty, emergency_details, contact_number]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Create medical condition from emergency details
        medical_condition = f"EMERGENCY: {emergency_details}"
        
        # Generate QR code
        qr_data = f"Emergency Referral\nID: {referral_id}\nPatient: {patient_name}\nUrgency: {urgency_level}\nContact: {contact_number}"
        qr_code = generate_qr_code(qr_data)
        
        # Save to database
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO referrals (
                user_id, referral_id, patient_name, referring_doctor, target_doctor,
                medical_condition, urgency_level, status, notes, qr_code, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'], referral_id, patient_name, referring_doctor, target_specialty,
            medical_condition, urgency_level, 'emergency_pending',
            f"Emergency contact: {contact_number}\nDetails: {emergency_details}",
            qr_code, datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
        # Log the emergency referral creation for audit
        log_compliance_action(
            session['user_id'], 'CREATE', 'emergency_referral', 
            referral_id, f'Emergency referral created for {patient_name}', request
        )
        
        return jsonify({
            'success': True,
            'message': 'Emergency referral submitted successfully. Specialists will be notified immediately.',
            'referral_id': referral_id,
            'redirect_url': f'/referral/track/{referral_id}'
        })
        
    except Exception as e:
        app.logger.error(f'Error creating emergency referral: {str(e)}')
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/referral/routine', methods=['POST'])
@check_subscription_required
def create_routine_referral():
    """Create routine referral with standard processing"""
    try:
        # Generate unique referral ID
        referral_id = str(uuid.uuid4())[:8].upper()
        
        # Get form data
        patient_name = request.form.get('patient_name')
        patient_age = request.form.get('patient_age')
        referring_doctor = request.form.get('referring_doctor', session.get('full_name'))
        target_specialty = request.form.get('target_specialty')
        medical_condition = request.form.get('medical_condition')
        treatment_history = request.form.get('treatment_history', '')
        preferred_date = request.form.get('preferred_date')
        insurance_info = request.form.get('insurance_info', '')
        additional_notes = request.form.get('additional_notes', '')
        
        # Validation
        if not all([patient_name, target_specialty, medical_condition]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Compile notes
        notes_parts = []
        if patient_age:
            notes_parts.append(f"Patient age: {patient_age}")
        if treatment_history:
            notes_parts.append(f"Treatment history: {treatment_history}")
        if preferred_date:
            notes_parts.append(f"Preferred appointment: {preferred_date}")
        if insurance_info:
            notes_parts.append(f"Insurance: {insurance_info}")
        if additional_notes:
            notes_parts.append(f"Additional notes: {additional_notes}")
        
        notes = "\n".join(notes_parts)
        
        # Generate QR code
        qr_data = f"Routine Referral\nID: {referral_id}\nPatient: {patient_name}\nSpecialty: {target_specialty}"
        qr_code = generate_qr_code(qr_data)
        
        # Save to database
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO referrals (
                user_id, referral_id, patient_name, referring_doctor, target_doctor,
                medical_condition, urgency_level, status, notes, qr_code, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'], referral_id, patient_name, referring_doctor, target_specialty,
            medical_condition, 'normal', 'pending', notes, qr_code, datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Routine referral created successfully. You will receive updates on the progress.',
            'referral_id': referral_id,
            'redirect_url': f'/referral/track/{referral_id}'
        })
        
    except Exception as e:
        app.logger.error(f'Error creating routine referral: {str(e)}')
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/consultation/request', methods=['POST'])
@check_subscription_required
def request_consultation():
    """Request consultation with specialist"""
    try:
        # Generate unique consultation ID
        consultation_id = str(uuid.uuid4())[:8].upper()
        
        # Get form data
        consultation_type = request.form.get('consultation_type')
        specialty = request.form.get('specialty')
        case_description = request.form.get('case_description')
        specific_questions = request.form.get('specific_questions', '')
        urgency = request.form.get('urgency', 'normal')
        preferred_method = request.form.get('preferred_method', 'chat')
        
        # Validation
        if not all([consultation_type, specialty, case_description]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Compile consultation details
        consultation_details = f"Type: {consultation_type}\nSpecialty: {specialty}\nCase: {case_description}"
        if specific_questions:
            consultation_details += f"\nQuestions: {specific_questions}"
        
        notes = f"Urgency: {urgency}\nPreferred method: {preferred_method}\nDetails: {consultation_details}"
        
        # Generate QR code for consultation
        qr_data = f"Consultation Request\nID: {consultation_id}\nType: {consultation_type}\nSpecialty: {specialty}"
        qr_code = generate_qr_code(qr_data)
        
        # Save as special referral type
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO referrals (
                user_id, referral_id, patient_name, referring_doctor, target_doctor,
                medical_condition, urgency_level, status, notes, qr_code, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'], consultation_id, f"Consultation Request - {consultation_type}",
            session.get('full_name'), specialty, case_description, urgency, 
            'consultation_pending', notes, qr_code, datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Consultation request submitted successfully. A specialist will contact you soon.',
            'referral_id': consultation_id,
            'redirect_url': f'/consultation/track/{consultation_id}'
        })
        
    except Exception as e:
        app.logger.error(f'Error creating consultation request: {str(e)}')
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/referral/track/<referral_id>')
def track_referral(referral_id):
    """Track referral progress page"""
    if 'user_id' not in session:
        flash('Please log in to track your referral.', 'error')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get referral details
    cursor.execute('''
        SELECT * FROM referrals 
        WHERE referral_id = ? AND user_id = ?
    ''', (referral_id, session['user_id']))
    
    referral = cursor.fetchone()
    conn.close()
    
    if not referral:
        flash('Referral not found.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('track_referral.html', referral=referral)

@app.route('/consultation/track/<consultation_id>')
def track_consultation(consultation_id):
    """Track consultation request page"""
    return track_referral(consultation_id)  # Same functionality for now

# Case Acceptance Management Routes
@app.route('/api/case/update-status', methods=['POST'])
def update_case_status():
    """Update case acceptance status and track conversion pipeline"""
    try:
        data = request.get_json()
        referral_id = data.get('referral_id')
        new_status = data.get('status')  # consultation_scheduled, case_accepted, case_rejected, treatment_started, treatment_completed
        notes = data.get('notes', '')
        estimated_value = data.get('estimated_value')
        actual_value = data.get('actual_value')
        rejection_reason = data.get('rejection_reason')
        
        if not referral_id or not new_status:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        # Update referral with new case status
        update_fields = ['case_status = ?', 'updated_at = ?']
        update_values = [new_status, datetime.now()]
        
        # Set appropriate timestamp based on status
        if new_status == 'consultation_scheduled':
            update_fields.append('consultation_date = ?')
            update_values.append(datetime.now())
        elif new_status == 'case_accepted':
            update_fields.append('case_accepted_date = ?')
            update_values.append(datetime.now())
        elif new_status == 'treatment_started':
            update_fields.append('treatment_start_date = ?')
            update_values.append(datetime.now())
        elif new_status == 'treatment_completed':
            update_fields.append('treatment_complete_date = ?')
            update_values.append(datetime.now())
        
        if estimated_value:
            update_fields.append('estimated_value = ?')
            update_values.append(float(estimated_value))
            
        if actual_value:
            update_fields.append('actual_value = ?')
            update_values.append(float(actual_value))
            
        if rejection_reason:
            update_fields.append('rejection_reason = ?')
            update_values.append(rejection_reason)
        
        update_values.append(referral_id)
        
        cursor.execute(f'''
            UPDATE referrals 
            SET {', '.join(update_fields)}
            WHERE referral_id = ?
        ''', update_values)
        
        # Track conversion stage
        cursor.execute('''
            INSERT INTO case_conversions (referral_id, stage, notes, created_by)
            VALUES (?, ?, ?, ?)
        ''', (referral_id, new_status, notes, session.get('user_id')))
        
        # Update referring doctor stats if case is accepted or rejected
        if new_status in ['case_accepted', 'case_rejected']:
            update_referring_doctor_stats(cursor, referral_id, new_status == 'case_accepted', actual_value or estimated_value)
        
        # Update team metrics
        if session.get('user_id'):
            update_team_metrics(cursor, session['user_id'], new_status)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Case status updated to {new_status.replace("_", " ").title()}',
            'status': new_status
        })
        
    except Exception as e:
        app.logger.error(f'Error updating case status: {str(e)}')
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/conversion-analytics')
def get_conversion_analytics():
    """Get conversion pipeline analytics for dashboard"""
    try:
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        # Get conversion funnel data
        cursor.execute('''
            SELECT 
                case_status,
                COUNT(*) as count,
                AVG(CASE WHEN estimated_value IS NOT NULL THEN estimated_value ELSE 0 END) as avg_estimated_value,
                AVG(CASE WHEN actual_value IS NOT NULL THEN actual_value ELSE 0 END) as avg_actual_value
            FROM referrals 
            WHERE created_at >= date('now', '-30 days')
            GROUP BY case_status
        ''')
        
        conversion_data = {}
        for row in cursor.fetchall():
            conversion_data[row[0] or 'pending'] = {
                'count': row[1],
                'avg_estimated_value': round(row[2] or 0, 2),
                'avg_actual_value': round(row[3] or 0, 2)
            }
        
        # Get referring doctor performance
        cursor.execute('''
            SELECT 
                rd.name,
                rd.referral_count,
                rd.conversion_rate,
                rd.avg_case_value,
                rd.last_referral_date
            FROM referring_doctors rd
            ORDER BY rd.conversion_rate DESC
            LIMIT 10
        ''')
        
        top_referring_doctors = []
        for row in cursor.fetchall():
            top_referring_doctors.append({
                'name': row[0],
                'referral_count': row[1],
                'conversion_rate': row[2],
                'avg_case_value': row[3],
                'last_referral_date': row[4]
            })
        
        # Get team productivity
        cursor.execute('''
            SELECT 
                u.full_name,
                tm.referrals_processed,
                tm.cases_accepted,
                tm.avg_response_time_hours,
                tm.revenue_generated
            FROM team_metrics tm
            JOIN users u ON tm.user_id = u.id
            WHERE tm.date >= date('now', '-7 days')
            ORDER BY tm.revenue_generated DESC
        ''')
        
        team_performance = []
        for row in cursor.fetchall():
            team_performance.append({
                'name': row[0],
                'referrals_processed': row[1],
                'cases_accepted': row[2],
                'avg_response_time': row[3],
                'revenue_generated': row[4]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'conversion_funnel': conversion_data,
            'top_referring_doctors': top_referring_doctors,
            'team_performance': team_performance
        })
        
    except Exception as e:
        app.logger.error(f'Error getting conversion analytics: {str(e)}')
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

def update_referring_doctor_stats(cursor, referral_id, case_accepted, case_value=None):
    """Update referring doctor statistics based on case outcome"""
    try:
        # Get referring doctor name from referral
        cursor.execute('SELECT referring_doctor FROM referrals WHERE referral_id = ?', (referral_id,))
        result = cursor.fetchone()
        if not result or not result[0]:
            return
        
        referring_doctor_name = result[0]
        
        # Check if referring doctor exists in our system
        cursor.execute('SELECT id, referral_count, conversion_rate, avg_case_value FROM referring_doctors WHERE name = ?', 
                      (referring_doctor_name,))
        doctor_record = cursor.fetchone()
        
        if doctor_record:
            # Update existing doctor record
            doctor_id, current_count, current_rate, current_avg = doctor_record
            new_count = current_count + 1
            
            if case_accepted:
                new_conversion_rate = ((current_rate * current_count) + 100) / new_count
                if case_value:
                    new_avg_value = ((current_avg * current_count) + case_value) / new_count
                else:
                    new_avg_value = current_avg
            else:
                new_conversion_rate = (current_rate * current_count) / new_count
                new_avg_value = current_avg
            
            cursor.execute('''
                UPDATE referring_doctors 
                SET referral_count = ?, conversion_rate = ?, avg_case_value = ?, 
                    last_referral_date = ?, updated_at = ?
                WHERE id = ?
            ''', (new_count, round(new_conversion_rate, 2), round(new_avg_value, 2), 
                  datetime.now(), datetime.now(), doctor_id))
        else:
            # Create new doctor record
            initial_rate = 100 if case_accepted else 0
            initial_value = case_value if case_accepted and case_value else 0
            
            cursor.execute('''
                INSERT INTO referring_doctors 
                (name, referral_count, conversion_rate, avg_case_value, last_referral_date)
                VALUES (?, 1, ?, ?, ?)
            ''', (referring_doctor_name, initial_rate, initial_value, datetime.now()))
    
    except Exception as e:
        app.logger.error(f'Error updating referring doctor stats: {str(e)}')

def update_team_metrics(cursor, user_id, status):
    """Update team productivity metrics"""
    try:
        today = datetime.now().date()
        
        # Check if record exists for today
        cursor.execute('SELECT id FROM team_metrics WHERE user_id = ? AND date = ?', (user_id, today))
        existing_record = cursor.fetchone()
        
        if existing_record:
            # Update existing record
            if status in ['consultation_scheduled', 'case_accepted', 'case_rejected']:
                cursor.execute('''
                    UPDATE team_metrics 
                    SET referrals_processed = referrals_processed + 1
                    WHERE user_id = ? AND date = ?
                ''', (user_id, today))
            
            if status == 'consultation_scheduled':
                cursor.execute('''
                    UPDATE team_metrics 
                    SET consultations_completed = consultations_completed + 1
                    WHERE user_id = ? AND date = ?
                ''', (user_id, today))
            
            if status == 'case_accepted':
                cursor.execute('''
                    UPDATE team_metrics 
                    SET cases_accepted = cases_accepted + 1
                    WHERE user_id = ? AND date = ?
                ''', (user_id, today))
        else:
            # Create new record
            referrals_processed = 1 if status in ['consultation_scheduled', 'case_accepted', 'case_rejected'] else 0
            consultations_completed = 1 if status == 'consultation_scheduled' else 0
            cases_accepted = 1 if status == 'case_accepted' else 0
            
            cursor.execute('''
                INSERT INTO team_metrics 
                (user_id, date, referrals_processed, consultations_completed, cases_accepted)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, today, referrals_processed, consultations_completed, cases_accepted))
    
    except Exception as e:
        app.logger.error(f'Error updating team metrics: {str(e)}')

@app.route('/conversion-dashboard')
def conversion_dashboard():
    """Dental specialist conversion dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('conversion_dashboard.html', 
                         analytics_config=ANALYTICS_CONFIG)

def log_compliance_action(user_id, action_type, entity_type, entity_id, action_details, request):
    """Log compliance actions for audit trail"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO compliance_audit_trail 
        (user_id, action_type, entity_type, entity_id, action_details, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, action_type, entity_type, entity_id, action_details, 
          request.remote_addr, request.headers.get('User-Agent', '')))
    
    conn.commit()
    conn.close()

def check_reward_triggers(user_id, referral_id):
    """Check and process reward triggers for a user action"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get active reward programs
    cursor.execute('''
        SELECT rp.*, rt.* FROM reward_programs rp
        JOIN reward_triggers rt ON rp.id = rt.program_id
        WHERE rp.status = 'active' AND rt.is_active = TRUE
    ''')
    active_triggers = cursor.fetchall()
    
    for trigger in active_triggers:
        program_id, trigger_type = trigger[0], trigger[13]
        
        if trigger_type == 'referral_completed':
            # Award points for completed referral
            cursor.execute('''
                INSERT INTO user_rewards 
                (user_id, program_id, referral_id, points_earned, reward_status)
                VALUES (?, ?, ?, ?, 'earned')
            ''', (user_id, program_id, referral_id, trigger[16]))
            
            # Send notification
            cursor.execute('''
                INSERT INTO reward_notifications 
                (user_id, notification_type, title, message)
                VALUES (?, 'reward_earned', 'Reward Earned!', 'You earned points for your referral!')
            ''', (user_id,))
    
    conn.commit()
    conn.close()

@app.route('/rewards')
def rewards_dashboard():
    """Main rewards dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get user's total points
    cursor.execute('''
        SELECT COALESCE(SUM(points_earned), 0) as total_points
        FROM user_rewards 
        WHERE user_id = ? AND reward_status = 'earned'
    ''', (session['user_id'],))
    total_points = cursor.fetchone()[0]
    
    # Get user's recent rewards
    cursor.execute('''
        SELECT ur.*, rp.name as program_name, rt.tier_name
        FROM user_rewards ur
        JOIN reward_programs rp ON ur.program_id = rp.id
        LEFT JOIN reward_tiers rt ON ur.tier_id = rt.id
        WHERE ur.user_id = ?
        ORDER BY ur.earned_date DESC
        LIMIT 10
    ''', (session['user_id'],))
    recent_rewards = cursor.fetchall()
    
    # Get active reward programs
    cursor.execute('''
        SELECT * FROM reward_programs 
        WHERE status = 'active' 
        ORDER BY created_at DESC
    ''', ())
    active_programs = cursor.fetchall()
    
    # Get user achievements
    cursor.execute('''
        SELECT a.*, ua.earned_date, ua.progress
        FROM achievements a
        LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = ?
        WHERE a.is_active = TRUE
        ORDER BY ua.earned_date DESC NULLS LAST
    ''', (session['user_id'],))
    achievements = cursor.fetchall()
    
    # Get notifications
    cursor.execute('''
        SELECT * FROM reward_notifications 
        WHERE user_id = ? AND is_read = FALSE
        ORDER BY sent_at DESC
        LIMIT 5
    ''', (session['user_id'],))
    notifications = cursor.fetchall()
    
    conn.close()
    
    return render_template('rewards/dashboard.html', 
                         total_points=total_points,
                         recent_rewards=recent_rewards,
                         active_programs=active_programs,
                         achievements=achievements,
                         notifications=notifications)

@app.route('/rewards/admin')
def rewards_admin():
    """Rewards administration dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check admin privileges
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
    user_role = cursor.fetchone()[0]
    
    if user_role not in ['admin', 'doctor']:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('rewards_dashboard'))
    
    # Get all reward programs
    cursor.execute('''
        SELECT rp.*, u.full_name as created_by_name
        FROM reward_programs rp
        LEFT JOIN users u ON rp.created_by = u.id
        ORDER BY rp.created_at DESC
    ''')
    programs = cursor.fetchall()
    
    # Get program statistics
    cursor.execute('''
        SELECT 
            rp.id,
            rp.name,
            COUNT(DISTINCT ur.user_id) as participant_count,
            SUM(ur.points_earned) as total_points_awarded,
            COUNT(ur.id) as total_rewards
        FROM reward_programs rp
        LEFT JOIN user_rewards ur ON rp.id = ur.program_id
        GROUP BY rp.id, rp.name
    ''')
    program_stats = cursor.fetchall()
    
    conn.close()
    
    return render_template('rewards/admin.html', 
                         programs=programs, 
                         program_stats=program_stats)

@app.route('/rewards/admin/program/new', methods=['GET', 'POST'])
def new_reward_program():
    """Create new reward program"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check admin privileges
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
    user_role = cursor.fetchone()[0]
    
    if user_role not in ['admin', 'doctor']:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('rewards_dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        program_type = request.form['program_type']
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        compliance_notes = request.form['compliance_notes']
        legal_language = request.form['legal_language']
        
        cursor.execute('''
            INSERT INTO reward_programs 
            (name, description, program_type, start_date, end_date, 
             created_by, compliance_notes, legal_language)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, description, program_type, start_date, end_date,
              session['user_id'], compliance_notes, legal_language))
        
        program_id = cursor.lastrowid
        
        # Log compliance action
        log_compliance_action(session['user_id'], 'CREATE', 'reward_program', 
                            program_id, f'Created reward program: {name}', request)
        
        conn.commit()
        conn.close()
        
        flash('Reward program created successfully!', 'success')
        return redirect(url_for('edit_reward_program', program_id=program_id))
    
    conn.close()
    return render_template('rewards/new_program.html')

@app.route('/rewards/admin/program/<int:program_id>/edit', methods=['GET', 'POST'])
def edit_reward_program(program_id):
    """Edit reward program"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Check admin privileges
    cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
    user_role = cursor.fetchone()[0]
    
    if user_role not in ['admin', 'doctor']:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('rewards_dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        status = request.form['status']
        compliance_notes = request.form['compliance_notes']
        legal_language = request.form['legal_language']
        
        cursor.execute('''
            UPDATE reward_programs 
            SET name = ?, description = ?, status = ?, 
                compliance_notes = ?, legal_language = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (name, description, status, compliance_notes, legal_language, program_id))
        
        # Log compliance action
        log_compliance_action(session['user_id'], 'UPDATE', 'reward_program', 
                            program_id, f'Updated reward program: {name}', request)
        
        conn.commit()
        flash('Reward program updated successfully!', 'success')
    
    # Get program details
    cursor.execute('SELECT * FROM reward_programs WHERE id = ?', (program_id,))
    program = cursor.fetchone()
    
    # Get program tiers
    cursor.execute('SELECT * FROM reward_tiers WHERE program_id = ? ORDER BY tier_level', (program_id,))
    tiers = cursor.fetchall()
    
    # Get program triggers
    cursor.execute('SELECT * FROM reward_triggers WHERE program_id = ?', (program_id,))
    triggers = cursor.fetchall()
    
    conn.close()
    
    return render_template('rewards/edit_program.html', 
                         program=program, tiers=tiers, triggers=triggers)

@app.route('/rewards/admin/program/<int:program_id>/tier/new', methods=['POST'])
def add_reward_tier(program_id):
    """Add new reward tier"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Check admin privileges
    cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
    user_role = cursor.fetchone()[0]
    
    if user_role not in ['admin', 'doctor']:
        return jsonify({'error': 'Access denied'}), 403
    
    tier_name = request.form['tier_name']
    tier_level = request.form['tier_level']
    referrals_required = request.form['referrals_required']
    reward_type = request.form['reward_type']
    reward_value = request.form['reward_value']
    reward_description = request.form['reward_description']
    fulfillment_type = request.form['fulfillment_type']
    fulfillment_config = request.form.get('fulfillment_config', '')
    
    cursor.execute('''
        INSERT INTO reward_tiers 
        (program_id, tier_name, tier_level, referrals_required, reward_type,
         reward_value, reward_description, fulfillment_type, fulfillment_config)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (program_id, tier_name, tier_level, referrals_required, reward_type,
          reward_value, reward_description, fulfillment_type, fulfillment_config))
    
    # Log compliance action
    log_compliance_action(session['user_id'], 'CREATE', 'reward_tier', 
                        cursor.lastrowid, f'Created tier: {tier_name}', request)
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Tier added successfully'})

@app.route('/rewards/leaderboard')
def rewards_leaderboard():
    """Rewards leaderboard with gamification"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get top users by points (anonymized for HIPAA compliance)
    cursor.execute('''
        SELECT 
            CASE 
                WHEN u.id = ? THEN u.full_name 
                ELSE 'User ' || SUBSTR(u.full_name, 1, 1) || '***'
            END as display_name,
            SUM(ur.points_earned) as total_points,
            COUNT(ur.id) as total_rewards,
            CASE WHEN u.id = ? THEN 1 ELSE 0 END as is_current_user
        FROM users u
        JOIN user_rewards ur ON u.id = ur.user_id
        WHERE ur.reward_status = 'earned'
        GROUP BY u.id, u.full_name
        ORDER BY total_points DESC
        LIMIT 20
    ''', (session['user_id'], session['user_id']))
    leaderboard = cursor.fetchall()
    
    # Get user's rank
    cursor.execute('''
        SELECT COUNT(*) + 1 as user_rank
        FROM (
            SELECT SUM(ur.points_earned) as total_points
            FROM user_rewards ur
            WHERE ur.reward_status = 'earned'
            GROUP BY ur.user_id
            HAVING total_points > (
                SELECT SUM(ur2.points_earned)
                FROM user_rewards ur2
                WHERE ur2.user_id = ? AND ur2.reward_status = 'earned'
            )
        )
    ''', (session['user_id'],))
    user_rank = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('rewards/leaderboard.html', 
                         leaderboard=leaderboard, user_rank=user_rank)

@app.route('/rewards/compliance/audit')
def compliance_audit():
    """Compliance audit trail"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Check admin privileges
    cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
    user_role = cursor.fetchone()[0]
    
    if user_role not in ['admin']:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('rewards_dashboard'))
    
    # Get audit trail
    cursor.execute('''
        SELECT cat.*, u.full_name as user_name
        FROM compliance_audit_trail cat
        JOIN users u ON cat.user_id = u.id
        ORDER BY cat.timestamp DESC
        LIMIT 100
    ''')
    audit_entries = cursor.fetchall()
    
    conn.close()
    
    return render_template('rewards/compliance_audit.html', audit_entries=audit_entries)

@app.route('/api/rewards/notifications/mark-read', methods=['POST'])
def mark_notifications_read():
    """Mark reward notifications as read"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE reward_notifications 
        SET is_read = TRUE 
        WHERE user_id = ? AND is_read = FALSE
    ''', (session['user_id'],))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/rewards/trigger-check', methods=['POST'])
def trigger_reward_check():
    """Manually trigger reward check (for testing/admin)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    referral_id = request.json.get('referral_id')
    target_user_id = request.json.get('user_id', session['user_id'])
    
    check_reward_triggers(target_user_id, referral_id)
    
    return jsonify({'success': True, 'message': 'Rewards check completed'})

# Update referral completion to trigger rewards
def update_referral_completion_hook(referral_id, user_id):
    """Hook to trigger reward checks when referral is completed"""
    check_reward_triggers(user_id, referral_id)

@app.route('/profile')
def profile():
    """User profile page"""
    if 'user_id' not in session:
        flash('Please log in to access your profile.', 'error')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get user information
    cursor.execute('''
        SELECT username, email, full_name, role, created_at
        FROM users 
        WHERE id = ?
    ''', (session['user_id'],))
    
    user = cursor.fetchone()
    
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('logout'))
    
    # Get user stats
    cursor.execute('''
        SELECT COUNT(*) as total_referrals
        FROM referrals 
        WHERE user_id = ?
    ''', (session['user_id'],))
    
    stats = cursor.fetchone()
    total_referrals = stats[0] if stats else 0
    
    # Get user documents count
    cursor.execute('''
        SELECT COUNT(*) as total_documents
        FROM documents 
        WHERE user_id = ?
    ''', (session['user_id'],))
    
    doc_stats = cursor.fetchone()
    total_documents = doc_stats[0] if doc_stats else 0
    
    conn.close()
    
    user_data = {
        'username': user[0],
        'email': user[1],
        'full_name': user[2],
        'role': user[3],
        'created_at': user[4],
        'total_referrals': total_referrals,
        'total_documents': total_documents
    }
    
    return render_template('profile.html', user=user_data)

@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    """Edit user profile"""
    if 'user_id' not in session:
        flash('Please log in to access your profile.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        
        if not full_name or not email:
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('edit_profile'))
        
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users 
                SET full_name = ?, email = ?
                WHERE id = ?
            ''', (full_name, email, session['user_id']))
            
            conn.commit()
            flash('Profile updated successfully!', 'success')
            
            # Update session data
            session['full_name'] = full_name
            
        except sqlite3.IntegrityError:
            flash('Email address is already in use.', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('profile'))
    
    # GET request - show edit form
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT username, email, full_name, role
        FROM users 
        WHERE id = ?
    ''', (session['user_id'],))
    
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('logout'))
    
    user_data = {
        'username': user[0],
        'email': user[1],
        'full_name': user[2],
        'role': user[3]
    }
    
    return render_template('edit_profile.html', user=user_data)

@app.route('/settings')
def settings():
    """User settings page"""
    if 'user_id' not in session:
        flash('Please log in to access settings.', 'error')
        return redirect(url_for('login'))
    
    return render_template('settings.html')

@app.route('/settings/password', methods=['POST'])
def change_password():
    """Change user password"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        flash('Please fill in all password fields.', 'error')
        return redirect(url_for('settings'))
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('settings'))
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters long.', 'error')
        return redirect(url_for('settings'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Verify current password
    cursor.execute('''
        SELECT password_hash FROM users WHERE id = ?
    ''', (session['user_id'],))
    
    user = cursor.fetchone()
    
    if not user or not check_password_hash(user[0], current_password):
        flash('Current password is incorrect.', 'error')
        conn.close()
        return redirect(url_for('settings'))
    
    # Update password
    new_password_hash = generate_password_hash(new_password)
    cursor.execute('''
        UPDATE users SET password_hash = ? WHERE id = ?
    ''', (new_password_hash, session['user_id']))
    
    conn.commit()
    conn.close()
    
    flash('Password changed successfully!', 'success')
    return redirect(url_for('settings'))

def generate_provider_code():
    """Generate a unique 6-character alphanumeric provider code"""
    import random
    import string
    
    # Use alphanumeric characters (excluding confusing ones like 0, O, I, 1, L)
    chars = '23456789ABCDEFGHJKMNPQRSTUVWXYZ'
    
    max_attempts = 100  # Prevent infinite loops
    attempt = 0
    
    while attempt < max_attempts:
        # Generate 6-character alphanumeric code
        code = ''.join(random.choice(chars) for _ in range(6))
        
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM provider_codes WHERE provider_code = ?', (code,))
        if not cursor.fetchone():
            conn.close()
            return code
        conn.close()
        attempt += 1
    
    # Fallback if we can't find a unique code (very unlikely with 30^6 combinations)
    raise Exception("Unable to generate unique provider code after 100 attempts")

def check_role_permission(required_roles, user_role=None):
    """Check if user has permission for required roles"""
    if user_role is None:
        user_role = session.get('role')
    
    if not user_role:
        return False
    
    # Convert single role to list for uniform handling
    if isinstance(required_roles, str):
        required_roles = [required_roles]
    
    return user_role in required_roles

def require_roles(required_roles):
    """Decorator to require specific roles for routes"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('login'))
            
            if not check_role_permission(required_roles):
                flash('Access denied. You do not have permission to view this page.', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

def get_user_subscription(user_id):
    """Get user's current subscription details"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT us.*, sp.plan_name, sp.plan_type, sp.features, sp.max_referrals, sp.support_level
        FROM user_subscriptions us
        JOIN subscription_plans sp ON us.plan_id = sp.id
        WHERE us.user_id = ? AND us.subscription_status = 'active'
        ORDER BY us.created_at DESC LIMIT 1
    ''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def create_provider_code(user_id, provider_type, practice_name=None, specialization=None):
    """Create a provider code for a user (dentists and specialists only)"""
    
    # Only create provider codes for dentists and specialists
    valid_provider_types = ['dentist', 'specialist', 'dentist_admin', 'specialist_admin']
    if provider_type not in valid_provider_types:
        raise ValueError(f"Provider codes can only be created for dentists and specialists, not {provider_type}")
    
    # Check if user already has an active provider code
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT provider_code FROM provider_codes 
        WHERE user_id = ? AND is_active = TRUE
    ''', (user_id,))
    existing_code = cursor.fetchone()
    
    if existing_code:
        conn.close()
        return existing_code[0]  # Return existing code
    
    # Generate new code
    code = generate_provider_code()
    
    cursor.execute('''
        INSERT INTO provider_codes (user_id, provider_code, provider_type, practice_name, specialization)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, code, provider_type, practice_name, specialization))
    conn.commit()
    conn.close()
    return code

@app.route('/pricing')
def pricing():
    """Pricing plans page"""
    return render_template('pricing.html')

# Portal Routes for Different User Types

@app.route('/portal/dentist')
@require_roles(['dentist', 'dentist_admin'])
def dentist_portal():
    """Dentist portal dashboard"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get dentist's provider code
    cursor.execute('''
        SELECT provider_code, practice_name, specialization 
        FROM provider_codes 
        WHERE user_id = ? AND provider_type IN ('dentist', 'dentist_admin') AND is_active = TRUE
    ''', (session['user_id'],))
    provider_info = cursor.fetchone()
    
    # Create provider code if none exists
    if not provider_info:
        try:
            new_code = create_provider_code(
                session['user_id'], 
                session.get('role', 'dentist'),
                'Professional Practice',
                'General Dentistry'
            )
            provider_info = (new_code, 'Professional Practice', 'General Dentistry')
        except ValueError as e:
            flash(f'Error creating provider code: {str(e)}', 'error')
            provider_info = None
    
    # Get referral stats (only referrals created by this dentist)
    cursor.execute('''
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
               SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
               SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted
        FROM referrals WHERE user_id = ?
    ''', (session['user_id'],))
    stats = cursor.fetchone()
    
    # Get recent referrals created by this dentist
    cursor.execute('''
        SELECT referral_id, patient_name, target_doctor, status, created_at, medical_condition
        FROM referrals 
        WHERE user_id = ? 
        ORDER BY created_at DESC LIMIT 5
    ''', (session['user_id'],))
    recent_referrals = cursor.fetchall()
    
    # Get incoming referrals if this is a specialist dentist
    cursor.execute('''
        SELECT COUNT(*) as incoming_total
        FROM referrals 
        WHERE target_doctor LIKE ? OR target_doctor = ?
    ''', (f"%{session['full_name']}%", session['full_name']))
    incoming_stats = cursor.fetchone()
    
    conn.close()
    
    return render_template('portal/dentist.html', 
                         provider_info=provider_info,
                         stats=stats,
                         recent_referrals=recent_referrals,
                         incoming_stats=incoming_stats,
                         user_role=session.get('role'))

@app.route('/portal/specialist')
@require_roles(['specialist', 'specialist_admin'])
def specialist_portal():
    """Specialist portal dashboard"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get specialist's provider code
    cursor.execute('''
        SELECT provider_code, practice_name, specialization 
        FROM provider_codes 
        WHERE user_id = ? AND provider_type IN ('specialist', 'specialist_admin') AND is_active = TRUE
    ''', (session['user_id'],))
    provider_info = cursor.fetchone()
    
    # Create provider code if none exists
    if not provider_info:
        try:
            new_code = create_provider_code(
                session['user_id'], 
                session.get('role', 'specialist'),
                'Specialist Practice',
                'Specialty Care'
            )
            provider_info = (new_code, 'Specialist Practice', 'Specialty Care')
        except ValueError as e:
            flash(f'Error creating provider code: {str(e)}', 'error')
            provider_info = None
    
    # Get incoming referrals for this specialist
    cursor.execute('''
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
               SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted,
               SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
        FROM referrals 
        WHERE target_doctor = ? OR target_doctor LIKE ?
    ''', (session['full_name'], f"%{session['full_name']}%"))
    incoming_stats = cursor.fetchone()
    
    # Get referrals created by this specialist (if they also refer patients)
    cursor.execute('''
        SELECT COUNT(*) as outgoing_total,
               SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as outgoing_pending
        FROM referrals WHERE user_id = ?
    ''', (session['user_id'],))
    outgoing_stats = cursor.fetchone()
    
    # Get recent incoming referrals
    cursor.execute('''
        SELECT referral_id, patient_name, referring_doctor, status, created_at, medical_condition, urgency_level
        FROM referrals 
        WHERE target_doctor = ? OR target_doctor LIKE ?
        ORDER BY created_at DESC LIMIT 10
    ''', (session['full_name'], f"%{session['full_name']}%"))
    incoming_referrals = cursor.fetchall()
    
    conn.close()
    
    return render_template('portal/specialist.html',
                         provider_info=provider_info,
                         incoming_stats=incoming_stats,
                         outgoing_stats=outgoing_stats,
                         incoming_referrals=incoming_referrals,
                         user_role=session.get('role'))

@app.route('/portal/patient')
@require_roles(['patient'])
def patient_portal():
    """Patient portal dashboard"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get patient's referrals (referrals where they are the subject)
    cursor.execute('''
        SELECT referral_id, referring_doctor, target_doctor, medical_condition, status, created_at, urgency_level
        FROM referrals 
        WHERE patient_name LIKE ? OR notes LIKE ?
        ORDER BY created_at DESC LIMIT 10
    ''', (f"%{session['full_name']}%", f"%{session['full_name']}%"))
    referrals = cursor.fetchall()
    
    # Get patient's documents
    cursor.execute('''
        SELECT file_name, file_type, upload_date
        FROM documents 
        WHERE user_id = ?
        ORDER BY upload_date DESC LIMIT 5
    ''', (session['user_id'],))
    documents = cursor.fetchall()
    
    # Get referral summary stats for patient
    cursor.execute('''
        SELECT COUNT(*) as total_referrals,
               SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
               SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted,
               SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
        FROM referrals 
        WHERE patient_name LIKE ? OR notes LIKE ?
    ''', (f"%{session['full_name']}%", f"%{session['full_name']}%"))
    referral_stats = cursor.fetchone()
    
    conn.close()
    
    return render_template('portal/patient.html',
                         referrals=referrals,
                         documents=documents,
                         referral_stats=referral_stats,
                         user_role=session.get('role'))

@app.route('/portal/admin')
@require_roles(['dentist_admin', 'specialist_admin', 'admin'])
def admin_portal():
    """Admin portal for practice management"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    user_role = session.get('role')
    
    # Get practice information based on admin type
    if user_role == 'admin':
        # Super admin can see all practices
        cursor.execute('''
            SELECT p.*, us.plan_id, sp.plan_name, sp.plan_type, u.full_name as admin_name
            FROM practices p
            LEFT JOIN user_subscriptions us ON p.subscription_id = us.id
            LEFT JOIN subscription_plans sp ON us.plan_id = sp.id
            LEFT JOIN users u ON p.admin_user_id = u.id
            ORDER BY p.created_at DESC
        ''')
        practices_info = cursor.fetchall()
        practice_info = None  # Admin sees all practices, not just one
    else:
        # Practice-specific admin
        cursor.execute('''
            SELECT p.*, us.plan_id, sp.plan_name, sp.plan_type
            FROM practices p
            LEFT JOIN user_subscriptions us ON p.subscription_id = us.id
            LEFT JOIN subscription_plans sp ON us.plan_id = sp.id
            WHERE p.admin_user_id = ?
        ''', (session['user_id'],))
        practice_info = cursor.fetchone()
        practices_info = [practice_info] if practice_info else []
    
    # Get practice members (based on admin level)
    if user_role == 'admin':
        # Super admin sees all users
        cursor.execute('''
            SELECT u.id, u.full_name, u.email, u.role, u.created_at, u.is_verified,
                   pc.provider_code, pc.practice_name as provider_practice
            FROM users u
            LEFT JOIN provider_codes pc ON u.id = pc.user_id AND pc.is_active = TRUE
            ORDER BY u.created_at DESC
            LIMIT 50
        ''')
        members = cursor.fetchall()
    else:
        # Practice admin sees their practice members
        cursor.execute('''
            SELECT pm.*, u.full_name, u.email, u.role, u.created_at,
                   pc.provider_code, pc.practice_name as provider_practice
            FROM practice_members pm
            JOIN users u ON pm.user_id = u.id
            LEFT JOIN provider_codes pc ON u.id = pc.user_id AND pc.is_active = TRUE
            WHERE pm.practice_id = (SELECT id FROM practices WHERE admin_user_id = ?)
        ''', (session['user_id'],))
        members = cursor.fetchall()
    
    # Get comprehensive stats based on admin level
    if user_role == 'admin':
        # System-wide stats for super admin
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT u.id) as total_users,
                COUNT(DISTINCT CASE WHEN u.role IN ('dentist', 'dentist_admin') THEN u.id END) as total_dentists,
                COUNT(DISTINCT CASE WHEN u.role IN ('specialist', 'specialist_admin') THEN u.id END) as total_specialists,
                COUNT(DISTINCT CASE WHEN u.role = 'patient' THEN u.id END) as total_patients,
                COUNT(DISTINCT r.id) as total_referrals,
                COUNT(DISTINCT CASE WHEN r.status = 'pending' THEN r.id END) as pending_referrals,
                COUNT(DISTINCT pc.id) as active_provider_codes
            FROM users u
            LEFT JOIN referrals r ON u.id = r.user_id
            LEFT JOIN provider_codes pc ON u.id = pc.user_id AND pc.is_active = TRUE
        ''')
    else:
        # Practice-specific stats
        cursor.execute('''
            SELECT COUNT(*) as total_referrals,
                   COUNT(DISTINCT user_id) as active_users,
                   SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_referrals,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_referrals
            FROM referrals 
            WHERE user_id IN (
                SELECT user_id FROM practice_members 
                WHERE practice_id = (SELECT id FROM practices WHERE admin_user_id = ?)
            )
        ''', (session['user_id'],))
    
    stats = cursor.fetchone()
    
    # Get recent system activity for admins
    cursor.execute('''
        SELECT 'referral' as activity_type, referral_id as item_id, patient_name as description, 
               status, created_at, u.full_name as user_name
        FROM referrals r
        JOIN users u ON r.user_id = u.id
        {} 
        ORDER BY created_at DESC 
        LIMIT 10
    '''.format(
        '' if user_role == 'admin' else 
        'WHERE r.user_id IN (SELECT user_id FROM practice_members WHERE practice_id = (SELECT id FROM practices WHERE admin_user_id = ?))'
    ), (session['user_id'],) if user_role != 'admin' else ())
    recent_activity = cursor.fetchall()
    
    conn.close()
    
    return render_template('portal/admin.html',
                         practice_info=practice_info,
                         practices_info=practices_info,
                         members=members,
                         stats=stats,
                         recent_activity=recent_activity,
                         user_role=user_role,
                         is_super_admin=(user_role == 'admin'))

@app.route('/portal/messages')
def messages_portal():
    """Messages portal for all user types"""
    if 'user_id' not in session:
        flash('Please log in to access messages.', 'error')
        return redirect(url_for('login'))
    
    return render_template('messages.html', user_role=session.get('role'))

@app.route('/portal/provider-code/generate', methods=['POST'])
@require_roles(['dentist', 'dentist_admin', 'specialist', 'specialist_admin'])
def generate_new_provider_code():
    """Generate new provider code for user (dentists and specialists only)"""
    data = request.get_json()
    provider_type = data.get('provider_type', session.get('role'))
    practice_name = data.get('practice_name', 'Professional Practice')
    specialization = data.get('specialization', 'General')
    
    # Validate provider type matches user role
    user_role = session.get('role')
    valid_combinations = {
        'dentist': ['dentist'],
        'dentist_admin': ['dentist', 'dentist_admin'],
        'specialist': ['specialist'],
        'specialist_admin': ['specialist', 'specialist_admin']
    }
    
    if provider_type not in valid_combinations.get(user_role, []):
        return jsonify({'error': f'Cannot create {provider_type} code for {user_role} user'}), 400
    
    try:
        new_code = create_provider_code(session['user_id'], provider_type, practice_name, specialization)
        return jsonify({
            'success': True, 
            'provider_code': new_code,
            'message': f'New 6-character alphanumeric provider code generated: {new_code}'
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to generate provider code: {str(e)}'}), 500

@app.route('/api/quick-referral', methods=['POST'])
def create_quick_referral():
    """Create a quick referral using provider code from popup form"""
    try:
        data = request.get_json()
        provider_code = data.get('provider_code', '').upper().strip()
        patient_name = data.get('patient_name', '').strip()
        patient_phone = data.get('patient_phone', '').strip()
        medical_condition = data.get('medical_condition', '').strip()
        urgency_level = data.get('urgency_level', 'normal')
        notes = data.get('notes', '').strip()
        
        # Validation
        if not provider_code or not patient_name:
            return jsonify({'success': False, 'message': 'Provider code and patient name are required'}), 400
        
        if len(provider_code) != 6 or not provider_code.isalnum():
            return jsonify({'success': False, 'message': 'Provider code must be exactly 6 alphanumeric characters'}), 400
        
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        # Find provider by code
        cursor.execute('''
            SELECT pc.user_id, pc.practice_name, u.full_name, pc.provider_type, pc.specialization
            FROM provider_codes pc
            JOIN users u ON pc.user_id = u.id
            WHERE pc.provider_code = ? AND pc.is_active = TRUE
        ''', (provider_code,))
        
        provider = cursor.fetchone()
        
        if not provider:
            conn.close()
            return jsonify({'success': False, 'message': 'Provider code not found or inactive'}), 404
        
        # Verify provider is a dentist or specialist
        if provider[3] not in ['dentist', 'dentist_admin', 'specialist', 'specialist_admin']:
            conn.close()
            return jsonify({'success': False, 'message': 'Provider code is not valid for referrals'}), 400
        
        # Generate referral ID and QR code
        referral_id = str(uuid.uuid4())[:8].upper()
        qr_data = f"Quick Referral\nID: {referral_id}\nPatient: {patient_name}\nProvider: {provider[2]}"
        qr_code = generate_qr_code(qr_data)
        
        # Compile notes
        compiled_notes = f"Quick referral via provider code {provider_code}"
        if patient_phone:
            compiled_notes += f"\nPatient phone: {patient_phone}"
        if notes:
            compiled_notes += f"\nAdditional notes: {notes}"
        
        # Create referral
        cursor.execute('''
            INSERT INTO referrals (
                user_id, referral_id, patient_name, referring_doctor, target_doctor, 
                medical_condition, urgency_level, status, notes, qr_code, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            provider[0], referral_id, patient_name, 'Quick Referral', provider[2], 
            medical_condition or 'General consultation', urgency_level, 'pending', 
            compiled_notes, qr_code, datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'referral_id': referral_id,
            'provider': {
                'name': provider[2],
                'practice': provider[1],
                'type': provider[3],
                'specialty': provider[4]
            },
            'message': f'Quick referral created successfully to {provider[2]} at {provider[1]}'
        })
        
    except Exception as e:
        app.logger.error(f'Error creating quick referral: {str(e)}')
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

# Messages API endpoints
@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Get messages for the current user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        user_id = session['user_id']
        message_type = request.args.get('type', 'all')  # 'sent', 'received', 'all'
        
        if message_type == 'sent':
            cursor.execute('''
                SELECT m.id, m.subject, m.content, m.message_type, m.referral_id, 
                       m.is_read, m.created_at, u.full_name as recipient_name,
                       u.role as recipient_role
                FROM messages m
                JOIN users u ON m.recipient_id = u.id
                WHERE m.sender_id = ? AND m.is_deleted_by_sender = FALSE
                ORDER BY m.created_at DESC
            ''', (user_id,))
        elif message_type == 'received':
            cursor.execute('''
                SELECT m.id, m.subject, m.content, m.message_type, m.referral_id,
                       m.is_read, m.created_at, u.full_name as sender_name,
                       u.role as sender_role
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE m.recipient_id = ? AND m.is_deleted_by_recipient = FALSE
                ORDER BY m.created_at DESC
            ''', (user_id,))
        else:  # all messages
            cursor.execute('''
                SELECT m.id, m.subject, m.content, m.message_type, m.referral_id,
                       m.is_read, m.created_at, 
                       CASE WHEN m.sender_id = ? THEN u2.full_name ELSE u1.full_name END as contact_name,
                       CASE WHEN m.sender_id = ? THEN u2.role ELSE u1.role END as contact_role,
                       CASE WHEN m.sender_id = ? THEN 'sent' ELSE 'received' END as direction
                FROM messages m
                JOIN users u1 ON m.sender_id = u1.id
                JOIN users u2 ON m.recipient_id = u2.id
                WHERE (m.sender_id = ? AND m.is_deleted_by_sender = FALSE) 
                   OR (m.recipient_id = ? AND m.is_deleted_by_recipient = FALSE)
                ORDER BY m.created_at DESC
            ''', (user_id, user_id, user_id, user_id, user_id))
        
        messages = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        message_list = []
        for msg in messages:
            message_list.append({
                'id': msg[0],
                'subject': msg[1],
                'content': msg[2],
                'message_type': msg[3],
                'referral_id': msg[4],
                'is_read': msg[5],
                'created_at': msg[6],
                'contact_name': msg[7],
                'contact_role': msg[8],
                'direction': msg[9] if len(msg) > 9 else message_type
            })
        
        return jsonify({'success': True, 'messages': message_list})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/messages', methods=['POST'])
def send_message():
    """Send a new message"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['recipient_id', 'subject', 'content']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        sender_id = session['user_id']
        recipient_id = data['recipient_id']
        subject = data['subject']
        content = data['content']
        message_type = data.get('message_type', 'general')
        referral_id = data.get('referral_id')
        
        # Verify recipient exists
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE id = ?', (recipient_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Recipient not found'}), 404
        
        # Insert message
        cursor.execute('''
            INSERT INTO messages (sender_id, recipient_id, subject, content, message_type, referral_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (sender_id, recipient_id, subject, content, message_type, referral_id))
        
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message_id': message_id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/messages/<int:message_id>/read', methods=['POST'])
def mark_message_read(message_id):
    """Mark a message as read"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        user_id = session['user_id']
        
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        # Verify user is the recipient of this message
        cursor.execute('''
            SELECT id FROM messages 
            WHERE id = ? AND recipient_id = ?
        ''', (message_id, user_id))
        
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Message not found or access denied'}), 404
        
        # Mark as read
        cursor.execute('''
            UPDATE messages 
            SET is_read = TRUE, read_at = CURRENT_TIMESTAMP
            WHERE id = ? AND recipient_id = ?
        ''', (message_id, user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    """Delete a message (soft delete)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        user_id = session['user_id']
        
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        # Check if user is sender or recipient
        cursor.execute('''
            SELECT sender_id, recipient_id FROM messages WHERE id = ?
        ''', (message_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'success': False, 'error': 'Message not found'}), 404
        
        sender_id, recipient_id = result
        
        # Soft delete based on user role
        if user_id == sender_id:
            cursor.execute('''
                UPDATE messages SET is_deleted_by_sender = TRUE WHERE id = ?
            ''', (message_id,))
        elif user_id == recipient_id:
            cursor.execute('''
                UPDATE messages SET is_deleted_by_recipient = TRUE WHERE id = ?
            ''', (message_id,))
        else:
            conn.close()
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/contacts')
def get_user_contacts():
    """Get list of users that can be messaged"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        user_id = session['user_id']
        user_role = session.get('role', 'patient')
        
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        # Different contact lists based on user role
        if user_role == 'patient':
            # Patients can message dentists and specialists
            cursor.execute('''
                SELECT id, full_name, role, email 
                FROM users 
                WHERE role IN ('dentist', 'specialist', 'dentist_admin', 'specialist_admin') 
                AND id != ?
                ORDER BY full_name
            ''', (user_id,))
        elif user_role in ['dentist', 'dentist_admin']:
            # Dentists can message patients, specialists, and admins
            cursor.execute('''
                SELECT id, full_name, role, email 
                FROM users 
                WHERE role IN ('patient', 'specialist', 'specialist_admin', 'admin') 
                AND id != ?
                ORDER BY full_name
            ''', (user_id,))
        elif user_role in ['specialist', 'specialist_admin']:
            # Specialists can message patients, dentists, and admins
            cursor.execute('''
                SELECT id, full_name, role, email 
                FROM users 
                WHERE role IN ('patient', 'dentist', 'dentist_admin', 'admin') 
                AND id != ?
                ORDER BY full_name
            ''', (user_id,))
        else:  # admin
            # Admins can message everyone
            cursor.execute('''
                SELECT id, full_name, role, email 
                FROM users 
                WHERE id != ?
                ORDER BY full_name
            ''', (user_id,))
        
        contacts = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        contact_list = []
        for contact in contacts:
            contact_list.append({
                'id': contact[0],
                'name': contact[1],
                'role': contact[2],
                'email': contact[3]
            })
        
        return jsonify({'success': True, 'contacts': contact_list})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/referral/<referral_id>')
def get_referral_detail(referral_id):
    """Get detailed referral information"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        # Get referral details with access control
        user_role = session.get('role', 'patient')
        user_id = session['user_id']
        
        if user_role in ['dentist', 'dentist_admin']:
            # Dentists can see their own referrals
            cursor.execute('SELECT * FROM referrals WHERE referral_id = ? AND user_id = ?', 
                         (referral_id, user_id))
        elif user_role in ['specialist', 'specialist_admin']:
            # Specialists can see referrals sent to them or created by them
            user_full_name = session.get('full_name', '')
            cursor.execute('''SELECT * FROM referrals 
                            WHERE referral_id = ? AND (user_id = ? OR target_doctor = ?)''', 
                         (referral_id, user_id, user_full_name))
        else:
            # Patients can see referrals related to them
            patient_name = session.get('full_name', '')
            cursor.execute('''SELECT * FROM referrals 
                            WHERE referral_id = ? AND (patient_name LIKE ? OR user_id = ?)''', 
                         (referral_id, f'%{patient_name}%', user_id))
        
        referral = cursor.fetchone()
        conn.close()
        
        if not referral:
            return jsonify({'success': False, 'error': 'Referral not found or access denied'}), 404
        
        # Convert to dictionary
        referral_dict = {
            'id': referral[0],
            'user_id': referral[1],
            'referral_id': referral[2],
            'patient_name': referral[3],
            'referring_doctor': referral[4],
            'target_doctor': referral[5],
            'medical_condition': referral[6],
            'urgency_level': referral[7],
            'status': referral[8],
            'notes': referral[9],
            'qr_code': referral[10],
            'created_at': referral[11],
            'updated_at': referral[12],
            'case_status': referral[13] if len(referral) > 13 else None,
            'consultation_date': referral[14] if len(referral) > 14 else None,
            'case_accepted_date': referral[15] if len(referral) > 15 else None,
            'treatment_start_date': referral[16] if len(referral) > 16 else None,
            'treatment_complete_date': referral[17] if len(referral) > 17 else None,
            'rejection_reason': referral[18] if len(referral) > 18 else None,
            'estimated_value': referral[19] if len(referral) > 19 else None,
            'actual_value': referral[20] if len(referral) > 20 else None
        }
        
        return jsonify({'success': True, 'referral': referral_dict})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/referral/by-code', methods=['POST'])
def create_referral_by_code():
    """Create referral using provider code"""
    data = request.get_json()
    provider_code = data.get('provider_code', '').upper().strip()  # Normalize to uppercase
    patient_name = data.get('patient_name')
    referring_doctor = data.get('referring_doctor', 'Self-referral')
    medical_condition = data.get('medical_condition', '')
    
    if not provider_code or not patient_name:
        return jsonify({'error': 'Provider code and patient name are required'}), 400
    
    # Validate provider code format (6 alphanumeric characters)
    if len(provider_code) != 6 or not provider_code.isalnum():
        return jsonify({'error': 'Provider code must be exactly 6 alphanumeric characters'}), 400
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
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
    
    # Provider Codes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS provider_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            provider_code TEXT UNIQUE NOT NULL,
            provider_type TEXT NOT NULL,
            practice_name TEXT,
            specialization TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Appointments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id TEXT UNIQUE NOT NULL,
            patient_id INTEGER,
            provider_id INTEGER NOT NULL,
            referral_id TEXT,
            appointment_type TEXT DEFAULT 'consultation',
            appointment_date TIMESTAMP NOT NULL,
            duration_minutes INTEGER DEFAULT 60,
            status TEXT DEFAULT 'scheduled',
            notes TEXT,
            patient_name TEXT,
            patient_email TEXT,
            patient_phone TEXT,
            reason TEXT,
            location TEXT,
            virtual_meeting_link TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES users (id),
            FOREIGN KEY (provider_id) REFERENCES users (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Promotions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promotions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            image_path TEXT,
            image_filename TEXT,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            status TEXT DEFAULT 'draft',
            target_audience TEXT,
            budget DECIMAL(10,2),
            impressions INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            click_through_rate DECIMAL(5,4) DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # User Feedback table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            visit_purpose TEXT,
            ease_of_use TEXT,
            confusion_feedback TEXT,
            nps_score INTEGER,
            additional_comments TEXT,
            contact_email TEXT,
            page_url TEXT,
            page_title TEXT,
            timestamp TEXT,
            server_timestamp TEXT,
            ip_address TEXT,
            user_agent TEXT,
            screen_resolution TEXT,
            session_duration INTEGER,
            user_role TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Fraud Detection tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fraud_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ip_address TEXT,
            email TEXT,
            device_fingerprint TEXT,
            fraud_score DECIMAL(5,2) DEFAULT 0.0,
            risk_level TEXT DEFAULT 'low',
            is_paused BOOLEAN DEFAULT FALSE,
            reasons TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Seed initial admin user
    cursor.execute("SELECT id FROM users WHERE email = ?", (INITIAL_ADMIN['email'],))
    if cursor.fetchone() is None:
        password_hash = generate_password_hash(generate_secure_password())
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, role, is_verified)
            VALUES (?, ?, ?, ?, ?, TRUE)
        ''', (
            INITIAL_ADMIN['username'],
            INITIAL_ADMIN['email'],
            password_hash,
            INITIAL_ADMIN['full_name'],
            INITIAL_ADMIN['role']
        ))
    
    conn.commit()
    conn.close()

# Helper functions
def create_provider_code(user_id, provider_type, practice_name, specialization):
    """Create a unique provider code"""
    import random
    import string
    
    chars = config_class.PROVIDER_CODE_CHARS
    length = config_class.PROVIDER_CODE_LENGTH
    
    while True:
        code = ''.join(random.choices(chars, k=length))
        conn = sqlite3.connect(config_class.DATABASE_NAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO provider_codes (user_id, provider_code, provider_type, practice_name, specialization)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, code, provider_type, practice_name, specialization))
            conn.commit()
            conn.close()
            return code
        except sqlite3.IntegrityError:
            conn.close()
            continue

# Routes
@app.route('/')
def index():
    """Home page"""
    return render_template('index.html', analytics_config=ANALYTICS_CONFIG)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect(config_class.DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            if user[6]:  # is_paused
                flash('Your account has been suspended. Please contact support.', 'error')
                return redirect(url_for('login'))
                
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['full_name'] = user[4]
            session['role'] = user[5]
            
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html', analytics_config=ANALYTICS_CONFIG)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        role = request.form.get('role', 'patient')
        
        conn = sqlite3.connect(config_class.DATABASE_NAME)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if cursor.fetchone():
            flash('Username or email already exists', 'error')
            conn.close()
            return redirect(url_for('register'))
        
        # Create user
        password_hash = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, password_hash, full_name, role))
        
        user_id = cursor.lastrowid
        
        # Create provider code for dentists/specialists
        if role in ['dentist', 'specialist', 'dentist_admin', 'specialist_admin']:
            create_provider_code(user_id, role, f"{full_name} Practice", 'General')
        
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', analytics_config=ANALYTICS_CONFIG)

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(config_class.DATABASE_NAME)
    cursor = conn.cursor()
    
    # Get user stats
    cursor.execute('SELECT COUNT(*) FROM referrals WHERE user_id = ?', (session['user_id'],))
    total_referrals = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM referrals WHERE user_id = ? AND status = "pending"', (session['user_id'],))
    pending_referrals = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('dashboard.html', 
                         total_referrals=total_referrals,
                         pending_referrals=pending_referrals,
                         analytics_config=ANALYTICS_CONFIG)

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# API Routes
@app.route('/api/referrals', methods=['GET'])
def get_referrals():
    """Get user referrals"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = sqlite3.connect(config_class.DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM referrals WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],))
    referrals = cursor.fetchall()
    conn.close()




# ============================================================================
# STATIC PAGE ROUTES & NAVIGATION LINKS
# ============================================================================

# Authentication check for static files
@app.before_request
def check_static_auth():
    """Check authentication for protected static HTML files before processing request"""
    if request.endpoint == 'static' and request.path.startswith('/static/') and request.path.endswith('.html'):
        filename = request.path[8:]  # Remove '/static/' prefix
        
        # Remove .html extension for comparison with existing lists
        base_filename = filename
        if base_filename.endswith('.html'):
            base_filename = base_filename[:-5]
        
        # Define protected page categories (reuse from serve_static_page)
        admin_pages = [
            'admin', 'admin-1', 'admin-2', 'admin-3', 'admin-4', 'admin-users', 
            'admin-referrals', 'sapyyn-admin-panel', 'corrected_admin_html',
            'importDentists', 'importPatients', 'importSpecialist', 'users', 'roles'
        ]
        
        portal_pages = [
            'Dashboard', 'Patient Referral', 'Patient Referrral Admin portal',
            'Patient Referrral Admin', 'Referral History', 'Track Referral',
            'Medical Updates', 'portal-1', 'portal-referrals', 'portal-signup',
            'portal_integrations', 'portal_messaging', 'portal_settings',
            'patient', 'dentist', 'specialist', 'sapyyn-portal',
            'sapyyn_unified_portal', 'sapyyn_unified_portal (1)', 'sapyyn_unified_portal (2)',
            'updated_portal_rewards', 'appointments', 'forms', 'referrals',
            'referrals_page', 'referrals_page (1)', 'rewards', 'redeem list'
        ]
        
        # Check if this is a protected admin page
        if base_filename in admin_pages:
            if 'user_id' not in session or session.get('role') not in ['admin', 'dentist_admin', 'specialist_admin']:
                flash('Access denied. Administrator privileges required.', 'error')
                return redirect(url_for('login'))
        
        # Check if this is a protected portal page
        elif base_filename in portal_pages:
            if 'user_id' not in session:
                flash('Please log in to access portal pages.', 'error')
                return redirect(url_for('login'))


@app.route('/static/<path:filename>')
def serve_static_with_auth_check(filename):
    """Serve static files with authentication checks for portal/admin HTML files"""
    
    # Only apply authentication checks to HTML files
    if filename.endswith('.html'):
        from urllib.parse import unquote
        base_filename = unquote(filename)
        
        # Remove .html extension for comparison with existing lists
        if base_filename.endswith('.html'):
            base_filename = base_filename[:-5]
        
        # Define protected page categories (reuse from serve_static_page)
        admin_pages = [
            'admin', 'admin-1', 'admin-2', 'admin-3', 'admin-4', 'admin-users', 
            'admin-referrals', 'sapyyn-admin-panel', 'corrected_admin_html',
            'importDentists', 'importPatients', 'importSpecialist', 'users', 'roles'
        ]
        
        portal_pages = [
            'Dashboard', 'Patient Referral', 'Patient Referrral Admin portal',
            'Patient Referrral Admin', 'Referral History', 'Track Referral',
            'Medical Updates', 'portal-1', 'portal-referrals', 'portal-signup',
            'portal_integrations', 'portal_messaging', 'portal_settings',
            'patient', 'dentist', 'specialist', 'sapyyn-portal',
            'sapyyn_unified_portal', 'sapyyn_unified_portal (1)', 'sapyyn_unified_portal (2)',
            'updated_portal_rewards', 'appointments', 'forms', 'referrals',
            'referrals_page', 'referrals_page (1)', 'rewards', 'redeem list'
        ]
        
        # Check if this is a protected admin page
        if base_filename in admin_pages:
            if 'user_id' not in session or session.get('role') not in ['admin', 'dentist_admin', 'specialist_admin']:
                flash('Access denied. Administrator privileges required.', 'error')
                return redirect(url_for('login'))
        
        # Check if this is a protected portal page
        elif base_filename in portal_pages:
            if 'user_id' not in session:
                flash('Please log in to access portal pages.', 'error')
                return redirect(url_for('login'))
    
    # Serve the static file from the static directory
    return send_from_directory('static', filename)


@app.route('/static-pages/<path:filename>')
def serve_static_page(filename):
    """Serve static HTML pages with authentication checks"""
    from urllib.parse import unquote
    filename = unquote(filename)
    if filename.endswith('.html'):
        filename = filename[:-5]
    public_pages = [
        'about_page', 'pricing_page', 'resources_page', 'contact', 'contact-us',
        'blog', 'blog-article', 'case studies', 'educational content',

        'training and support', 'how to guide', 'short video', 'newsletter',
        'surgical-instruction', 'surgical-instruction-page', 'pre op consultation',
        'co_marketing', 'getstarted_page', 'resources'
    ]
    admin_pages = [
        'admin', 'admin-1', 'admin-2', 'admin-3', 'admin-4', 'admin-users', 
        'admin-referrals', 'sapyyn-admin-panel', 'corrected_admin_html',
        'importDentists', 'importPatients', 'importSpecialist', 'users', 'roles'
    ]
    portal_pages = [
        'Dashboard', 'Patient Referral', 'Patient Referrral Admin portal',
        'Patient Referrral Admin', 'Referral History', 'Track Referral',
        'Medical Updates', 'portal-1', 'portal-referrals', 'portal-signup',
        'portal_integrations', 'portal_messaging', 'portal_settings',
        'patient', 'dentist', 'specialist', 'sapyyn-portal',
        'sapyyn_unified_portal', 'sapyyn_unified_portal (1)', 'sapyyn_unified_portal (2)',
        'updated_portal_rewards', 'appointments', 'forms', 'referrals',
        'referrals_page', 'referrals_page (1)', 'rewards', 'redeem list'
    ]
    static_file_path = os.path.join('static', f'{filename}.html')
    if not os.path.exists(static_file_path):
        return render_template('404.html'), 404
    if filename in admin_pages:
        if 'user_id' not in session or session.get('role') not in ['admin', 'dentist_admin', 'specialist_admin']:
            flash('Access denied. Administrator privileges required.', 'error')
            return redirect(url_for('login'))
    elif filename in portal_pages:
        if 'user_id' not in session:
            flash('Please log in to access portal pages.', 'error')
            return redirect(url_for('login'))
    return send_from_directory('static', f'{filename}.html')

@app.route('/about')
def about():
    """About page route"""
    return redirect(url_for('serve_static_page', filename='about_page'))

@app.route('/resources')
def resources():
    """Resources page route"""
    return redirect(url_for('serve_static_page', filename='resources_page'))

@app.route('/contact')
def contact():
    """Contact page route"""
    return redirect(url_for('serve_static_page', filename='contact'))

@app.route('/blog')
def blog():
    """Blog page route"""
    return redirect(url_for('serve_static_page', filename='blog'))

@app.route('/training')
def training():
    """Training and support page route"""
    return redirect(url_for('serve_static_page', filename='training and support'))

@app.route('/surgical-instructions')
def surgical_instructions():
    """Surgical instructions page route"""
    return redirect(url_for('serve_static_page', filename='surgical-instruction'))

@app.route('/admin-panel')
def admin_panel():
    """Admin panel page route"""
    if 'user_id' not in session or session.get('role') not in ['admin', 'dentist_admin', 'specialist_admin']:
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('login'))
    return redirect(url_for('serve_static_page', filename='admin'))

@app.route('/referral-history')
def referral_history():
    """Referral history page route"""
    if 'user_id' not in session:
        flash('Please log in to view referral history.', 'error')
        return redirect(url_for('login'))
    return redirect(url_for('serve_static_page', filename='Referral History'))

@app.route('/track-referral')
def track_referral_page():
    """Track referral page route"""
    if 'user_id' not in session:
        flash('Please log in to track referrals.', 'error')
        return redirect(url_for('login'))
    return redirect(url_for('serve_static_page', filename='Track Referral'))

@app.route('/appointments')
def appointments():
    """Appointments page route"""
    if 'user_id' not in session:
        flash('Please log in to view appointments.', 'error')
        return redirect(url_for('login'))
    return redirect(url_for('serve_static_page', filename='appointments'))

@app.route('/messages')
def messages():
    """Messages page route"""
    if 'user_id' not in session:
        flash('Please log in to view messages.', 'error')
        return redirect(url_for('login'))
    return render_template('messages.html')

@app.route('/my-referrals')
def my_referrals():
    """My Referrals page route - alias for referral history"""
    if 'user_id' not in session:
        flash('Please log in to view your referrals.', 'error')
        return redirect(url_for('login'))
    return redirect(url_for('referral_history'))

@app.route('/portal-dashboard')
def portal_dashboard():
    """Portal dashboard route based on user role"""
    if 'user_id' not in session:
        flash('Please log in to access the portal.', 'error')
        return redirect(url_for('login'))
    role = session.get('role', 'patient')
    if role in ['admin', 'dentist_admin', 'specialist_admin']:
        return redirect(url_for('serve_static_page', filename='admin'))
    elif role in ['dentist']:
        return redirect(url_for('serve_static_page', filename='dentist'))
    elif role in ['specialist']:
        return redirect(url_for('serve_static_page', filename='specialist'))
    else:
        return redirect(url_for('serve_static_page', filename='patient'))

# Additional navigation routes from copilot branch not covered above
@app.route('/original')
def original_page():
    """Serve the original static index.html page for comparison"""
    return send_from_directory('.', 'index.html')


@app.route('/referrals')
def referrals():
    """My Referrals page with list and detail view"""
    if 'user_id' not in session:
        flash('Please log in to view your referrals.', 'error')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    # Build base query - get referrals based on user role
    user_role = session.get('role', 'patient')
    
    if user_role in ['dentist', 'dentist_admin']:
        # Dentists see referrals they created
        base_query = '''
            SELECT r.*, COUNT(d.id) as document_count,
                   u.full_name as target_provider_name
            FROM referrals r
            LEFT JOIN documents d ON r.id = d.referral_id
            LEFT JOIN users u ON u.full_name = r.target_doctor
            WHERE r.user_id = ?
        '''
        query_params = [session['user_id']]
    elif user_role in ['specialist', 'specialist_admin']:
        # Specialists see referrals sent to them + ones they created
        base_query = '''
            SELECT r.*, COUNT(d.id) as document_count,
                   CASE WHEN r.user_id = ? THEN r.target_doctor ELSE u.full_name END as target_provider_name,
                   CASE WHEN r.user_id = ? THEN 'sent' ELSE 'received' END as referral_direction
            FROM referrals r
            LEFT JOIN documents d ON r.id = d.referral_id
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.user_id = ? OR r.target_doctor = ?
        '''
        user_full_name = session.get('full_name', '')
        query_params = [session['user_id'], session['user_id'], session['user_id'], user_full_name]
    else:
        # Patients see referrals where they are the patient
        base_query = '''
            SELECT r.*, COUNT(d.id) as document_count,
                   r.target_doctor as target_provider_name,
                   u.full_name as referring_provider_name
            FROM referrals r
            LEFT JOIN documents d ON r.id = d.referral_id
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.patient_name LIKE ? OR r.user_id = ?
        '''
        query_params = [f'%{session.get("full_name", "")}%', session['user_id']]
    
    # Add status filter
    if status_filter != 'all':
        base_query += ' AND r.status = ?'
        query_params.append(status_filter)
    
    # Add search filter
    if search_query:
        base_query += ''' AND (r.patient_name LIKE ? OR r.referring_doctor LIKE ? 
                             OR r.target_doctor LIKE ? OR r.medical_condition LIKE ?)'''
        search_pattern = f'%{search_query}%'
        query_params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
    
    # Add GROUP BY and ORDER BY
    base_query += f''' GROUP BY r.id ORDER BY r.{sort_by} {sort_order.upper()}'''
    
    cursor.execute(base_query, query_params)
    referrals = cursor.fetchall()
    
    # Get summary statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
            SUM(CASE WHEN case_status = 'case_accepted' THEN 1 ELSE 0 END) as accepted
        FROM referrals 
        WHERE {} = ?
    '''.format('user_id' if user_role in ['dentist', 'specialist'] else 'patient_name LIKE'), 
    [session['user_id']] if user_role in ['dentist', 'specialist'] else [f'%{session.get("full_name", "")}%'])
    
    stats = cursor.fetchone()
    
    # Get available statuses for filter dropdown
    cursor.execute('SELECT DISTINCT status FROM referrals WHERE user_id = ? ORDER BY status', (session['user_id'],))
    available_statuses = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('referrals.html', 
                         referrals=referrals,
                         stats=stats,
                         available_statuses=available_statuses,
                         current_filter=status_filter,
                         current_search=search_query,
                         current_sort=sort_by,
                         current_order=sort_order,
                         user_role=user_role)


@app.route('/surgicalInstruction')
def surgical_instruction():
    """Surgical instruction page (legacy route)"""
    return send_from_directory('static', 'surgical-instruction-page.html')

@app.route('/casestudies')
def case_studies():
    """Case studies page"""
    return render_template('case_studies.html')

@app.route('/tutorials')
def tutorials():
    """Tutorials page"""
    return render_template('tutorials.html')

@app.route('/howtoguides')
def how_to_guides():
    """How-to guides page"""
    return render_template('how_to_guides.html')

@app.route('/loyaltyrewards')
def loyalty_rewards():
    """Loyalty rewards page - redirect to rewards dashboard"""

    return redirect(url_for('rewards_dashboard'))

@app.route('/hipaa')
def hipaa():
    """HIPAA compliance page"""
    return render_template('hipaa.html')

@app.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')

@app.route('/faq')
def faq():
    """FAQ page"""
    return render_template('faq.html')

@app.route('/connectproviders')
def connect_providers():
    """Connect providers page - redirect to appropriate portal"""
    if 'user_id' in session:
        user_role = session.get('role', 'patient')
        if user_role == 'dentist':

            return redirect(url_for('dentist_portal'))
        elif user_role == 'specialist':
            return redirect(url_for('specialist_portal'))
        else:
            return redirect(url_for('patient_portal'))
    return redirect(url_for('login'))

@app.route('/sendpatientdocuments')
def send_patient_documents():
    """Send patient documents page - redirect to upload"""
    if 'user_id' in session:
        return redirect(url_for('upload_file'))
    return redirect(url_for('login'))


@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Submit user feedback for UX optimization"""
    try:
        feedback_data = request.get_json()
        
        if not feedback_data:
            return jsonify({'error': 'No feedback data provided'}), 400
        
        # Add server-side data
        feedback_data['server_timestamp'] = datetime.now().isoformat()
        feedback_data['ip_address'] = request.remote_addr
        feedback_data['user_id'] = session.get('user_id')
        feedback_data['user_role'] = session.get('role')
        
        # Save to database
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        # Create feedback table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                visit_purpose TEXT,
                ease_of_use TEXT,
                confusion_feedback TEXT,
                nps_score INTEGER,
                additional_comments TEXT,
                contact_email TEXT,
                page_url TEXT,
                page_title TEXT,
                timestamp TEXT,
                server_timestamp TEXT,
                ip_address TEXT,
                user_agent TEXT,
                screen_resolution TEXT,
                session_duration INTEGER,
                user_role TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert feedback
        cursor.execute('''
            INSERT INTO user_feedback (
                user_id, visit_purpose, ease_of_use, confusion_feedback, nps_score,
                additional_comments, contact_email, page_url, page_title, timestamp,
                server_timestamp, ip_address, user_agent, screen_resolution,
                session_duration, user_role
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            feedback_data.get('user_id'),
            feedback_data.get('visit_purpose'),
            feedback_data.get('ease_of_use'),
            feedback_data.get('confusion_feedback'),
            feedback_data.get('nps_score'),
            feedback_data.get('additional_comments'),
            feedback_data.get('contact_email'),
            feedback_data.get('page_url'),
            feedback_data.get('page_title'),
            feedback_data.get('timestamp'),
            feedback_data.get('server_timestamp'),
            feedback_data.get('ip_address'),
            feedback_data.get('user_agent'),
            feedback_data.get('screen_resolution'),
            feedback_data.get('session_duration'),
            feedback_data.get('user_role')
        ))
        
        conn.commit()
        conn.close()
        
        # Track feedback submission in analytics
        if ANALYTICS_CONFIG['ENABLE_ANALYTICS']:
            # You could send this to external analytics services here
            pass
        
        return jsonify({'success': True, 'message': 'Feedback submitted successfully'})
        
    except Exception as e:
        app.logger.error(f'Error submitting feedback: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/newsletter_subscribe', methods=['POST'])
def newsletter_subscribe():
    """Handle newsletter subscription"""
    try:
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        user_type = request.form.get('userType', '')
        
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400
        
        # Store newsletter subscription (you can add to database if needed)
        # For now, just return success
        flash(f'Thank you for subscribing to our newsletter, {name}!', 'success')
        return jsonify({'success': True, 'message': 'Subscription successful'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Subscription failed'}), 500

@app.route('/api/analytics/stats')
def analytics_stats():
    """Get analytics statistics for admin dashboard"""
    if 'user_id' not in session or session.get('role') not in ['admin', 'dentist_admin', 'specialist_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        days = request.args.get('days', 30, type=int)
        
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        # Get feedback stats by purpose
        cursor.execute('''
            SELECT 
                visit_purpose,
                COUNT(*) as purpose_count
            FROM user_feedback 
            WHERE created_at >= date('now', '-{} days')
            GROUP BY visit_purpose
            ORDER BY purpose_count DESC
        '''.format(days))
        feedback_stats = cursor.fetchall()
        
        # Get overall stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_feedback,
                AVG(CASE WHEN nps_score IS NOT NULL THEN nps_score END) as avg_nps,
                AVG(CASE 
                    WHEN ease_of_use = 'very_easy' THEN 5
                    WHEN ease_of_use = 'easy' THEN 4
                    WHEN ease_of_use = 'neutral' THEN 3
                    WHEN ease_of_use = 'difficult' THEN 2
                    WHEN ease_of_use = 'very_difficult' THEN 1
                    ELSE NULL
                END) as avg_ease_score,
                COUNT(DISTINCT CASE WHEN user_id IS NOT NULL THEN user_id 
                     ELSE ip_address END) as unique_users
            FROM user_feedback 
            WHERE created_at >= date('now', '-{} days')
        '''.format(days))
        user_stats = cursor.fetchone()
        
        # Get recent feedback for table
        cursor.execute('''
            SELECT id, visit_purpose, ease_of_use, nps_score, confusion_feedback, 
                   additional_comments, page_url, created_at, user_role
            FROM user_feedback 
            WHERE created_at >= date('now', '-{} days')
            ORDER BY created_at DESC
            LIMIT 20
        '''.format(days))
        recent_feedback_raw = cursor.fetchall()
        
        # Convert recent feedback to dictionaries
        columns = [description[0] for description in cursor.description]
        recent_feedback = [dict(zip(columns, row)) for row in recent_feedback_raw]
        
        # Get ease of use distribution
        cursor.execute('''
            SELECT ease_of_use, COUNT(*) as count
            FROM user_feedback 
            WHERE created_at >= date('now', '-{} days')
            AND ease_of_use IS NOT NULL
            GROUP BY ease_of_use
        '''.format(days))
        ease_distribution = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'feedback_stats': feedback_stats,
            'user_stats': user_stats,
            'recent_feedback': recent_feedback,
            'ease_distribution': ease_distribution,
            'period': f'last_{days}_days'
        })
        
    except Exception as e:
        app.logger.error(f'Error getting analytics stats: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/admin/analytics')
def analytics_dashboard():
    """Analytics dashboard for administrators"""
    if 'user_id' not in session or session.get('role') not in ['admin', 'dentist_admin', 'specialist_admin']:
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('login'))
    
    return render_template('analytics_dashboard.html')

@app.route('/api/feedback/<int:feedback_id>')
def get_feedback_detail(feedback_id):
    """Get detailed feedback information"""
    if 'user_id' not in session or session.get('role') not in ['admin', 'dentist_admin', 'specialist_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM user_feedback WHERE id = ?
        ''', (feedback_id,))
        
        feedback = cursor.fetchone()
        conn.close()
        
        if not feedback:
            return jsonify({'error': 'Feedback not found'}), 404
        
        # Convert to dictionary
        columns = [description[0] for description in cursor.description]
        feedback_dict = dict(zip(columns, feedback))
        
        return jsonify(feedback_dict)
        
    except Exception as e:
        app.logger.error(f'Error getting feedback detail: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/feedback/export')
def export_feedback():
    """Export feedback data as CSV"""
    if 'user_id' not in session or session.get('role') not in ['admin', 'dentist_admin', 'specialist_admin']:
        return jsonify({'error': 'Unauthorized'}), 403

    
    return jsonify([{
        'id': r[0],
        'referral_id': r[2],
        'patient_name': r[3],
        'status': r[9],
        'created_at': r[15]
    } for r in referrals])

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Render custom 404 page"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """Render custom 500 page"""
    return render_template('500.html'), 500

# Register blueprints
app.register_blueprint(nocode_api, url_prefix='/api/nocode')
app.register_blueprint(nocodebackend_api, url_prefix='/api/nocodebackend')
app.register_blueprint(promotions, url_prefix='/promotions')
app.register_blueprint(admin_promotions, url_prefix='/admin/promotions')

# ============================================================================
# NEW REFERRALS MODULE API ENDPOINTS
# ============================================================================

@app.route('/api/referrals', methods=['GET'])
def get_referrals_list():
    """Get list of referrals with filtering and permissions"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        user_id = session['user_id']
        user_role = session.get('role', 'patient')
        status_filter = request.args.get('status', 'all')  # all, pending, completed
        
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        # Build query based on user role and permissions
        if user_role == 'admin':
            # Admin sees all referrals
            base_query = '''
                SELECT r.*, 
                       p.full_name as patient_name_user,
                       d.full_name as dentist_name_user
                FROM referrals r
                LEFT JOIN users p ON r.patient_id = p.id
                LEFT JOIN users d ON r.dentist_id = d.id
            '''
            query_params = []
        elif user_role in ['dentist', 'dentist_admin', 'specialist', 'specialist_admin']:
            # Dentists see referrals they initiated
            base_query = '''
                SELECT r.*,
                       p.full_name as patient_name_user,
                       d.full_name as dentist_name_user
                FROM referrals r
                LEFT JOIN users p ON r.patient_id = p.id
                LEFT JOIN users d ON r.dentist_id = d.id
                WHERE r.dentist_id = ? OR r.user_id = ?
            '''
            query_params = [user_id, user_id]
        else:
            # Patients see their own referrals
            base_query = '''
                SELECT r.*,
                       p.full_name as patient_name_user,
                       d.full_name as dentist_name_user
                FROM referrals r
                LEFT JOIN users p ON r.patient_id = p.id
                LEFT JOIN users d ON r.dentist_id = d.id
                WHERE r.patient_id = ? OR r.user_id = ?
            '''
            query_params = [user_id, user_id]
        
        # Add status filter
        if status_filter != 'all':
            if status_filter == 'pending':
                base_query += ' AND (r.status = "pending" OR r.status = "emergency_pending" OR r.status = "consultation_pending")'
            elif status_filter == 'completed':
                base_query += ' AND (r.status = "completed" OR r.status = "treatment_completed")'
            else:
                base_query += ' AND r.status = ?'
                query_params.append(status_filter)
        
        base_query += ' ORDER BY r.created_at DESC'
        
        cursor.execute(base_query, query_params)
        referrals = cursor.fetchall()
        
        # Convert to list of dictionaries
        columns = [description[0] for description in cursor.description]
        referrals_list = []
        for referral in referrals:
            referral_dict = dict(zip(columns, referral))
            referrals_list.append(referral_dict)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'referrals': referrals_list,
            'count': len(referrals_list),
            'filter': status_filter
        })
        
    except Exception as e:
        app.logger.error(f'Error getting referrals list: {str(e)}')
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/referrals/<int:referral_id>', methods=['GET'])
def get_referral_detail(referral_id):
    """Get detailed information for a specific referral"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        user_id = session['user_id']
        user_role = session.get('role', 'patient')
        
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        # Get referral with permission check
        if user_role == 'admin':
            # Admin can see any referral
            cursor.execute('''
                SELECT r.*,
                       p.full_name as patient_name_user,
                       d.full_name as dentist_name_user
                FROM referrals r
                LEFT JOIN users p ON r.patient_id = p.id
                LEFT JOIN users d ON r.dentist_id = d.id
                WHERE r.id = ?
            ''', (referral_id,))
        elif user_role in ['dentist', 'dentist_admin', 'specialist', 'specialist_admin']:
            # Dentists can see referrals they initiated
            cursor.execute('''
                SELECT r.*,
                       p.full_name as patient_name_user,
                       d.full_name as dentist_name_user
                FROM referrals r
                LEFT JOIN users p ON r.patient_id = p.id
                LEFT JOIN users d ON r.dentist_id = d.id
                WHERE r.id = ? AND (r.dentist_id = ? OR r.user_id = ?)
            ''', (referral_id, user_id, user_id))
        else:
            # Patients can see their own referrals
            cursor.execute('''
                SELECT r.*,
                       p.full_name as patient_name_user,
                       d.full_name as dentist_name_user
                FROM referrals r
                LEFT JOIN users p ON r.patient_id = p.id
                LEFT JOIN users d ON r.dentist_id = d.id
                WHERE r.id = ? AND (r.patient_id = ? OR r.user_id = ?)
            ''', (referral_id, user_id, user_id))
        
        referral = cursor.fetchone()
        
        if not referral:
            conn.close()
            return jsonify({'success': False, 'error': 'Referral not found or access denied'}), 404
        
        # Convert to dictionary
        columns = [description[0] for description in cursor.description]
        referral_dict = dict(zip(columns, referral))
        
        # Get related documents
        cursor.execute('''
            SELECT id, file_type, file_name, file_size, upload_date
            FROM documents
            WHERE referral_id = ?
            ORDER BY upload_date DESC
        ''', (referral_id,))
        documents = cursor.fetchall()
        
        # Convert documents to list of dictionaries
        doc_columns = [description[0] for description in cursor.description]
        documents_list = [dict(zip(doc_columns, doc)) for doc in documents]
        
        referral_dict['documents'] = documents_list
        
        conn.close()
        
        return jsonify({
            'success': True,
            'referral': referral_dict
        })
        
    except Exception as e:
        app.logger.error(f'Error getting referral detail: {str(e)}')
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/referrals', methods=['POST'])
def create_referral():
    """Create a new referral"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        user_id = session['user_id']
        user_role = session.get('role', 'patient')
        
        # Extract required fields
        patient_id = data.get('patient_id')
        dentist_id = data.get('dentist_id')
        notes = data.get('notes', '')
        status = data.get('status', 'pending')
        
        # Additional fields for compatibility with existing system
        patient_name = data.get('patient_name', '')
        referring_doctor = data.get('referring_doctor', session.get('full_name', ''))
        target_doctor = data.get('target_doctor', '')
        medical_condition = data.get('medical_condition', '')
        urgency_level = data.get('urgency_level', 'normal')
        
        # Validation
        if not all([patient_id, dentist_id]):
            return jsonify({'success': False, 'error': 'patient_id and dentist_id are required'}), 400
        
        # Permission check - only dentists/admin can create referrals
        if user_role not in ['dentist', 'dentist_admin', 'specialist', 'specialist_admin', 'admin']:
            return jsonify({'success': False, 'error': 'Insufficient permissions to create referrals'}), 403
        
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        # Verify patient and dentist exist
        cursor.execute('SELECT full_name FROM users WHERE id = ?', (patient_id,))
        patient = cursor.fetchone()
        if not patient:
            conn.close()
            return jsonify({'success': False, 'error': 'Patient not found'}), 404
        
        cursor.execute('SELECT full_name FROM users WHERE id = ?', (dentist_id,))
        dentist = cursor.fetchone()
        if not dentist:
            conn.close()
            return jsonify({'success': False, 'error': 'Dentist not found'}), 404
        
        # Generate referral ID and QR code
        referral_id = str(uuid.uuid4())[:8].upper()
        qr_data = f"Referral ID: {referral_id}\nPatient: {patient[0]}\nDentist: {dentist[0]}"
        qr_code = generate_qr_code(qr_data)
        
        # Use patient/dentist names if not provided
        if not patient_name:
            patient_name = patient[0]
        if not target_doctor:
            target_doctor = dentist[0]
        
        # Create referral
        cursor.execute('''
            INSERT INTO referrals (
                user_id, referral_id, patient_id, dentist_id, patient_name, 
                referring_doctor, target_doctor, medical_condition, urgency_level,
                status, notes, qr_code, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, referral_id, patient_id, dentist_id, patient_name,
            referring_doctor, target_doctor, medical_condition, urgency_level,
            status, notes, qr_code, datetime.now(), datetime.now()
        ))
        
        new_referral_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'referral_id': new_referral_id,
            'referral_uuid': referral_id,
            'message': 'Referral created successfully'
        })
        
    except Exception as e:
        app.logger.error(f'Error creating referral: {str(e)}')
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/referrals/<int:referral_id>', methods=['PATCH'])
def update_referral_status():
    """Update referral status (dentist or admin only)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        user_id = session['user_id']
        user_role = session.get('role', 'patient')
        
        # Only dentists and admins can update status
        if user_role not in ['dentist', 'dentist_admin', 'specialist', 'specialist_admin', 'admin']:
            return jsonify({'success': False, 'error': 'Insufficient permissions to update referral status'}), 403
        
        data = request.get_json()
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        if not new_status:
            return jsonify({'success': False, 'error': 'Status is required'}), 400
        
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        # Check if referral exists and user has permission to update it
        if user_role == 'admin':
            cursor.execute('SELECT id, status, dentist_id FROM referrals WHERE id = ?', (referral_id,))
        else:
            cursor.execute('''
                SELECT id, status, dentist_id FROM referrals 
                WHERE id = ? AND (dentist_id = ? OR user_id = ?)
            ''', (referral_id, user_id, user_id))
        
        referral = cursor.fetchone()
        
        if not referral:
            conn.close()
            return jsonify({'success': False, 'error': 'Referral not found or access denied'}), 404
        
        old_status = referral[1]
        
        # Update referral status
        update_fields = ['status = ?', 'updated_at = ?']
        update_values = [new_status, datetime.now()]
        
        # Add notes to existing notes if provided
        if notes:
            cursor.execute('SELECT notes FROM referrals WHERE id = ?', (referral_id,))
            existing_notes = cursor.fetchone()[0] or ''
            new_notes = f"{existing_notes}\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Status updated to {new_status}: {notes}".strip()
            update_fields.append('notes = ?')
            update_values.append(new_notes)
        
        update_values.append(referral_id)
        
        cursor.execute(f'''
            UPDATE referrals 
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', update_values)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Referral status updated from {old_status} to {new_status}',
            'old_status': old_status,
            'new_status': new_status
        })
        
    except Exception as e:
        app.logger.error(f'Error updating referral status: {str(e)}')
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/my-referrals')
def my_referrals_page():
    """My Referrals page with filters"""
    if 'user_id' not in session:
        flash('Please log in to view your referrals.', 'error')
        return redirect(url_for('login'))
    
    return render_template('my_referrals.html', user_role=session.get('role'))

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run application
    app.run(debug=config_class.DEBUG, host='0.0.0.0', port=5000)
