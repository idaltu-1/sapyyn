"""
Security configuration for Sapyyn Flask application
Implements OWASP security best practices and HIPAA compliance measures
"""

import os
from datetime import timedelta

class SecurityConfig:
    """Security configuration class with HIPAA-compliant settings"""
    
    # CSRF Protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Session Security
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True  # No JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # 8-hour sessions
    
    # Security Headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com "
            "https://www.google-analytics.com https://static.hotjar.com "
            "https://script.hotjar.com https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net "
            "https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' https://www.google-analytics.com "
            "https://region1.google-analytics.com https://*.hotjar.com "
            "https://*.hotjar.io; "
            "frame-src 'self' https://www.youtube.com https://www.vimeo.com; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
    }
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_HEADERS_ENABLED = True
    
    # File Upload Security
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
    UPLOAD_PATH = 'uploads'
    
    # Database Security
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'sslmode': 'require' if os.environ.get('DATABASE_SSL') == 'true' else 'prefer'
        }
    }
    
    # HIPAA Compliance Settings
    AUDIT_LOG_ENABLED = True
    AUDIT_LOG_LEVEL = 'INFO'
    DATA_RETENTION_DAYS = 2555  # 7 years for HIPAA
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    
    # Authentication Settings
    PASSWORD_MIN_LENGTH = 12
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_SYMBOLS = True
    PASSWORD_HISTORY_COUNT = 12  # Remember last 12 passwords
    
    # Account Lockout
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=30)
    
    # Two-Factor Authentication
    TOTP_ENABLED = True
    TOTP_ISSUER = 'Sapyyn'
    
    # API Security
    API_RATE_LIMIT = "1000 per hour"
    API_KEY_REQUIRED = True
    
    # Logging and Monitoring
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s %(message)s'
    SECURITY_LOG_FILE = 'logs/security.log'
    
    # Environment-specific settings
    @classmethod
    def init_app(cls, app):
        """Initialize security settings for the Flask app"""
        
        # Set security headers
        @app.after_request
        def set_security_headers(response):
            for header, value in cls.SECURITY_HEADERS.items():
                response.headers[header] = value
            return response
        
        # Configure session security
        app.config.update(
            SECRET_KEY=cls.SECRET_KEY,
            SESSION_COOKIE_SECURE=cls.SESSION_COOKIE_SECURE,
            SESSION_COOKIE_HTTPONLY=cls.SESSION_COOKIE_HTTPONLY,
            SESSION_COOKIE_SAMESITE=cls.SESSION_COOKIE_SAMESITE,
            PERMANENT_SESSION_LIFETIME=cls.PERMANENT_SESSION_LIFETIME,
            WTF_CSRF_ENABLED=cls.WTF_CSRF_ENABLED,
            WTF_CSRF_TIME_LIMIT=cls.WTF_CSRF_TIME_LIMIT,
            MAX_CONTENT_LENGTH=cls.MAX_CONTENT_LENGTH
        )

class DevelopmentSecurityConfig(SecurityConfig):
    """Development environment security configuration"""
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    WTF_CSRF_ENABLED = False  # Disable CSRF in development for testing

class ProductionSecurityConfig(SecurityConfig):
    """Production environment security configuration"""
    # All security features enabled
    pass

class TestingSecurityConfig(SecurityConfig):
    """Testing environment security configuration"""
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    TESTING = True

# Configuration mapping
config = {
    'development': DevelopmentSecurityConfig,
    'production': ProductionSecurityConfig,
    'testing': TestingSecurityConfig,
    'default': DevelopmentSecurityConfig
}
