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
def init_db():
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
    
    # Appointments table for portal functionality
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
    # database initialization.  The credentials are pulled from the user's
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
def init_db():
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
=======
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
def init_db():
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
>>>>>>> 089bcb1771f43e5ded380d1d377a3687562bf186
    
    # Configure the app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///sapyyn.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    from models import db
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(nocode_api)
    app.register_blueprint(nocodebackend_api)
    app.register_blueprint(promotions)
    app.register_blueprint(admin_promotions)
    
    # Example route
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/login')
    def login():
        return send_from_directory('static', 'Login.html')
    
    @app.route('/rewards')
    def rewards():
        return render_template('rewards.html')
    
