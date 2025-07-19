"""
NoCodeBackend API endpoints for Sapyyn application
"""

from flask import Blueprint, request, jsonify, current_app, session
from services.nocodebackend_service import NoCodeBackendService
import logging

# Create blueprint
nocodebackend_api = Blueprint('nocodebackend_api', __name__, url_prefix='/api/nocodebackend')

# Initialize logger
logger = logging.getLogger(__name__)

# Helper function to check authentication
def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    
    # Preserve the original function's name and docstring
    decorated_function.__name__ = f.__name__
    decorated_function.__doc__ = f.__doc__
    
    return decorated_function

@nocodebackend_api.route('/referrals', methods=['GET'])
@require_auth
def get_referrals():
    """Get referrals from NoCodeBackend"""
    try:
        service = NoCodeBackendService()
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        skip = request.args.get('skip', 0, type=int)
        query = {}
        
        # Add filters if provided
        if 'status' in request.args:
            query['status'] = request.args.get('status')
        
        # Get referrals
        result = service.get_referrals(query, limit, skip)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting referrals: {str(e)}")
        return jsonify({'error': str(e)}), 500

@nocodebackend_api.route('/referrals', methods=['POST'])
@require_auth
def create_referral():
    """Create a new referral in NoCodeBackend"""
    try:
        service = NoCodeBackendService()
        
        # Get request data
        referral_data = request.json
        
        # Add user ID from session
        referral_data['user_id'] = session.get('user_id')
        
        # Create referral
        result = service.create_referral(referral_data)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error creating referral: {str(e)}")
        return jsonify({'error': str(e)}), 500

@nocodebackend_api.route('/referrals/<referral_id>', methods=['PUT'])
@require_auth
def update_referral(referral_id):
    """Update a referral in NoCodeBackend"""
    try:
        service = NoCodeBackendService()
        
        # Get request data
        referral_data = request.json
        
        # Update referral
        result = service.update_referral(referral_id, referral_data)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error updating referral: {str(e)}")
        return jsonify({'error': str(e)}), 500

@nocodebackend_api.route('/documents', methods=['POST'])
@require_auth
def upload_document():
    """Upload a document to NoCodeBackend"""
    try:
        service = NoCodeBackendService()
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is empty
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get referral ID if provided
        referral_id = request.form.get('referral_id')
        
        # Upload document
        result = service.upload_document(
            file.read(),
            file.filename,
            file.content_type
        )
        
        # Link document to referral if provided
        if referral_id and 'data' in result and '_id' in result['data']:
            document_id = result['data']['_id']
            service.link_document_to_referral(document_id, referral_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        return jsonify({'error': str(e)}), 500

@nocodebackend_api.route('/documents', methods=['GET'])
@require_auth
def get_documents():
    """Get documents from NoCodeBackend"""
    try:
        service = NoCodeBackendService()
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        skip = request.args.get('skip', 0, type=int)
        query = {}
        
        # Add referral ID filter if provided
        if 'referral_id' in request.args:
            query['referral_id'] = request.args.get('referral_id')
        
        # Get documents
        result = service.get_documents(query, limit, skip)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        return jsonify({'error': str(e)}), 500