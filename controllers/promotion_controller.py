"""
User-facing controller for promotions
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, abort
from models import db, User, UserPromotionPreference
from services.promotion_service import PromotionService
from services.audit_service import AuditService
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import re

# Create blueprint
promotions = Blueprint('promotions', __name__, url_prefix='/promotions')

@promotions.route('/slot/<location>')
def get_promotion_slot(location):
    """Handle request to get a promotion for a location
    
    Args:
        location (str): Location identifier
        
    Returns:
        HTML: Rendered promotion slot
    """
    try:
        # Get current user if logged in
        user = None
        if 'user_id' in session:
            user_id = session['user_id']
            user = User.query.get(user_id)
        
        # Get promotion for this location
        promotion = PromotionService.get_promotion_for_location(location, user)
        
        # Record impression if promotion found
        if promotion:
            PromotionService.record_impression(promotion.id)
        
        # Render the promotion slot
        return render_template(
            'components/promotion_slot.html',
            promotion=promotion,
            location=location
        )
    except Exception as e:
        # Log the error
        print(f"Error getting promotion: {str(e)}")
        # Return empty slot
        return render_template(
            'components/promotion_slot.html',
            promotion=None,
            location=location
        )

@promotions.route('/api/slot/<location>')
def get_promotion_api(location):
    """API endpoint to get a promotion for a location
    
    Args:
        location (str): Location identifier
        
    Returns:
        JSON: Promotion data or empty object
    """
    try:
        # Get current user if logged in
        user = None
        if 'user_id' in session:
            user_id = session['user_id']
            user = User.query.get(user_id)
        
        # Get promotion for this location
        promotion = PromotionService.get_promotion_for_location(location, user)
        
        # Record impression if promotion found
        if promotion:
            PromotionService.record_impression(promotion.id)
            
            # Return promotion data
            return jsonify({
                'id': promotion.id,
                'title': promotion.title,
                'image_url': promotion.image_url,
                'target_url': f"/promotions/redirect/{promotion.id}",
                'sponsored': True
            })
        
        # Return empty object if no promotion found
        return jsonify({})
    except Exception as e:
        # Log the error
        print(f"Error getting promotion: {str(e)}")
        return jsonify({'error': str(e)}), 500

def sanitize_url(url, user=None):
    """Sanitize URL to prevent data leakage
    
    Args:
        url (str): The URL to sanitize
        user (User, optional): The current user
        
    Returns:
        str: The sanitized URL
    """
    # Ensure the URL is absolute and has a scheme
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    # Parse the URL
    parsed = urlparse(url)
    
    # Get query parameters
    query_params = parse_qs(parsed.query)
    
    # Remove potentially sensitive parameters
    sensitive_params = ['token', 'auth', 'key', 'password', 'secret', 'session', 
                       'user', 'patient', 'medical', 'health', 'record', 'mrn', 
                       'ssn', 'dob', 'birth']
    
    # Remove any parameter that contains sensitive keywords
    sanitized_params = {}
    for key, value in query_params.items():
        is_sensitive = False
        for param in sensitive_params:
            if param.lower() in key.lower():
                is_sensitive = True
                break
        if not is_sensitive:
            sanitized_params[key] = value
    
    # Rebuild the query string
    query_string = urlencode(sanitized_params, doseq=True) if sanitized_params else ''
    
    # Rebuild the URL
    sanitized_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        query_string,
        ''  # Remove fragment to prevent tracking
    ))
    
    return sanitized_url

@promotions.route('/redirect/<int:promotion_id>')
def record_click(promotion_id):
    """Handle redirect request when a promotion is clicked
    
    Args:
        promotion_id (int): ID of the promotion
        
    Returns:
        Redirect: Redirects to the target URL
    """
    promotion = PromotionService.get_promotion(promotion_id)
    if not promotion:
        abort(404)
    
    # Record the click
    PromotionService.record_click(promotion_id)
    
    # Get current user if logged in
    user = None
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
    
    # Sanitize the target URL
    target_url = sanitize_url(promotion.target_url, user)
    
    # Log the redirect
    AuditService.log_action('click', 'promotion', promotion_id, {
        'target_url': target_url
    })
    
    # Redirect to the target URL
    return redirect(target_url)

@promotions.route('/preferences', methods=['GET', 'POST'])
def update_preferences():
    """Handle request to update promotion preferences
    
    Returns:
        Redirect: Redirects to settings page
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        opt_out = request.form.get('opt_out') == 'on'
        
        # Get or create user preferences
        user_prefs = UserPromotionPreference.query.filter_by(user_id=user_id).first()
        if not user_prefs:
            user_prefs = UserPromotionPreference(user_id=user_id)
            db.session.add(user_prefs)
        
        # Update preferences
        user_prefs.opt_out = opt_out
        user_prefs.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash_message = 'You have opted out of targeted promotions.' if opt_out else 'You will now see targeted promotions.'
        flash(flash_message, 'success')
    
    # Redirect to settings page
    return redirect(url_for('settings'))