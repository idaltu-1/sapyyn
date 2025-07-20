"""
Admin controller for managing promotions
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models import db, Promotion, PromotionRole, PromotionLocation
from services.promotion_service import PromotionService
from services.image_service import ImageService
from services.audit_service import AuditService
from datetime import datetime
import json

# Create blueprint
admin_promotions = Blueprint('admin_promotions', __name__, url_prefix='/admin/promotions')

# Helper function to check admin access
def require_admin(f):
    """Decorator to require admin access"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        
        if session.get('role') != 'admin':
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    
    # Preserve the original function's name and docstring
    decorated_function.__name__ = f.__name__
    decorated_function.__doc__ = f.__doc__
    
    return decorated_function

@admin_promotions.route('/')
@require_admin
def list_promotions():
    """Handle GET request to list promotions"""
    # Get filter parameters
    is_active = request.args.get('is_active')
    location = request.args.get('location')
    
    filters = {}
    if is_active is not None:
        filters['is_active'] = is_active.lower() == 'true'
    if location:
        try:
            filters['location'] = PromotionLocation(location)
        except ValueError:
            pass
    
    promotions = PromotionService.list_promotions(filters)
    
    # Get all available locations for the filter dropdown
    locations = [location.value for location in PromotionLocation]
    
    return render_template(
        'admin/promotions/list.html',
        promotions=promotions,
        locations=locations,
        current_filters=filters
    )

@admin_promotions.route('/create', methods=['GET', 'POST'])
@require_admin
def create_promotion():
    """Handle GET/POST requests to create a promotion"""
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        target_url = request.form.get('target_url')
        location = request.form.get('location')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        is_active = request.form.get('is_active') == 'on'
        allowed_roles = request.form.getlist('allowed_roles')
        
        # Validate required fields
        if not title or not target_url or not location or not start_date_str or not end_date_str:
            flash('Please fill in all required fields', 'error')
            return redirect(request.url)
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(request.url)
        
        # Validate location
        try:
            location_enum = PromotionLocation(location)
        except ValueError:
            flash('Invalid location', 'error')
            return redirect(request.url)
        
        # Handle image upload
        image_file = request.files.get('image')
        if not image_file:
            flash('Please upload an image', 'error')
            return redirect(request.url)
        
        # Validate and save image
        image_url = ImageService.save_promotion_image(image_file)
        if not image_url:
            flash('Invalid image. Please check size and format.', 'error')
            return redirect(request.url)
        
        # Create promotion
        promotion_data = {
            'title': title,
            'description': description,
            'image_url': image_url,
            'target_url': target_url,
            'location': location_enum,
            'start_date': start_date,
            'end_date': end_date,
            'is_active': is_active,
            'allowed_roles': allowed_roles
        }
        
        try:
            promotion = PromotionService.create_promotion(promotion_data)
            # Log the action
            AuditService.log_promotion_action('create', promotion.id, {
                'title': promotion.title,
                'location': promotion.location.value,
                'allowed_roles': allowed_roles
            })
            flash('Promotion created successfully', 'success')
            return redirect(url_for('admin_promotions.list_promotions'))
        except Exception as e:
            flash(f'Error creating promotion: {str(e)}', 'error')
            return redirect(request.url)
    
    # GET request - show form
    locations = [(location.value, location.name) for location in PromotionLocation]
    roles = ['patient', 'doctor', 'admin', 'specialist']
    
    return render_template(
        'admin/promotions/create.html',
        locations=locations,
        roles=roles
    )

@admin_promotions.route('/<int:promotion_id>/edit', methods=['GET', 'POST'])
@require_admin
def edit_promotion(promotion_id):
    """Handle GET/POST requests to edit a promotion"""
    promotion = PromotionService.get_promotion(promotion_id)
    if not promotion:
        flash('Promotion not found', 'error')
        return redirect(url_for('admin_promotions.list_promotions'))
    
    # Get current allowed roles
    current_roles = [role.role for role in promotion.allowed_roles]
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        target_url = request.form.get('target_url')
        location = request.form.get('location')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        is_active = request.form.get('is_active') == 'on'
        allowed_roles = request.form.getlist('allowed_roles')
        
        # Validate required fields
        if not title or not target_url or not location or not start_date_str or not end_date_str:
            flash('Please fill in all required fields', 'error')
            return redirect(request.url)
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(request.url)
        
        # Validate location
        try:
            location_enum = PromotionLocation(location)
        except ValueError:
            flash('Invalid location', 'error')
            return redirect(request.url)
        
        # Prepare update data
        promotion_data = {
            'title': title,
            'description': description,
            'target_url': target_url,
            'location': location_enum,
            'start_date': start_date,
            'end_date': end_date,
            'is_active': is_active,
            'allowed_roles': allowed_roles
        }
        
        # Handle image upload if provided
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            image_url = ImageService.save_promotion_image(image_file)
            if not image_url:
                flash('Invalid image. Please check size and format.', 'error')
                return redirect(request.url)
            promotion_data['image_url'] = image_url
        
        try:
            promotion = PromotionService.update_promotion(promotion_id, promotion_data)
            flash('Promotion updated successfully', 'success')
            return redirect(url_for('admin_promotions.list_promotions'))
        except Exception as e:
            flash(f'Error updating promotion: {str(e)}', 'error')
            return redirect(request.url)
    
    # GET request - show form with current values
    locations = [(location.value, location.name) for location in PromotionLocation]
    roles = ['patient', 'doctor', 'admin', 'specialist']
    
    # Format dates for the form
    start_date_str = promotion.start_date.strftime('%Y-%m-%d')
    end_date_str = promotion.end_date.strftime('%Y-%m-%d')
    
    return render_template(
        'admin/promotions/edit.html',
        promotion=promotion,
        locations=locations,
        roles=roles,
        current_roles=current_roles,
        start_date=start_date_str,
        end_date=end_date_str
    )

@admin_promotions.route('/<int:promotion_id>/delete', methods=['POST'])
@require_admin
def delete_promotion(promotion_id):
    """Handle POST request to delete a promotion"""
    if PromotionService.delete_promotion(promotion_id):
        flash('Promotion deleted successfully', 'success')
    else:
        flash('Promotion not found', 'error')
    
    return redirect(url_for('admin_promotions.list_promotions'))

@admin_promotions.route('/<int:promotion_id>/toggle', methods=['POST'])
@require_admin
def toggle_status(promotion_id):
    """Handle POST request to toggle promotion status"""
    is_active = request.form.get('is_active') == 'true'
    
    promotion = PromotionService.toggle_promotion_status(promotion_id, is_active)
    if promotion:
        status_text = 'activated' if is_active else 'deactivated'
        flash(f'Promotion {status_text} successfully', 'success')
    else:
        flash('Promotion not found', 'error')
    
    # If AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': promotion is not None})
    
    return redirect(url_for('admin_promotions.list_promotions'))

@admin_promotions.route('/<int:promotion_id>/stats', methods=['GET'])
@require_admin
def get_stats(promotion_id):
    """Handle GET request to get promotion stats"""
    promotion = PromotionService.get_promotion(promotion_id)
    if not promotion:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Promotion not found'}), 404
        flash('Promotion not found', 'error')
        return redirect(url_for('admin_promotions.list_promotions'))
    
    stats = {
        'impressions': promotion.impression_count,
        'clicks': promotion.click_count,
        'ctr': f"{promotion.click_through_rate * 100:.2f}%",
        'start_date': promotion.start_date.strftime('%Y-%m-%d'),
        'end_date': promotion.end_date.strftime('%Y-%m-%d'),
        'status': 'Active' if promotion.is_active else 'Inactive',
        'days_remaining': (promotion.end_date - datetime.utcnow()).days
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(stats)
    
    return render_template(
        'admin/promotions/stats.html',
        promotion=promotion,
        stats=stats
    )