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

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run application
    app.run(debug=config_class.DEBUG, host='0.0.0.0', port=5000)
