"""
Configuration module for Sapyyn application
Contains security and domain settings
"""

import os
from typing import List

class Config:
    """Application configuration"""
    
    # Security configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'sapyyn-patient-referral-system-2025')
    
    # Domain restrictions for login
    ALLOWED_DOMAINS = os.environ.get('ALLOWED_DOMAINS', '').split(',') if os.environ.get('ALLOWED_DOMAINS') else [
        'sapyyn.com',
        'dentalcenter.com', 
        'orthodontics.com',
        'medicalpractice.com',
        'gmail.com',  # Allow gmail for demo/testing
        'yahoo.com',  # Allow yahoo for demo/testing
        'outlook.com'  # Allow outlook for demo/testing
    ]
    
    # Remove empty strings from domains list
    ALLOWED_DOMAINS = [domain.strip() for domain in ALLOWED_DOMAINS if domain.strip()]
    
    # Password complexity requirements
    PASSWORD_MIN_LENGTH = 10
    PASSWORD_REQUIRE_UPPER = True
    PASSWORD_REQUIRE_LOWER = True
    PASSWORD_REQUIRE_DIGIT = True
    PASSWORD_REQUIRE_SYMBOL = True
    
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sapyyn.db')
    
    # Flask-WTF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    @classmethod
    def is_domain_allowed(cls, email: str) -> bool:
        """Check if email domain is in allowed domains list"""
        if not email or '@' not in email:
            return False
        
        domain = email.split('@')[1].lower()
        return domain in [d.lower() for d in cls.ALLOWED_DOMAINS]
    
    @classmethod
    def get_password_requirements_text(cls) -> str:
        """Get human-readable password requirements"""
        requirements = []
        requirements.append(f"at least {cls.PASSWORD_MIN_LENGTH} characters")
        
        if cls.PASSWORD_REQUIRE_UPPER:
            requirements.append("uppercase letter")
        if cls.PASSWORD_REQUIRE_LOWER:
            requirements.append("lowercase letter")
        if cls.PASSWORD_REQUIRE_DIGIT:
            requirements.append("number")
        if cls.PASSWORD_REQUIRE_SYMBOL:
            requirements.append("special character")
        
        return "Password must contain " + ", ".join(requirements[:-1]) + " and " + requirements[-1] + "."