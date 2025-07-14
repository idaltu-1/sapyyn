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
from datetime import datetime, timedelta
import json
import stripe

app = Flask(__name__)
app.secret_key = 'sapyyn-patient-referral-system-2025'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Stripe configuration
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_...')  # Replace with your Stripe secret key
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_...')  # Replace with your Stripe publishable key

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
        ('Starter', 'individual', 49.99, 499.99, 'Basic referral management, Up to 50 referrals/month, Email support', 50, 1, 5, 'email'),
        ('Professional', 'practice', 99.99, 999.99, 'Advanced features, Up to 200 referrals/month, Priority support, Multi-user access', 200, 5, 25, 'priority'),
        ('Enterprise', 'enterprise', 499.00, 4999.00, 'Unlimited referrals, Unlimited users, Custom integrations, 24/7 phone support', -1, -1, 100, 'phone'),
        ('Free Trial', 'trial', 0.00, 0.00, '14-day free trial, Up to 10 referrals, Auto-renews to Professional', 10, 1, 1, 'email')
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

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/get_started_page')
def get_started_page():
    """Get started onboarding page"""
    return send_from_directory('static', 'getstarted_page.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash, full_name, role FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['full_name'] = user[3]
            session['role'] = user[4]
            flash('Login successful!', 'success')
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
        role = request.form.get('role', 'patient')
        
        password_hash = generate_password_hash(password)
        
        try:
            conn = sqlite3.connect('sapyyn.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, full_name, role))
            conn.commit()
            conn.close()
            
            flash('Registration successful! Please login.', 'success')
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

# ============================================================================
# REWARD SYSTEM ROUTES
# ============================================================================

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
    """Generate a unique 6-digit provider code"""
    import random
    while True:
        code = f"{random.randint(100000, 999999)}"
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM provider_codes WHERE provider_code = ?', (code,))
        if not cursor.fetchone():
            conn.close()
            return code
        conn.close()

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
    """Create a provider code for a user"""
    code = generate_provider_code()
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
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
def dentist_portal():
    """Dentist portal dashboard"""
    if 'user_id' not in session:
        flash('Please log in to access the dentist portal.', 'error')
        return redirect(url_for('login'))
    
    if session.get('role') not in ['dentist', 'dentist_admin']:
        flash('Access denied. This portal is for dentists only.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get dentist's provider code
    cursor.execute('''
        SELECT provider_code, practice_name, specialization 
        FROM provider_codes 
        WHERE user_id = ? AND provider_type = 'dentist' AND is_active = TRUE
    ''', (session['user_id'],))
    provider_info = cursor.fetchone()
    
    # Get referral stats
    cursor.execute('''
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
               SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
        FROM referrals WHERE user_id = ?
    ''', (session['user_id'],))
    stats = cursor.fetchone()
    
    # Get recent referrals
    cursor.execute('''
        SELECT referral_id, patient_name, target_doctor, status, created_at
        FROM referrals 
        WHERE user_id = ? 
        ORDER BY created_at DESC LIMIT 5
    ''', (session['user_id'],))
    recent_referrals = cursor.fetchall()
    
    conn.close()
    
    return render_template('portal/dentist.html', 
                         provider_info=provider_info,
                         stats=stats,
                         recent_referrals=recent_referrals)

@app.route('/portal/specialist')
def specialist_portal():
    """Specialist portal dashboard"""
    if 'user_id' not in session:
        flash('Please log in to access the specialist portal.', 'error')
        return redirect(url_for('login'))
    
    if session.get('role') not in ['specialist', 'specialist_admin']:
        flash('Access denied. This portal is for specialists only.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get specialist's provider code
    cursor.execute('''
        SELECT provider_code, practice_name, specialization 
        FROM provider_codes 
        WHERE user_id = ? AND provider_type = 'specialist' AND is_active = TRUE
    ''', (session['user_id'],))
    provider_info = cursor.fetchone()
    
    # Get incoming referrals for this specialist
    cursor.execute('''
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
               SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted
        FROM referrals 
        WHERE target_doctor = ? OR target_doctor LIKE ?
    ''', (session['full_name'], f"%{session['full_name']}%"))
    stats = cursor.fetchone()
    
    # Get recent incoming referrals
    cursor.execute('''
        SELECT referral_id, patient_name, referring_doctor, status, created_at
        FROM referrals 
        WHERE target_doctor = ? OR target_doctor LIKE ?
        ORDER BY created_at DESC LIMIT 5
    ''', (session['full_name'], f"%{session['full_name']}%"))
    recent_referrals = cursor.fetchall()
    
    conn.close()
    
    return render_template('portal/specialist.html',
                         provider_info=provider_info,
                         stats=stats,
                         recent_referrals=recent_referrals)

@app.route('/portal/patient')
def patient_portal():
    """Patient portal dashboard"""
    if 'user_id' not in session:
        flash('Please log in to access the patient portal.', 'error')
        return redirect(url_for('login'))
    
    if session.get('role') != 'patient':
        flash('Access denied. This portal is for patients only.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get patient's referrals (referrals where they are the subject)
    cursor.execute('''
        SELECT referral_id, referring_doctor, target_doctor, medical_condition, status, created_at
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
    
    conn.close()
    
    return render_template('portal/patient.html',
                         referrals=referrals,
                         documents=documents)

@app.route('/portal/admin')
def admin_portal():
    """Admin portal for practice management"""
    if 'user_id' not in session:
        flash('Please log in to access the admin portal.', 'error')
        return redirect(url_for('login'))
    
    if session.get('role') not in ['dentist_admin', 'specialist_admin', 'admin']:
        flash('Access denied. This portal is for administrators only.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get practice information
    cursor.execute('''
        SELECT p.*, us.plan_id, sp.plan_name, sp.plan_type
        FROM practices p
        LEFT JOIN user_subscriptions us ON p.subscription_id = us.id
        LEFT JOIN subscription_plans sp ON us.plan_id = sp.id
        WHERE p.admin_user_id = ?
    ''', (session['user_id'],))
    practice_info = cursor.fetchone()
    
    # Get practice members
    cursor.execute('''
        SELECT pm.*, u.full_name, u.email, u.role
        FROM practice_members pm
        JOIN users u ON pm.user_id = u.id
        WHERE pm.practice_id = (SELECT id FROM practices WHERE admin_user_id = ?)
    ''', (session['user_id'],))
    members = cursor.fetchall()
    
    # Get practice stats
    cursor.execute('''
        SELECT COUNT(*) as total_referrals,
               COUNT(DISTINCT user_id) as active_users
        FROM referrals 
        WHERE user_id IN (
            SELECT user_id FROM practice_members 
            WHERE practice_id = (SELECT id FROM practices WHERE admin_user_id = ?)
        )
    ''', (session['user_id'],))
    stats = cursor.fetchone()
    
    conn.close()
    
    return render_template('portal/admin.html',
                         practice_info=practice_info,
                         members=members,
                         stats=stats)

@app.route('/portal/provider-code/generate', methods=['POST'])
def generate_new_provider_code():
    """Generate new provider code for user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    provider_type = request.json.get('provider_type')
    practice_name = request.json.get('practice_name')
    specialization = request.json.get('specialization')
    
    if not provider_type:
        return jsonify({'error': 'Provider type is required'}), 400
    
    try:
        new_code = create_provider_code(session['user_id'], provider_type, practice_name, specialization)
        return jsonify({'success': True, 'provider_code': new_code})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/referral/by-code', methods=['POST'])
def create_referral_by_code():
    """Create referral using provider code"""
    provider_code = request.json.get('provider_code')
    patient_name = request.json.get('patient_name')
    referring_doctor = request.json.get('referring_doctor', 'Self-referral')
    medical_condition = request.json.get('medical_condition', '')
    
    if not provider_code or not patient_name:
        return jsonify({'error': 'Provider code and patient name are required'}), 400
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Find provider by code
    cursor.execute('''
        SELECT pc.user_id, pc.practice_name, u.full_name
        FROM provider_codes pc
        JOIN users u ON pc.user_id = u.id
        WHERE pc.provider_code = ? AND pc.is_active = TRUE
    ''', (provider_code,))
    
    provider = cursor.fetchone()
    
    if not provider:
        conn.close()
        return jsonify({'error': 'Invalid provider code'}), 404
    
    # Create referral
    referral_id = str(uuid.uuid4())[:8]
    target_doctor = provider[2]  # full_name
    
    cursor.execute('''
        INSERT INTO referrals (user_id, referral_id, patient_name, referring_doctor, target_doctor, medical_condition)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (provider[0], referral_id, patient_name, referring_doctor, target_doctor, medical_condition))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True, 
        'referral_id': referral_id,
        'target_doctor': target_doctor,
        'practice_name': provider[1]
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


@app.errorhandler(404)
def page_not_found(e):
    """Render custom 404 page"""
    return render_template('404.html'), 404
