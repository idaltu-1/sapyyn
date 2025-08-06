"""
Supabase API routes for Sapyyn application.
This module replaces the NoCodeBackend routes.
"""

from flask import Blueprint, request, jsonify, current_app
from utils.supabase_utils import (
    get_referrals_from_supabase,
    create_referral_in_supabase,
    update_referral_in_supabase,
    upload_document_to_supabase
)

# Create blueprint
supabase_routes = Blueprint('supabase_routes', __name__, url_prefix='/api/supabase')

@supabase_routes.route('/referrals', methods=['GET'])
def get_referrals():
    """Get referrals from Supabase"""
    # Get query parameters
    params = request.args.to_dict() if request.args else None
    
    # Get referrals
    result = get_referrals_from_supabase(params)
    
    return jsonify(result)

@supabase_routes.route('/referrals', methods=['POST'])
def create_referral():
    """Create a new referral in Supabase"""
    # Get request data
    referral_data = request.json
    
    # Create referral
    result = create_referral_in_supabase(referral_data)
    
    return jsonify(result)

@supabase_routes.route('/referrals/<referral_id>', methods=['PUT'])
def update_referral(referral_id):
    """Update a referral in Supabase"""
    # Get request data
    referral_data = request.json
    
    # Update referral
    result = update_referral_in_supabase(referral_id, referral_data)
    
    return jsonify(result)

@supabase_routes.route('/documents', methods=['POST'])
def upload_document():
    """Upload a document to Supabase Storage"""
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if file is empty
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Upload document
    result = upload_document_to_supabase(
        file.read(),
        file.filename,
        file.content_type
    )
    
    return jsonify(result)