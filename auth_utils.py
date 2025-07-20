"""
Authentication and security utilities for Sapyyn
"""

import re
import functools
from typing import List, Union, Tuple
from flask import session, request, redirect, url_for, flash, jsonify
from config import Config

def validate_password_complexity(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password complexity according to requirements
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check minimum length
    if len(password) < Config.PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {Config.PASSWORD_MIN_LENGTH} characters long")
    
    # Check for uppercase letter
    if Config.PASSWORD_REQUIRE_UPPER and not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    # Check for lowercase letter
    if Config.PASSWORD_REQUIRE_LOWER and not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    # Check for digit
    if Config.PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    # Check for special character
    if Config.PASSWORD_REQUIRE_SYMBOL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")
    
    return len(errors) == 0, errors

def validate_domain_restriction(email: str) -> Tuple[bool, str]:
    """
    Validate email domain against allowed domains
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not Config.is_domain_allowed(email):
        domain = email.split('@')[1] if '@' in email else ''
        return False, f"Email domain '{domain}' is not in the allowed domains list. Access restricted to authorized domains only."
    
    return True, ""

def require_roles(allowed_roles: Union[str, List[str]], redirect_route: str = 'login'):
    """
    Decorator to require specific roles for route access
    
    Args:
        allowed_roles: Single role string or list of allowed roles
        redirect_route: Route to redirect to if access denied
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
    
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is logged in
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required', 'redirect': url_for(redirect_route)}), 401
                flash('Please log in to access this page.', 'error')
                return redirect(url_for(redirect_route))
            
            # Check if user has required role
            user_role = session.get('role')
            if user_role not in allowed_roles:
                if request.is_json:
                    return jsonify({'error': 'Access denied. Insufficient privileges.'}), 403
                flash('Access denied. You do not have permission to view this page.', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_login(redirect_route: str = 'login'):
    """
    Decorator to require login for route access
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required', 'redirect': url_for(redirect_route)}), 401
                flash('Please log in to access this page.', 'error')
                return redirect(url_for(redirect_route))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Role hierarchy and permissions
ROLE_HIERARCHY = {
    'admin': ['admin', 'dentist_admin', 'specialist_admin', 'dentist', 'specialist', 'patient'],
    'dentist_admin': ['dentist_admin', 'dentist'],
    'specialist_admin': ['specialist_admin', 'specialist'],
    'dentist': ['dentist'],
    'specialist': ['specialist'],
    'patient': ['patient']
}

# Page access permissions
PAGE_PERMISSIONS = {
    # Patient pages
    'dashboard': ['admin', 'dentist_admin', 'specialist_admin', 'dentist', 'specialist', 'patient'],
    'appointments': ['admin', 'dentist_admin', 'specialist_admin', 'dentist', 'specialist', 'patient'],
    'messages': ['admin', 'dentist_admin', 'specialist_admin', 'dentist', 'specialist', 'patient'],
    'documents': ['admin', 'dentist_admin', 'specialist_admin', 'dentist', 'specialist', 'patient'],
    'my_referrals': ['admin', 'dentist_admin', 'specialist_admin', 'dentist', 'specialist', 'patient'],
    
    # Provider pages
    'referrals': ['admin', 'dentist_admin', 'specialist_admin', 'dentist', 'specialist'],
    'new_referral': ['admin', 'dentist_admin', 'specialist_admin', 'dentist', 'specialist'],
    'track_referral': ['admin', 'dentist_admin', 'specialist_admin', 'dentist', 'specialist', 'patient'],
    
    # Admin pages
    'admin_panel': ['admin', 'dentist_admin', 'specialist_admin'],
    'user_management': ['admin'],
    'analytics_dashboard': ['admin', 'dentist_admin', 'specialist_admin'],
    'subscription_management': ['admin'],
    
    # Upload and file management
    'upload_file': ['admin', 'dentist_admin', 'specialist_admin', 'dentist', 'specialist', 'patient'],
    'view_documents': ['admin', 'dentist_admin', 'specialist_admin', 'dentist', 'specialist', 'patient'],
}

def can_access_page(page_name: str, user_role: str) -> bool:
    """
    Check if user role can access specific page
    
    Args:
        page_name: Name of the page/route
        user_role: User's role
        
    Returns:
        True if access allowed, False otherwise
    """
    allowed_roles = PAGE_PERMISSIONS.get(page_name, [])
    return user_role in allowed_roles

def require_page_access(page_name: str):
    """
    Decorator to check page-specific access permissions
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is logged in
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required', 'redirect': url_for('login')}), 401
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('login'))
            
            # Check page access
            user_role = session.get('role')
            if not can_access_page(page_name, user_role):
                if request.is_json:
                    return jsonify({'error': 'Access denied. Insufficient privileges.'}), 403
                flash('Access denied. You do not have permission to view this page.', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator