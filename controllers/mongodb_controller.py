"""
MongoDB API endpoints for Sapyyn application (replaces NoCodeBackend controller)
"""

from flask import Blueprint, request, jsonify, current_app, session
from services.mongodb_service import MongoDBService
import logging

# Create blueprint - keeping same URL prefix for compatibility
mongodb_api = Blueprint('mongodb_api', __name__, url_prefix='/api/nocodebackend')

# Initialize logger
logger = logging.getLogger(__name__)

# Helper function to check authentication
def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    
    # Preserve the original function's name and docstring
    decorated_function.__name__ = f.__name__
    decorated_function.__doc__ = f.__doc__
    
    return decorated_function

@mongodb_api.route('/referrals', methods=['GET'])
@require_auth
def get_referrals():
    """Get referrals from MongoDB"""
    try:
        service = MongoDBService()
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        skip = request.args.get('skip', 0, type=int)
        query = {}
        
        # Add filters if provided
        if 'status' in request.args:
            query['status'] = request.args.get('status')
        
        # Add user filter for regular users
        user_role = session.get('role', 'patient')
        if user_role not in ['admin', 'dentist_admin', 'specialist_admin']:
            query['user_id'] = session.get('user_id')
        
        # Get referrals
        result = service.get_referrals(query, limit, skip)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting referrals: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mongodb_api.route('/referrals', methods=['POST'])
@require_auth
def create_referral():
    """Create a new referral in MongoDB"""
    try:
        service = MongoDBService()
        
        # Get request data
        referral_data = request.json
        
        # Add user ID from session
        referral_data['user_id'] = session.get('user_id')
        
        # Create referral
        result = service.create_referral(referral_data)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error creating referral: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mongodb_api.route('/referrals/<referral_id>', methods=['PUT'])
@require_auth
def update_referral(referral_id):
    """Update a referral in MongoDB"""
    try:
        service = MongoDBService()
        
        # Get request data
        referral_data = request.json
        
        # Update referral
        result = service.update_referral(referral_id, referral_data)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error updating referral: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mongodb_api.route('/documents', methods=['POST'])
@require_auth
def upload_document():
    """Upload a document to MongoDB"""
    try:
        service = MongoDBService()
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is empty
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Get referral ID if provided
        referral_id = request.form.get('referral_id')
        
        # Prepare metadata
        metadata = {
            'user_id': session.get('user_id'),
            'uploaded_by': session.get('full_name', 'Unknown')
        }
        
        if referral_id:
            metadata['referral_id'] = referral_id
        
        # Upload document
        result = service.upload_document(
            file.read(),
            file.filename,
            file.content_type,
            metadata
        )
        
        # Link document to referral if provided
        if referral_id and result.get('success') and 'data' in result and '_id' in result['data']:
            document_id = result['data']['_id']
            link_result = service.link_document_to_referral(document_id, referral_id)
            if not link_result.get('success'):
                logger.warning(f"Failed to link document {document_id} to referral {referral_id}")
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mongodb_api.route('/documents', methods=['GET'])
@require_auth
def get_documents():
    """Get documents from MongoDB"""
    try:
        service = MongoDBService()
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        skip = request.args.get('skip', 0, type=int)
        query = {}
        
        # Add referral ID filter if provided
        if 'referral_id' in request.args:
            query['referral_id'] = request.args.get('referral_id')
        
        # Add user filter for regular users
        user_role = session.get('role', 'patient')
        if user_role not in ['admin', 'dentist_admin', 'specialist_admin']:
            query['user_id'] = session.get('user_id')
        
        # Get documents
        result = service.get_documents(query, limit, skip)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Add new endpoints for enhanced functionality
@mongodb_api.route('/referrals/<referral_id>', methods=['GET'])
@require_auth
def get_referral_detail(referral_id):
    """Get a single referral by ID"""
    try:
        service = MongoDBService()
        result = service.get_referral(referral_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting referral {referral_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mongodb_api.route('/referrals/<referral_id>/documents', methods=['GET'])
@require_auth
def get_referral_documents(referral_id):
    """Get all documents for a specific referral"""
    try:
        service = MongoDBService()
        result = service.get_referral_documents(referral_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting documents for referral {referral_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mongodb_api.route('/search/referrals', methods=['GET'])
@require_auth
def search_referrals():
    """Search referrals by text"""
    try:
        service = MongoDBService()
        
        search_query = request.args.get('q', '')
        limit = request.args.get('limit', 100, type=int)
        skip = request.args.get('skip', 0, type=int)
        
        if not search_query:
            return jsonify({'success': False, 'error': 'Search query is required'}), 400
        
        result = service.search_referrals(search_query, limit, skip)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error searching referrals: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mongodb_api.route('/stats', methods=['GET'])
@require_auth
def get_stats():
    """Get database statistics"""
    try:
        service = MongoDBService()
        result = service.get_stats()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500