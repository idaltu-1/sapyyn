"""
NoCodeBackend API routes for Sapyyn application
"""

from flask import Blueprint, request, jsonify, current_app
from utils.nocodebackend_utils import (
    get_referrals_from_nocode,
    create_referral_in_nocode,
    update_referral_in_nocode,
    upload_document_to_nocode
)

# Create blueprint
nocode_api = Blueprint('nocode_api', __name__, url_prefix='/api/nocode')

@nocode_api.route('/referrals', methods=['GET'])
def get_referrals():
    """Get referrals from NoCodeBackend"""
    # Get query parameters
    params = request.args.to_dict() if request.args else None
    
    # Get referrals
    result = get_referrals_from_nocode(params)
    
    return jsonify(result)

@nocode_api.route('/referrals', methods=['POST'])
def create_referral():
    """Create a new referral in NoCodeBackend"""
    # Get request data
    referral_data = request.json
    
    # Create referral
    result = create_referral_in_nocode(referral_data)
    
    return jsonify(result)

@nocode_api.route('/referrals/<referral_id>', methods=['PUT'])
def update_referral(referral_id):
    """Update a referral in NoCodeBackend"""
    # Get request data
    referral_data = request.json
    
    # Update referral
    result = update_referral_in_nocode(referral_id, referral_data)
    
    return jsonify(result)

@nocode_api.route('/documents', methods=['POST'])
def upload_document():
    """Upload a document to NoCodeBackend"""
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if file is empty
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Upload document
    result = upload_document_to_nocode(
        file.read(),
        file.filename,
        file.content_type
    )
    
    return jsonify(result)