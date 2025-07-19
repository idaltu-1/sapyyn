
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
    key_func=get_remote_address,
    app=app,
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
    'ENVIRONMENT': os.environ.get('FLASK_ENV', 'development')
}

# Configuration
UPLOAD_FOLDER = config_class.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = config_class.ALLOWED_EXTENSIONS

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

    # Referral campaigns table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referral_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            advocate_role TEXT,
            reward_type TEXT,
            reward_value DECIMAL(10,2),
            reward_trigger TEXT,
            max_referrals_per_advocate INTEGER,
            fraud_threshold DECIMAL(5,2),
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Referral codes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referral_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            advocate_id INTEGER NOT NULL,
            code TEXT UNIQUE NOT NULL,
            link_slug TEXT UNIQUE,
            qr_svg TEXT,
            usage_count INTEGER DEFAULT 0,
            reward_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES referral_campaigns (id),
            FOREIGN KEY (advocate_id) REFERENCES users (id)
        )
    ''')

    # Referral events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referral_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code_id INTEGER NOT NULL,
            referred_patient_id INTEGER,
            status TEXT NOT NULL CHECK (status IN ('SIGNED_UP', 'CONVERTED', 'REWARDED')),
            ip_addr TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (code_id) REFERENCES referral_codes (id),
            FOREIGN KEY (referred_patient_id) REFERENCES users (id)
        )
    ''')

    # Rewards table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            advocate_id INTEGER NOT NULL,
            campaign_id INTEGER NOT NULL,
            event_id INTEGER,
            reward_type TEXT NOT NULL CHECK (reward_type IN ('GIFT_CARD', 'CREDIT', 'SWAG')),
            amount DECIMAL(10,2),
            issued_at TIMESTAMP,
            fulfilled_at TIMESTAMP,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (advocate_id) REFERENCES users (id),
            FOREIGN KEY (campaign_id) REFERENCES referral_campaigns (id),
            FOREIGN KEY (event_id) REFERENCES referral_events (id)
        )
    ''')

    conn.commit()
    conn.close()
"""
Sapyyn Patient Referral System - Main Application
"""

from flask import Flask, render_template, send_from_directory, redirect, url_for, request, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from routes.nocode_routes import nocode_api
from controllers.nocodebackend_controller import nocodebackend_api
from controllers.promotion_controller import promotions
from controllers.admin_promotion_controller import admin_promotions
import os
import sqlite3
import uuid
import qrcode
import base64
from io import BytesIO
from datetime import datetime, timedelta
import stripe

app = Flask(__name__)
app.secret_key = 'sapyyn-patient-referral-system-2025'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Stripe configuration
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_...')  # Replace with your Stripe secret key
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_...')  # Replace with your Stripe publishable key

# Analytics configuration
ANALYTICS_CONFIG = {
    'GA4_MEASUREMENT_ID': os.environ.get('GA4_MEASUREMENT_ID', 'G-XXXXXXXXXX'),
    'GTM_CONTAINER_ID': os.environ.get('GTM_CONTAINER_ID', 'GTM-XXXXXXX'),
    'HOTJAR_SITE_ID': os.environ.get('HOTJAR_SITE_ID', '3842847'),
    'ENABLE_ANALYTICS': os.environ.get('ENABLE_ANALYTICS', 'true').lower() == 'true',
    'ENVIRONMENT': os.environ.get('FLASK_ENV', 'development')
}

# Configuration
UPLOAD_FOLDER = 'patient-referral'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database initialization
def init_db_dup2():
    """Initialize the SQLite database"""
    conn = sqlite3.connect('sapyyn.db')
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
    
    # Continue with the rest of the database setup...
    conn.commit()
    conn.close()

# Flask app initialization
app = Flask(__name__)
app.secret_key = 'sapyyn-patient-referral-system-2025'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Stripe configuration
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_...')  # Replace with your Stripe secret key
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_...')  # Replace with your Stripe publishable key

# Analytics configuration
ANALYTICS_CONFIG = {
    'GA4_MEASUREMENT_ID': os.environ.get('GA4_MEASUREMENT_ID', 'G-XXXXXXXXXX'),
    'GTM_CONTAINER_ID': os.environ.get('GTM_CONTAINER_ID', 'GTM-XXXXXXX'),
    'HOTJAR_SITE_ID': os.environ.get('HOTJAR_SITE_ID', '3842847'),
    'ENABLE_ANALYTICS': os.environ.get('ENABLE_ANALYTICS', 'true').lower() == 'true',
    'ENVIRONMENT': os.environ.get('FLASK_ENV', 'development')
}

# Configuration
UPLOAD_FOLDER = 'patient-referral'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database initialization
def init_db_dup3():
    """Initialize the SQLite database"""
    conn = sqlite3.connect('sapyyn.db')
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
    
    # Device Fingerprints table for deduplication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fingerprint_hash TEXT UNIQUE NOT NULL,
            user_agent TEXT,
            screen_resolution TEXT,
            timezone TEXT,
            language TEXT,
            plugins TEXT,
            canvas_fingerprint TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_count INTEGER DEFAULT 0
        )
    ''')
    
    # Duplicate Detection Log
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS duplicate_detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            detection_type TEXT NOT NULL,
            original_user_id INTEGER,
            duplicate_user_id INTEGER,
            matching_field TEXT,
            matching_value TEXT,
            action_taken TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (original_user_id) REFERENCES users (id),
            FOREIGN KEY (duplicate_user_id) REFERENCES users (id)
        )
    ''')
    
    # Add fraud score to users table if it doesn't exist
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN fraud_score DECIMAL(5,2) DEFAULT 0.0')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN is_paused BOOLEAN DEFAULT FALSE')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN device_fingerprint TEXT')
    except sqlite3.OperationalError:
        pass

    # ---------------------------------------------------------------------------
    # Appointments table
    #
    # Create a dedicated table to store appointment bookings between patients and
    # providers. This table references the users table twice (once for the
    # patient and once for the provider) and stores the scheduled datetime,
    # optional appointment type, notes, status and timestamps. If the table
    # already exists this statement will be ignored. Keeping this DDL close to
    # other schema alterations ensures the database is ready before any routes
    # interact with appointments.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            provider_id INTEGER NOT NULL,
            appointment_date_time TIMESTAMP NOT NULL,
            appointment_type TEXT,
            notes TEXT,
            status TEXT DEFAULT 'scheduled',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (provider_id) REFERENCES users (id)
        )
    ''')

    # ---------------------------------------------------------------------------
    # Promotions table for campaign management
    #
    # Create a table to store promotional campaigns that dental practices can run
    # to attract referrals. Includes campaign details, image uploads, date ranges,
    # status controls, and real-time tracking of impressions and clicks.
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

    # Promotion Stats table for real-time tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promotion_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            promotion_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            referrer TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (promotion_id) REFERENCES promotions (id)
        )
    ''')

    # -----------------------------------------------------------------------
    # Seed a default super administrator account if one does not already exist.
    # This ensures the system has at least one user with full privileges after
    # database initialization.  The credentials are pulled from the user’s
    # configuration: email wgray@stloralsurgery.com and a strong password.  If
    # the email already exists, no action is taken.
    cursor.execute("SELECT id FROM users WHERE email = ?", ("wgray@stloralsurgery.com",))
    if cursor.fetchone() is None:
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash('P@$sW0rD54321$')
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, role, created_at, is_verified)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
        ''', (
            'wgray@stloralsurgery.com',
            'wgray@stloralsurgery.com',
            password_hash,
            'Super Admin',
            'admin'
        ))

    # Referral campaigns table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referral_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            advocate_role TEXT,
            reward_type TEXT,
            reward_value DECIMAL(10,2),
            reward_trigger TEXT,
            max_referrals_per_advocate INTEGER,
            fraud_threshold DECIMAL(5,2),
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Referral codes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referral_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            advocate_id INTEGER NOT NULL,
            code TEXT UNIQUE NOT NULL,
            link_slug TEXT UNIQUE,
            qr_svg TEXT,
            usage_count INTEGER DEFAULT 0,
            reward_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES referral_campaigns (id),
            FOREIGN KEY (advocate_id) REFERENCES users (id)
        )
    ''')

    # Referral events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referral_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code_id INTEGER NOT NULL,
            referred_patient_id INTEGER,
            status TEXT NOT NULL CHECK (status IN ('SIGNED_UP', 'CONVERTED', 'REWARDED')),
            ip_addr TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (code_id) REFERENCES referral_codes (id),
            FOREIGN KEY (referred_patient_id) REFERENCES users (id)
        )
    ''')

    # Rewards table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            advocate_id INTEGER NOT NULL,
            campaign_id INTEGER NOT NULL,
            event_id INTEGER,
            reward_type TEXT NOT NULL CHECK (reward_type IN ('GIFT_CARD', 'CREDIT', 'SWAG')),
            amount DECIMAL(10,2),
            issued_at TIMESTAMP,
            fulfilled_at TIMESTAMP,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (advocate_id) REFERENCES users (id),
            FOREIGN KEY (campaign_id) REFERENCES referral_campaigns (id),
            FOREIGN KEY (event_id) REFERENCES referral_events (id)
        )
    ''')

    conn.commit()
    conn.close()

def calculate_fraud_score(user_id, ip_address, email, device_fingerprint):
    """Calculate fraud score based on various factors"""
    score = 0.0
    reasons = []
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Check for duplicate emails
    cursor.execute('SELECT COUNT(*) FROM users WHERE email = ? AND id != ?', (email, user_id))
    email_count = cursor.fetchone()[0]
    if email_count > 0:
        score += 30.0
        reasons.append(f"Duplicate email found ({email_count} matches)")
    
    # Check for duplicate IP addresses
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM compliance_audit_trail WHERE ip_address = ?', (ip_address,))
    ip_count = cursor.fetchone()[0]
    if ip_count > 5:
        score += 20.0
        reasons.append(f"High IP usage ({ip_count} users)")
    elif ip_count > 2:
        score += 10.0
        reasons.append(f"Moderate IP usage ({ip_count} users)")
    
    # Check for duplicate device fingerprints
    if device_fingerprint:
        cursor.execute('SELECT user_count FROM device_fingerprints WHERE fingerprint_hash = ?', (device_fingerprint,))
        fp_result = cursor.fetchone()
        if fp_result and fp_result[0] > 1:
            score += 25.0
            reasons.append(f"Device fingerprint shared ({fp_result[0]} users)")
    
    # Check registration patterns (multiple registrations in short time from same IP)
    cursor.execute('''
        SELECT COUNT(*) FROM compliance_audit_trail 
        WHERE ip_address = ? AND action_type = 'user_registration' 
        AND timestamp > datetime('now', '-1 hour')
    ''', (ip_address,))
    recent_registrations = cursor.fetchone()[0]
    if recent_registrations > 3:
        score += 40.0
        reasons.append(f"Rapid registrations from IP ({recent_registrations} in last hour)")
    elif recent_registrations > 1:
        score += 15.0
        reasons.append(f"Multiple recent registrations ({recent_registrations} in last hour)")
    
    conn.close()
    
    # Determine risk level
    if score >= 50.0:
        risk_level = 'high'
    elif score >= 25.0:
        risk_level = 'medium'
    else:
        risk_level = 'low'
    
    return score, risk_level, reasons

def update_fraud_score(user_id, ip_address, email, device_fingerprint):
    """Update fraud score for a user and auto-pause if needed"""
    score, risk_level, reasons = calculate_fraud_score(user_id, ip_address, email, device_fingerprint)
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Insert/update fraud score record
    cursor.execute('''
        INSERT INTO fraud_scores 
        (user_id, ip_address, email, device_fingerprint, fraud_score, risk_level, reasons, is_paused)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, ip_address, email, device_fingerprint, score, risk_level, 
          ', '.join(reasons), score >= 50.0))
    
    # Update user fraud score and pause status
    cursor.execute('''
        UPDATE users SET fraud_score = ?, is_paused = ? WHERE id = ?
    ''', (score, score >= 50.0, user_id))
    
    # Log duplicate detections if score is high
    if score >= 25.0:
        for reason in reasons:
            if 'email' in reason.lower():
                cursor.execute('''
                    INSERT INTO duplicate_detections 
                    (detection_type, duplicate_user_id, matching_field, matching_value, action_taken)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('email_duplicate', user_id, 'email', email, 'flagged' if score < 50.0 else 'paused'))
            elif 'ip' in reason.lower():
                cursor.execute('''
                    INSERT INTO duplicate_detections 
                    (detection_type, duplicate_user_id, matching_field, matching_value, action_taken)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('ip_duplicate', user_id, 'ip_address', ip_address, 'flagged' if score < 50.0 else 'paused'))
            elif 'fingerprint' in reason.lower():
                cursor.execute('''
                    INSERT INTO duplicate_detections 
                    (detection_type, duplicate_user_id, matching_field, matching_value, action_taken)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('device_duplicate', user_id, 'device_fingerprint', device_fingerprint, 
                      'flagged' if score < 50.0 else 'paused'))
    
    conn.commit()
    conn.close()
    
    return score >= 50.0  # Return True if user should be paused

# ---------------------------------------------------------------------------
# Email Notification Utility
#
# The application occasionally needs to notify administrators or advocates when
# important events occur, such as when an appointment is booked or a reward is
# issued.  A full featured implementation would integrate with an email
# provider (e.g., SMTP, SendGrid, SES).  For now we provide a simple helper
# that logs the intent to send an email.  This allows the rest of the
# application to call send_email() without crashing if an email service is not
# configured.  To wire up a real service, replace the body of this function
# with code that sends an email using your chosen provider.
def send_email(to_email: str, subject: str, message: str) -> None:
    """Send an email notification.

    Parameters
    ----------
    to_email : str
        Recipient email address.
    subject : str
        Subject line for the email.
    message : str
        Body of the email.

    Notes
    -----
    This is a stub implementation.  It simply prints the email to the
    application log.  Replace the print statement with your preferred email
    sending logic (for example, using smtplib or a transactional email API).
    """
    try:
        # Log the email being "sent".  In a production system you might use
        # smtplib, sendgrid, or another service here.
        print(f"[Email] To: {to_email} | Subject: {subject}\n{message}\n")
    except Exception as e:
        app.logger.error(f'Failed to send email to {to_email}: {e}')

def record_device_fingerprint(fingerprint_hash, user_agent, screen_resolution, timezone, language, plugins, canvas_fingerprint):
    """Record or update device fingerprint"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Check if fingerprint exists
    cursor.execute('SELECT id, user_count FROM device_fingerprints WHERE fingerprint_hash = ?', (fingerprint_hash,))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing fingerprint
        cursor.execute('''
            UPDATE device_fingerprints 
            SET last_seen = CURRENT_TIMESTAMP, user_count = user_count + 1
            WHERE id = ?
        ''', (existing[0],))
    else:
        # Insert new fingerprint
        cursor.execute('''
            INSERT INTO device_fingerprints 
            (fingerprint_hash, user_agent, screen_resolution, timezone, language, plugins, canvas_fingerprint, user_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        ''', (fingerprint_hash, user_agent, screen_resolution, timezone, language, plugins, canvas_fingerprint))
    
    conn.commit()
    conn.close()

def hash_patient_id(patient_id):
    """Hash patient ID for use in URLs and emails"""
    import hashlib
    # Use a consistent salt for hashing
    salt = app.secret_key.encode('utf-8')
    return hashlib.sha256(f"{patient_id}{salt}".encode('utf-8')).hexdigest()[:16]

def unhash_patient_id(hashed_id):
    """Find the original patient ID from hash (for internal use only)"""
    # Note: This is for reverse lookup in database - not cryptographically reversible
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('SELECT referral_id FROM referrals WHERE hashed_referral_id = ?', (hashed_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def generate_secure_referral_url(referral_id):
    """Generate a secure URL for referral tracking that doesn't expose patient info"""
    hashed_id = hash_patient_id(referral_id)
    # Store the mapping in database for lookup
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE referrals ADD COLUMN hashed_referral_id TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    cursor.execute('UPDATE referrals SET hashed_referral_id = ? WHERE referral_id = ?', 
                  (hashed_id, referral_id))
    conn.commit()
    conn.close()
    
    return f"/referral/track/{hashed_id}"

def log_audit_action(user_id, action, entity_type, entity_id, action_details, ip_address, user_agent):
    """Enhanced audit logging with fraud detection tracking"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO compliance_audit_trail (user_id, action_type, entity_type, entity_id, action_details, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, action, entity_type, entity_id, action_details, ip_address, user_agent))
    
    conn.commit()
    conn.close()

def check_user_paused(user_id):
    """Check if user is paused due to fraud score"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('SELECT is_paused FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else False

def require_active_user(f):
    """Decorator to check if user is not paused"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        if check_user_paused(session['user_id']):
            flash('Your account has been temporarily suspended. Please contact support.', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

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

def select_promotion(location='DASHBOARD_TOP'):
    """
    Select a promotion using weighted round-robin algorithm.
    Returns a promotion dict or None if no active promotions found.
    Falls back to house ads if no partner promotions are available.
    """
    import random
    import time
    from datetime import datetime
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get active promotions for the specified location
    current_time = datetime.now().isoformat()
    cursor.execute('''
        SELECT id, title, content, promotion_type, weight, link_url, image_url, 
               partner_name, impression_count, click_count
        FROM promotions 
        WHERE is_active = 1 
        AND location = ?
        AND (start_date IS NULL OR start_date <= ?)
        AND (end_date IS NULL OR end_date >= ?)
        ORDER BY promotion_type DESC  -- Partner promotions first
    ''', (location, current_time, current_time))
    
    promotions = cursor.fetchall()
    
    if not promotions:
        conn.close()
        return None
    
    # Separate partner and house promotions
    partner_promotions = [p for p in promotions if p[3] == 'partner']
    house_promotions = [p for p in promotions if p[3] == 'house']
    
    # Try to select from partner promotions first
    selected_promotion = None
    if partner_promotions:
        # Weighted round-robin selection
        total_weight = sum(p[4] for p in partner_promotions)  # p[4] is weight
        if total_weight > 0:
            rand_num = random.randint(1, total_weight)
            cumulative_weight = 0
            for promo in partner_promotions:
                cumulative_weight += promo[4]
                if rand_num <= cumulative_weight:
                    selected_promotion = promo
                    break
    
    # Fallback to house promotions if no partner promotion selected
    if not selected_promotion and house_promotions:
        # For house ads, use simple random selection
        selected_promotion = random.choice(house_promotions)
    
    if selected_promotion:
        # Convert to dict for easier template usage
        promotion_dict = {
            'id': selected_promotion[0],
            'title': selected_promotion[1],
            'content': selected_promotion[2],
            'promotion_type': selected_promotion[3],
            'weight': selected_promotion[4],
            'link_url': selected_promotion[5],
            'image_url': selected_promotion[6],
            'partner_name': selected_promotion[7],
            'impression_count': selected_promotion[8],
            'click_count': selected_promotion[9]
        }
        
        # Increment impression count
        cursor.execute('''
            UPDATE promotions SET impression_count = impression_count + 1 
            WHERE id = ?
        ''', (selected_promotion[0],))
        conn.commit()
        
        conn.close()
        return promotion_dict
    
    conn.close()
    return None

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
        
        # Get IP address and user agent for fraud detection
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
        user_agent = request.headers.get('User-Agent', '')
        device_fingerprint = data.get('deviceFingerprint', '')
        
        # Record device fingerprint if provided
        if device_fingerprint:
            record_device_fingerprint(
                device_fingerprint,
                user_agent,
                data.get('screenResolution', ''),
                data.get('timezone', ''),
                data.get('language', ''),
                data.get('plugins', ''),
                data.get('canvasFingerprint', '')
            )
            
            # Update user's device fingerprint
            cursor.execute('UPDATE users SET device_fingerprint = ? WHERE id = ?', 
                         (device_fingerprint, user_id))
        
        # Log registration audit
        log_audit_action(user_id, 'user_registration', 'user', user_id, 
                        f'Account created via onboarding - {data["accountType"]}', 
                        ip_address, user_agent)
        
        # Calculate and update fraud score
        is_paused = update_fraud_score(user_id, ip_address, data['email'], device_fingerprint)
        
        if is_paused:
            conn.close()
            return jsonify({
                'success': False, 
                'message': 'Account has been flagged for review. Please contact support.',
                'fraud_detected': True
            }), 403
        
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
    """User login"""
    provider_code = request.args.get('provider_code')
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash, full_name, role, is_paused FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user[2], password):
            # Check if user is paused due to fraud score
            if user[5]:  # is_paused column
                conn.close()
                flash('Your account has been temporarily suspended. Please contact support.', 'error')
                return redirect(url_for('login'))
            
            # Get IP address and user agent for audit logging
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
            user_agent = request.headers.get('User-Agent', '')
            
            # Log successful login
            log_audit_action(user[0], 'user_login', 'user', user[0], 
                           'Successful login', ip_address, user_agent)
            
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['full_name'] = user[3]
            session['role'] = user[4]
            
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
            conn.close()
    
    return render_template('login.html', provider_code=provider_code)

@app.route('/signup')
def signup():
    """Redirect signup to register page for compatibility"""
    return redirect(url_for('register'))

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
    
    # Get promotion for dashboard top
    dashboard_promotion = select_promotion('DASHBOARD_TOP')
    
    return render_template('dashboard.html', 
                         referrals=referrals, 
                         recent_documents=recent_documents,
                         dashboard_promotion=dashboard_promotion)

@app.route('/promotion/click/<int:promotion_id>')
def promotion_click(promotion_id):
    """Track promotion click and redirect to the promotion URL"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Increment click count
    cursor.execute('''
        UPDATE promotions SET click_count = click_count + 1 
        WHERE id = ?
    ''', (promotion_id,))
    
    # Get the promotion URL
    cursor.execute('SELECT link_url FROM promotions WHERE id = ?', (promotion_id,))
    result = cursor.fetchone()
    
    conn.commit()
    conn.close()
    
    if result and result[0]:
        return redirect(result[0])
    else:
        flash('Promotion link not found', 'error')
        return redirect(url_for('dashboard'))

@app.route('/referral/new', methods=['GET', 'POST'])
@require_active_user
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
        if status == 'trial' and trial_end:
            from datetime import datetime
            trial_end_date = datetime.fromisoformat(trial_end)
            if datetime.now() > trial_end_date:
                return jsonify({'has_subscription': False, 'message': 'Trial expired'})
        
        return jsonify({
            'has_subscription': True, 
            'plan_name': plan_name,
            'status': status
        })
    
    return jsonify({'has_subscription': False, 'message': 'No active subscription'})

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
    # Determine unread notifications for this dentist (messages addressed to them)
    cursor.execute('''
        SELECT COUNT(*) FROM messages
        WHERE recipient_id = ? AND is_read = 0 AND is_deleted_by_recipient = 0
    ''', (session['user_id'],))
    unread_count = cursor.fetchone()[0] or 0
    unread_notifications = True if unread_count > 0 else False

    conn.close()

    return render_template('portal/dentist.html', 
                         provider_info=provider_info,
                         stats=stats,
                         recent_referrals=recent_referrals,
                         incoming_stats=incoming_stats,
                         user_role=session.get('role'),
                         active='dashboard',
                         unread_notifications=unread_notifications)

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
    # Determine unread notifications for this specialist (messages addressed to them)
    cursor.execute('''
        SELECT COUNT(*) FROM messages
        WHERE recipient_id = ? AND is_read = 0 AND is_deleted_by_recipient = 0
    ''', (session['user_id'],))
    unread_count = cursor.fetchone()[0] or 0
    unread_notifications = True if unread_count > 0 else False

    conn.close()

    return render_template('portal/specialist.html',
                         provider_info=provider_info,
                         incoming_stats=incoming_stats,
                         outgoing_stats=outgoing_stats,
                         incoming_referrals=incoming_referrals,
                         user_role=session.get('role'),
                         active='dashboard',
                         unread_notifications=unread_notifications)

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

    # Determine unread notifications (messages that the user has not read)
    cursor.execute('''
        SELECT COUNT(*) FROM messages
        WHERE recipient_id = ? AND is_read = 0 AND is_deleted_by_recipient = 0
    ''', (session['user_id'],))
    unread_count = cursor.fetchone()[0] or 0
    unread_notifications = True if unread_count > 0 else False
    
    conn.close()

    return render_template('portal/patient.html',
                         referrals=referrals,
                         documents=documents,
                         referral_stats=referral_stats,
                         user_role=session.get('role'),
                         active='dashboard',
                         unread_notifications=unread_notifications)

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
    
    # Determine unread notifications for this admin
    cursor.execute('''
        SELECT COUNT(*) FROM messages
        WHERE recipient_id = ? AND is_read = 0 AND is_deleted_by_recipient = 0
    ''', (session['user_id'],))
    unread_count = cursor.fetchone()[0] or 0
    unread_notifications = True if unread_count > 0 else False

    conn.close()

    return render_template('portal/admin.html',
                         practice_info=practice_info,
                         practices_info=practices_info,
                         members=members,
                         stats=stats,
                         recent_activity=recent_activity,
                         user_role=user_role,
                         is_super_admin=(user_role == 'admin'),
                         active='dashboard',
                         unread_notifications=unread_notifications)

@app.route('/portal/messages')
def messages_portal():
    """Messages portal for all user types"""
    if 'user_id' not in session:
        flash('Please log in to access messages.', 'error')
        return redirect(url_for('login'))
    # Determine unread notifications for this user
    user_id = session.get('user_id')
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT COUNT(*) FROM messages
            WHERE recipient_id = ? AND is_read = 0 AND is_deleted_by_recipient = 0
        ''', (user_id,))
        unread_count = cursor.fetchone()[0] or 0
        unread_notifications = True if unread_count > 0 else False
    except Exception:
        unread_notifications = False
    finally:
        conn.close()

    return render_template('messages.html',
                           user_role=session.get('role'),
                           active='messages',
                           unread_notifications=unread_notifications)

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

@app.route('/portal/appointments')
def appointments_portal():
    """Appointments portal for all user types"""
    if 'user_id' not in session:
        flash('Please log in to access appointments.', 'error')
        return redirect(url_for('login'))
    
    user_role = session.get('role')
    user_id = session.get('user_id')
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get appointments based on user role
    if user_role in ['dentist', 'dentist_admin', 'specialist', 'specialist_admin']:
        # Providers see appointments with them
        cursor.execute('''
            SELECT a.id, a.appointment_id, a.appointment_date, a.appointment_type, 
                   a.status, a.patient_name, a.patient_email, a.patient_phone, 
                   a.reason, a.duration_minutes, a.notes, a.location, a.virtual_meeting_link,
                   u.full_name as created_by_name
            FROM appointments a
            LEFT JOIN users u ON a.created_by = u.id
            WHERE a.provider_id = ?
            ORDER BY a.appointment_date DESC
        ''', (user_id,))
    elif user_role == 'patient':
        # Patients see their own appointments
        cursor.execute('''
            SELECT a.id, a.appointment_id, a.appointment_date, a.appointment_type, 
                   a.status, a.patient_name, a.patient_email, a.patient_phone, 
                   a.reason, a.duration_minutes, a.notes, a.location, a.virtual_meeting_link,
                   p.full_name as provider_name
            FROM appointments a
            LEFT JOIN users p ON a.provider_id = p.id
            WHERE a.patient_id = ? OR a.patient_email = ?
            ORDER BY a.appointment_date DESC
        ''', (user_id, session.get('email')))
    else:  # admin
        # Admins see all appointments
        cursor.execute('''
            SELECT a.id, a.appointment_id, a.appointment_date, a.appointment_type, 
                   a.status, a.patient_name, a.patient_email, a.patient_phone, 
                   a.reason, a.duration_minutes, a.notes, a.location, a.virtual_meeting_link,
                   p.full_name as provider_name, u.full_name as created_by_name
            FROM appointments a
            LEFT JOIN users p ON a.provider_id = p.id
            LEFT JOIN users u ON a.created_by = u.id
            ORDER BY a.appointment_date DESC
        ''')
    
    appointments = cursor.fetchall()
    
    # Get available providers for new appointments (for patients and admins)
    providers = []
    if user_role in ['patient', 'admin']:
        cursor.execute('''
            SELECT id, full_name, role FROM users 
            WHERE role IN ('dentist', 'dentist_admin', 'specialist', 'specialist_admin')
            ORDER BY full_name
        ''')
        providers = cursor.fetchall()
    
    conn.close()
    
    return render_template('portal/appointments.html', 
                         appointments=appointments, 
                         providers=providers,
                         user_role=user_role)

@app.route('/api/appointments', methods=['POST'])
def create_appointment():
    """Create a new appointment"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    
    # Extract appointment data
    provider_id = data.get('provider_id')
    appointment_date = data.get('appointment_date')
    appointment_type = data.get('appointment_type', 'consultation')
    duration_minutes = data.get('duration_minutes', 60)
    patient_name = data.get('patient_name')
    patient_email = data.get('patient_email')
    patient_phone = data.get('patient_phone')
    reason = data.get('reason')
    notes = data.get('notes')
    location = data.get('location')
    virtual_meeting_link = data.get('virtual_meeting_link')
    
    # Validation
    if not all([provider_id, appointment_date, patient_name]):
        return jsonify({'error': 'Provider, appointment date, and patient name are required'}), 400
    
    # Generate unique appointment ID
    appointment_id = str(uuid.uuid4())[:12].upper()
    
    user_id = session.get('user_id')
    user_role = session.get('role')
    
    # Set patient_id if user is a patient
    patient_id = user_id if user_role == 'patient' else None
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO appointments (
                appointment_id, patient_id, provider_id, appointment_date, 
                appointment_type, duration_minutes, patient_name, patient_email, 
                patient_phone, reason, notes, location, virtual_meeting_link, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            appointment_id, patient_id, provider_id, appointment_date,
            appointment_type, duration_minutes, patient_name, patient_email,
            patient_phone, reason, notes, location, virtual_meeting_link, user_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'appointment_id': appointment_id,
            'message': 'Appointment created successfully'
        })
        
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Failed to create appointment: {str(e)}'}), 500

@app.route('/api/appointments/<appointment_id>', methods=['PUT'])
def update_appointment(appointment_id):
    """Update an appointment"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    user_id = session.get('user_id')
    user_role = session.get('role')
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Check if user has permission to update this appointment
    if user_role in ['dentist', 'dentist_admin', 'specialist', 'specialist_admin']:
        # Providers can update their own appointments
        cursor.execute('SELECT id FROM appointments WHERE appointment_id = ? AND provider_id = ?', 
                      (appointment_id, user_id))
    elif user_role == 'patient':
        # Patients can update their own appointments
        cursor.execute('SELECT id FROM appointments WHERE appointment_id = ? AND patient_id = ?', 
                      (appointment_id, user_id))
    else:  # admin
        # Admins can update any appointment
        cursor.execute('SELECT id FROM appointments WHERE appointment_id = ?', (appointment_id,))
    
    appointment = cursor.fetchone()
    if not appointment:
        conn.close()
        return jsonify({'error': 'Appointment not found or access denied'}), 404
    
    # Update appointment
    update_fields = []
    update_values = []
    
    allowed_fields = ['appointment_date', 'appointment_type', 'duration_minutes', 
                     'status', 'patient_name', 'patient_email', 'patient_phone', 
                     'reason', 'notes', 'location', 'virtual_meeting_link']
    
    for field in allowed_fields:
        if field in data:
            update_fields.append(f"{field} = ?")
            update_values.append(data[field])
    
    if update_fields:
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        update_values.append(appointment_id)
        
        query = f"UPDATE appointments SET {', '.join(update_fields)} WHERE appointment_id = ?"
        
        try:
            cursor.execute(query, update_values)
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Appointment updated successfully'})
            
        except Exception as e:
            conn.close()
            return jsonify({'error': f'Failed to update appointment: {str(e)}'}), 500
    
    conn.close()
    return jsonify({'error': 'No valid fields to update'}), 400

@app.route('/api/appointments/<appointment_id>', methods=['DELETE'])
def delete_appointment(appointment_id):
    """Delete an appointment"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session.get('user_id')
    user_role = session.get('role')
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Check if user has permission to delete this appointment
    if user_role in ['dentist', 'dentist_admin', 'specialist', 'specialist_admin']:
        # Providers can delete their own appointments
        cursor.execute('SELECT id FROM appointments WHERE appointment_id = ? AND provider_id = ?', 
                      (appointment_id, user_id))
    elif user_role == 'patient':
        # Patients can delete their own appointments
        cursor.execute('SELECT id FROM appointments WHERE appointment_id = ? AND patient_id = ?', 
                      (appointment_id, user_id))
    else:  # admin
        # Admins can delete any appointment
        cursor.execute('SELECT id FROM appointments WHERE appointment_id = ?', (appointment_id,))
    
    appointment = cursor.fetchone()
    if not appointment:
        conn.close()
        return jsonify({'error': 'Appointment not found or access denied'}), 404
    
    try:
        cursor.execute('DELETE FROM appointments WHERE appointment_id = ?', (appointment_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Appointment deleted successfully'})
        
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Failed to delete appointment: {str(e)}'}), 500

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
        return jsonify({'error': 'Invalid provider code or provider not found'}), 404
    
    # Verify provider is a dentist or specialist
    if provider[3] not in ['dentist', 'dentist_admin', 'specialist', 'specialist_admin']:
        conn.close()
        return jsonify({'error': 'Provider code is not valid for referrals'}), 400
    
    # Create referral
    referral_id = str(uuid.uuid4())[:8]
    target_doctor = provider[2]  # full_name
    
    cursor.execute('''
        INSERT INTO referrals (user_id, referral_id, patient_name, referring_doctor, target_doctor, medical_condition, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (provider[0], referral_id, patient_name, referring_doctor, target_doctor, medical_condition, 'pending', 
          f'Referral created using provider code {provider_code} for {provider[3]} {provider[4] or "practice"}'))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True, 
        'referral_id': referral_id,
        'target_doctor': target_doctor,
        'practice_name': provider[1],
        'provider_type': provider[3],
        'specialization': provider[4],
        'message': f'Referral successfully created to {provider[3]} {target_doctor}'
    })

# Stripe Payment Routes

@app.route('/subscribe/<plan_name>')
def subscribe(plan_name):
    """Start subscription process"""
    if 'user_id' not in session:
        flash('Please log in to subscribe.', 'error')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get plan details
    cursor.execute('SELECT * FROM subscription_plans WHERE plan_name = ?', (plan_name.title(),))
    plan = cursor.fetchone()
    
    if not plan:
        flash('Invalid subscription plan.', 'error')
        return redirect(url_for('pricing'))
    
    # Check if user already has an active subscription
    cursor.execute('''
        SELECT * FROM user_subscriptions 
        WHERE user_id = ? AND subscription_status = 'active'
    ''', (session['user_id'],))
    
    existing_sub = cursor.fetchone()
    conn.close()
    
    if existing_sub:
        flash('You already have an active subscription.', 'warning')
        return redirect(url_for('dashboard'))
    
    # Start free trial for trial plan
    if plan_name.lower() == 'free trial':
        return start_free_trial(plan)
    
    return render_template('subscribe.html', plan=plan, stripe_key=STRIPE_PUBLISHABLE_KEY)

@app.route('/start-free-trial')
def start_free_trial(plan=None):
    """Start 14-day free trial"""
    if 'user_id' not in session:
        flash('Please log in to start your free trial.', 'error')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    if not plan:
        # Get trial plan
        cursor.execute('SELECT * FROM subscription_plans WHERE plan_name = ?', ('Free Trial',))
        plan = cursor.fetchone()
    
    # Get professional plan for auto-renewal
    cursor.execute('SELECT * FROM subscription_plans WHERE plan_name = ?', ('Professional',))
    professional_plan = cursor.fetchone()
    
    # Calculate trial end date (14 days from now)
    trial_end = datetime.now() + timedelta(days=14)
    
    # Create subscription record
    cursor.execute('''
        INSERT INTO user_subscriptions 
        (user_id, plan_id, subscription_status, trial_end_date, end_date, auto_renew)
        VALUES (?, ?, 'trial', ?, ?, TRUE)
    ''', (session['user_id'], plan[0], trial_end, trial_end))
    
    # Generate provider code for the user
    provider_code = create_provider_code(
        session['user_id'], 
        session.get('role', 'dentist'),
        'Trial Practice',
        'General'
    )
    
    conn.commit()
    conn.close()
    
    flash(f'🎉 Your 14-day free trial has started! Your provider code is: {provider_code}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    """Create Stripe PaymentIntent"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        plan_id = data['plan_id']
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        # Get plan details
        cursor.execute('SELECT * FROM subscription_plans WHERE id = ?', (plan_id,))
        plan = cursor.fetchone()
        
        if not plan:
            return jsonify({'error': 'Invalid plan'}), 400
        
        # Calculate amount based on billing cycle
        amount = int(plan[3] * 100) if billing_cycle == 'monthly' else int(plan[4] * 100)  # Convert to cents
        
        # Create or retrieve Stripe customer
        cursor.execute('SELECT stripe_customer_id FROM user_subscriptions WHERE user_id = ?', (session['user_id'],))
        existing_customer = cursor.fetchone()
        
        if existing_customer and existing_customer[0]:
            customer_id = existing_customer[0]
        else:
            # Create new Stripe customer
            customer = stripe.Customer.create(
                email=session.get('email'),
                name=session.get('full_name'),
                metadata={'user_id': session['user_id']}
            )
            customer_id = customer.id
        
        # Create PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            customer=customer_id,
            metadata={
                'user_id': session['user_id'],
                'plan_id': plan_id,
                'billing_cycle': billing_cycle
            }
        )
        
        conn.close()
        
        return jsonify({
            'client_secret': intent.client_secret,
            'customer_id': customer_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ.get('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        handle_successful_payment(payment_intent)
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_update(subscription)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_cancellation(subscription)
    
    return 'Success', 200

def handle_successful_payment(payment_intent):
    """Handle successful payment"""
    user_id = payment_intent['metadata']['user_id']
    plan_id = payment_intent['metadata']['plan_id']
    billing_cycle = payment_intent['metadata']['billing_cycle']
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Update or create subscription
    cursor.execute('''
        INSERT OR REPLACE INTO user_subscriptions 
        (user_id, plan_id, subscription_status, billing_cycle, stripe_customer_id, stripe_payment_method_id)
        VALUES (?, ?, 'active', ?, ?, ?)
    ''', (user_id, plan_id, billing_cycle, payment_intent['customer'], payment_intent['payment_method']))
    
    # Generate provider code if not exists
    cursor.execute('SELECT provider_code FROM provider_codes WHERE user_id = ?', (user_id,))
    if not cursor.fetchone():
        # Get user role
        cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
        user_role = cursor.fetchone()[0]
        create_provider_code(user_id, user_role, 'Professional Practice', 'General')
    
    conn.commit()
    conn.close()

def handle_subscription_update(subscription):
    """Handle subscription updates"""
    customer_id = subscription['customer']
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE user_subscriptions 
        SET subscription_status = ?, stripe_subscription_id = ?
        WHERE stripe_customer_id = ?
    ''', (subscription['status'], subscription['id'], customer_id))
    
    conn.commit()
    conn.close()

def handle_subscription_cancellation(subscription):
    """Handle subscription cancellation"""
    customer_id = subscription['customer']
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE user_subscriptions 
        SET subscription_status = 'cancelled'
        WHERE stripe_customer_id = ?
    ''', (customer_id,))
    
    conn.commit()
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
            'Medical Updates', 'portal-referrals', 'portal-signup',
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
            'Medical Updates', 'portal-referrals', 'portal-signup',
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
        'Medical Updates', 'portal-referrals', 'portal-signup',
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
    """Legacy appointments page route.

    This endpoint previously served a static appointments page.  It now simply
    redirects authenticated users to the new dynamic appointments portal and
    unauthenticated users to the login page.
    """
    if 'user_id' not in session:
        flash('Please log in to view appointments.', 'error')
        return redirect(url_for('login'))
    # Redirect logged in users to the new appointments portal
    return redirect(url_for('portal_appointments'))

@app.route('/find-provider')
def find_provider():
    """Find provider page - search our network"""
    return render_template('find_provider.html')

@app.route('/portal')
def portal():
    """Main portal page with all key functionalities"""
    return send_from_directory('.', 'sapyyn_portal.html')

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
    """Referrals page - redirect to dashboard for logged in users"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/surgicalInstruction')
def surgical_instruction():
    """Surgical instruction page (legacy route)"""
    return send_from_directory('static', 'surgical-instruction-page.html')

@app.route('/casestudies')
def case_studies():
    """Case studies page"""
    return render_template('case_studies.html')

@app.route('/portal-1.html')
def portal_1():
    """Role-based portal-1 page with user-specific content"""
    if 'user_id' not in session:
        flash('Please log in to access the portal.', 'error')
        return redirect(url_for('login'))
    
    # Get user information from database for more complete session data
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, full_name, role FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        flash('User not found. Please log in again.', 'error')
        session.clear()
        return redirect(url_for('login'))
    
    # Update session with complete user data
    session['username'] = user[1]
    session['full_name'] = user[2]
    session['role'] = user[3]
    
    # Render role-specific portal-1 template
    return render_template('portal-1.html')

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

@app.route('/fraud-admin')
def fraud_admin():
    """Fraud detection administration dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check admin privileges  
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
    user_role = cursor.fetchone()[0]
    
    if user_role not in ['admin']:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get fraud statistics
    cursor.execute('SELECT COUNT(*) FROM fraud_scores WHERE fraud_score >= 50')
    high_risk_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM fraud_scores WHERE fraud_score >= 25 AND fraud_score < 50')
    medium_risk_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_paused = 1')
    paused_users_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM duplicate_detections WHERE detected_at > datetime("now", "-24 hours")')
    recent_duplicates = cursor.fetchone()[0]
    
    # Get recent high fraud scores
    cursor.execute('''
        SELECT fs.*, u.username, u.email, u.full_name
        FROM fraud_scores fs
        JOIN users u ON fs.user_id = u.id
        WHERE fs.fraud_score >= 25
        ORDER BY fs.created_at DESC
        LIMIT 20
    ''')
    high_fraud_users = cursor.fetchall()
    
    # Get duplicate detection summary
    cursor.execute('''
        SELECT detection_type, COUNT(*) as count
        FROM duplicate_detections
        WHERE detected_at > datetime("now", "-7 days")
        GROUP BY detection_type
    ''')
    duplicate_stats = cursor.fetchall()
    
    # Get device fingerprint sharing
    cursor.execute('''
        SELECT fingerprint_hash, user_count, last_seen
        FROM device_fingerprints
        WHERE user_count > 1
        ORDER BY user_count DESC
        LIMIT 10
    ''')
    shared_devices = cursor.fetchall()
    
    conn.close()
    
    return render_template('fraud_admin.html',
        high_risk_count=high_risk_count,
        medium_risk_count=medium_risk_count,
        paused_users_count=paused_users_count,
        recent_duplicates=recent_duplicates,
        high_fraud_users=high_fraud_users,
        duplicate_stats=duplicate_stats,
        shared_devices=shared_devices
    )

@app.route('/fraud-admin/user/<int:user_id>/unpause', methods=['POST'])
def unpause_user(user_id):
    """Unpause a user after admin review"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    # Check admin privileges
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
    user_role = cursor.fetchone()[0]
    
    if user_role not in ['admin']:
        return jsonify({'success': False, 'message': 'Admin privileges required'}), 403
    
    # Unpause user and reset fraud score
    cursor.execute('''
        UPDATE users SET is_paused = 0, fraud_score = 0 WHERE id = ?
    ''', (user_id,))
    
    # Log admin action
    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    username = cursor.fetchone()[0]
    
    log_audit_action(session['user_id'], 'admin_unpause_user', 'user', user_id,
                    f'Admin unpaused user: {username}',
                    request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', '')),
                    request.headers.get('User-Agent', ''))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'User unpaused successfully'})

@app.route('/fraud-admin/fraud-scores')
def fraud_scores_api():
    """API endpoint for fraud scores data"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Check admin privileges
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
    user_role = cursor.fetchone()[0]
    
    if user_role not in ['admin']:
        return jsonify({'error': 'Admin privileges required'}), 403
    
    # Get fraud score distribution
    cursor.execute('''
        SELECT 
            CASE 
                WHEN fraud_score >= 50 THEN 'High (50+)'
                WHEN fraud_score >= 25 THEN 'Medium (25-49)'
                WHEN fraud_score > 0 THEN 'Low (1-24)'
                ELSE 'Clean (0)'
            END as risk_category,
            COUNT(*) as count
        FROM users
        GROUP BY risk_category
    ''')
    distribution = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'distribution': [{'category': row[0], 'count': row[1]} for row in distribution]
    })

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
        print("Demo users created successfully!")
    else:
        print("Demo users already exist.")
    
    # Update existing 'doctor' role users to 'dentist' for compatibility
    cursor.execute("UPDATE users SET role = 'dentist' WHERE role = 'doctor'")
    conn.commit()
    

    
    
    conn.close()
@app.route('/my-referrals')
def my_referrals():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('sapyyn.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM referrals WHERE user_id = ?', (session['user_id'],))
    referrals = cursor.fetchall()
    conn.close()
    return render_template('my_referrals.html', referrals=referrals)

# Missing Core Routes
@app.route('/get-started')
def get_started_page_alt():
    """Get started onboarding page"""
    return send_from_directory('static', 'getstarted_page.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page"""
    if request.method == 'POST':
        email = request.form['email']
        # TODO: Implement password reset logic
        flash('Password reset instructions have been sent to your email.', 'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/profile')
def profile():
    """User profile page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('profile.html')

@app.route('/edit-profile')
def edit_profile():
    """Edit user profile page"""
    if 'user_id' not in session:

     
   
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
    
    flash('Password changed successfully!', 'success')
    return redirect(url_for('settings'))

@app.route('/settings')
def settings():
    """User settings page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('settings.html')

@app.route('/documents')
def view_documents_alt():
    """View user documents (alias for existing documents route)"""
    return documents()

@app.route('/conversion-dashboard')
@require_roles(['admin', 'dentist_admin', 'specialist_admin'])
def conversion_dashboard():
    """Conversion analytics dashboard"""
    return render_template('conversion_dashboard.html')

@app.route('/track-referral')
def track_referral():
    """Track referral page"""
    if 'user_id' not in session:
        flash('Please log in to track referrals.', 'error')
        return redirect(url_for('login'))
    return render_template('track_referral.html')

# Portal Route Aliases
@app.route('/portal/appointments')
def portal_appointments_dup():
    """Portal appointments page (alias)"""
    return appointments_portal()

@app.route('/portal/messages')
def messages_portal_dup():
    """Portal messages page (alias)"""
    return messages_portal()

# Rewards System Routes
@app.route('/rewards')
def rewards_dashboard():
    """Rewards dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('rewards/dashboard.html')

@app.route('/rewards/admin')
@require_roles(['admin', 'dentist_admin', 'specialist_admin'])
def rewards_admin():
    """Rewards administration"""
    return render_template('rewards/admin.html')

@app.route('/rewards/new-program')
@require_roles(['admin', 'dentist_admin', 'specialist_admin'])
def new_reward_program():
    """Create new reward program"""
    return render_template('rewards/new_program.html')


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
        return redirect(url_for('login'))
    return render_template('rewards/leaderboard.html')

@app.route('/rewards/compliance-audit')
@require_roles(['admin', 'dentist_admin', 'specialist_admin'])
def compliance_audit():
    """Compliance audit page"""
    return render_template('rewards/compliance_audit.html')

# Static Page Routes
@app.route('/about')
def about_dup():
    """About page"""
    return render_template('about.html')

@app.route('/blog')
def blog_dup():
    """Blog page"""
    return send_from_directory('static', 'blog.html')

@app.route('/surgical-instructions')
def surgical_instruction_dup():
    """Surgical instructions page"""
    return send_from_directory('static', 'surgical-instruction-page.html')

@app.route('/how-to-guides')
def how_to_guides_dup():
    """How-to guides page"""
    return render_template('how_to_guides.html')

# Admin Routes
@app.route('/admin')
@require_roles(['admin', 'dentist_admin', 'specialist_admin'])
def admin_panel_dup():
    """Admin panel redirect"""
    return redirect(url_for('admin_portal'))

@app.route('/static-pages/<path:filename>')
def serve_static_page_dup(filename):
    """Serve static HTML pages with authentication checks"""
    from urllib.parse import unquote
    filename = unquote(filename)
    if filename.endswith('.html'):
        filename = filename[:-5]
    
    # Define page categories for access control
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
        'Medical Updates', 'portal-referrals', 'portal-signup',
        'portal_integrations', 'portal_messaging', 'portal_settings',
        'patient', 'dentist', 'specialist', 'sapyyn-portal',
        'sapyyn_unified_portal', 'sapyyn_unified_portal (1)', 'sapyyn_unified_portal (2)',
        'updated_portal_rewards', 'appointments', 'forms', 'referrals',
        'referrals_page', 'referrals_page (1)', 'rewards', 'redeem list'
    ]
    
    # Check file exists
    static_file_path = os.path.join('static', f'{filename}.html')
    if not os.path.exists(static_file_path):
        return render_template('404.html'), 404

    
    conn = sqlite3.connect(config_class.DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM referrals WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],))
    referrals = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': r[0],
        'referral_id': r[2],
        'patient_name': r[3],
        'status': r[9],
        'created_at': r[15]
    } for r in referrals])

@app.route('/promotions/create')
@require_roles(['admin', 'dentist_admin', 'specialist_admin'])
def promotions_create():
    """Create promotion"""
    return render_template('promotions/create.html')

@app.route('/promotions/edit/<int:promotion_id>')
@require_roles(['admin', 'dentist_admin', 'specialist_admin'])
def promotions_edit(promotion_id):
    """Edit promotion"""
    return render_template('promotions/edit.html', promotion_id=promotion_id)

# Subscription Routes
@app.route('/subscribe/<plan_name>')
def subscribe_dup(plan_name):
    """Subscribe to a plan"""
    if 'user_id' not in session:
        flash('Please log in to subscribe.', 'error')
        return redirect(url_for('login'))
    return render_template('subscribe.html', plan_name=plan_name)

@app.route('/start-free-trial')
def start_free_trial_dup():
    """Start free trial"""
    if 'user_id' not in session:
        flash('Please log in to start your free trial.', 'error')
        return redirect(url_for('login'))
    
    # TODO: Implement trial logic
    flash('Your 14-day free trial has started!', 'success')
    return redirect(url_for('dashboard'))


# Register blueprints
app.register_blueprint(nocode_api, url_prefix='/api/nocode')
app.register_blueprint(nocodebackend_api, url_prefix='/api/nocodebackend')
app.register_blueprint(promotions, url_prefix='/promotions')
app.register_blueprint(admin_promotions, url_prefix='/admin/promotions')

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run application
    app.run(debug=config_class.DEBUG, host='0.0.0.0', port=5000)
