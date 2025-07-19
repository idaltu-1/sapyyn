"""
Application Configuration Management
Centralizes all configuration settings and removes hardcoded values
"""
import os
import secrets
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Security Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # Database Configuration
    DATABASE_NAME = os.environ.get('DATABASE_NAME', 'sapyyn.db')
    DATABASE_URL = os.environ.get('DATABASE_URL', f'sqlite:///{DATABASE_NAME}')
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    
    # External Service Configuration
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    NOCODEBACKEND_SECRET_KEY = os.environ.get('NOCODEBACKEND_SECRET_KEY')
    NOCODEBACKEND_REFERRAL_INSTANCE = os.environ.get('NOCODEBACKEND_REFERRAL_INSTANCE')
    NOCODEBACKEND_UPLOADS_INSTANCE = os.environ.get('NOCODEBACKEND_UPLOADS_INSTANCE')
    
    # Application URLs
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
    
    # Security Settings
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '100 per hour')
    
    # Password Policy
    PASSWORD_MIN_LENGTH = int(os.environ.get('PASSWORD_MIN_LENGTH', 8))
    PASSWORD_REQUIRE_UPPERCASE = os.environ.get('PASSWORD_REQUIRE_UPPERCASE', 'True').lower() == 'true'
    PASSWORD_REQUIRE_LOWERCASE = os.environ.get('PASSWORD_REQUIRE_LOWERCASE', 'True').lower() == 'true'
    PASSWORD_REQUIRE_NUMBERS = os.environ.get('PASSWORD_REQUIRE_NUMBERS', 'True').lower() == 'true'
    PASSWORD_REQUIRE_SYMBOLS = os.environ.get('PASSWORD_REQUIRE_SYMBOLS', 'True').lower() == 'true'
    PASSWORD_HISTORY_COUNT = int(os.environ.get('PASSWORD_HISTORY_COUNT', 12))
    
    # Business Logic Configuration
    PROVIDER_CODE_LENGTH = int(os.environ.get('PROVIDER_CODE_LENGTH', 6))
    PROVIDER_CODE_CHARS = os.environ.get('PROVIDER_CODE_CHARS', '23456789ABCDEFGHJKMNPQRSTUVWXYZ')
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # Analytics Configuration
    GA4_MEASUREMENT_ID = os.environ.get('GA4_MEASUREMENT_ID')
    GTM_CONTAINER_ID = os.environ.get('GTM_CONTAINER_ID')
    HOTJAR_SITE_ID = os.environ.get('HOTJAR_SITE_ID')
    ENABLE_ANALYTICS = os.environ.get('ENABLE_ANALYTICS', 'true').lower() == 'true'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = False
    TESTING = True
    DATABASE_NAME = ':memory:'  # In-memory database for tests
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # Force HTTPS in production
    
    # Override defaults for production
    RATELIMIT_DEFAULT = '50 per hour'  # Stricter rate limiting
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to syslog in production
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(config_name: str = None) -> Config:
    """Get configuration class based on environment"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config.get(config_name, config['default'])

# Subscription Plans Configuration
SUBSCRIPTION_PLANS = {
    'free': {
        'name': 'Basic',
        'price_monthly': 0.00,
        'price_yearly': 0.00,
        'description': 'Up to 5 referrals per month, basic support, email notifications',
        'referral_limit': 5,
        'specialists_limit': 1,
        'templates_limit': 1,
        'support_level': 'email'
    },
    'practice': {
        'name': 'Professional',
        'price_monthly': 49.99,
        'price_yearly': 499.99,
        'description': 'Unlimited referrals, up to 3 specialists, 10 custom templates, priority support',
        'referral_limit': -1,  # -1 means unlimited
        'specialists_limit': 3,
        'templates_limit': 10,
        'support_level': 'priority'
    },
    'enterprise': {
        'name': 'Enterprise',
        'price_monthly': 199.99,
        'price_yearly': 1999.99,
        'description': 'Unlimited everything, dedicated support, custom integrations',
        'referral_limit': -1,
        'specialists_limit': -1,
        'templates_limit': -1,
        'support_level': 'dedicated'
    }
}

# Admin User Configuration (for initial setup only)
INITIAL_ADMIN = {
    'username': os.environ.get('INITIAL_ADMIN_USERNAME', 'admin'),
    'email': os.environ.get('INITIAL_ADMIN_EMAIL', 'admin@sapyyn.com'),
    'full_name': os.environ.get('INITIAL_ADMIN_NAME', 'System Administrator'),
    'role': 'admin'
}

def generate_secure_password(length: int = 16) -> str:
    """Generate a cryptographically secure password"""
    import string
    import secrets
    
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password
