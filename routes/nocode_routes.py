"""
MongoDB API routes for Sapyyn application (formerly NoCodeBackend)
"""

from flask import Blueprint, request, jsonify, current_app
from utils.mongodb_utils import (
    get_referrals_from_mongodb,
    create_referral_in_mongodb,
    update_referral_in_mongodb,
    upload_document_to_mongodb
)

# Create blueprint - keeping same URL for compatibility
mongodb_api = Blueprint('mongodb_api', __name__, url_prefix='/api/nocode')

@mongodb_api.route('/referrals', methods=['GET'])
def get_referrals():
    """Get referrals from MongoDB"""
    # Get query parameters
    params = request.args.to_dict() if request.args else None
    
    # Get referrals
    result = get_referrals_from_mongodb(params)
    
    return jsonify(result)

@mongodb_api.route('/referrals', methods=['POST'])
def create_referral():
    """Create a new referral in MongoDB"""
    # Get request data
    referral_data = request.json
    
    # Create referral
    result = create_referral_in_mongodb(referral_data)
    
    return jsonify(result)

@mongodb_api.route('/referrals/<referral_id>', methods=['PUT'])
def update_referral(referral_id):
    """Update a referral in MongoDB"""
    # Get request data
    referral_data = request.json
    
    # Update referral
    result = update_referral_in_mongodb(referral_id, referral_data)
    
    return jsonify(result)

@mongodb_api.route('/documents', methods=['POST'])
def upload_document():
    """Upload a document to MongoDB"""
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if file is empty
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Upload document
    result = upload_document_to_mongodb(
        file.read(),
        file.filename,
        file.content_type
    )
    
    return jsonify(result)

# Update the blueprint reference
nocode_api = mongodb_api