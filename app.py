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

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run application
    app.run(debug=config_class.DEBUG, host='0.0.0.0', port=5000)
