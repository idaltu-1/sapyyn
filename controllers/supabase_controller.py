"""
Supabase API endpoints for Sapyyn application.
This controller replaces the NoCodeBackend controller.
"""

from flask import Blueprint, request, jsonify, current_app, session
from services.supabase_service import SupabaseService
from datetime import datetime
import logging

# Create blueprint
supabase_api = Blueprint('supabase_api', __name__, url_prefix='/api/supabase')

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

@supabase_api.route('/referrals', methods=['GET'])
@require_auth
def get_referrals():
    """Get referrals from Supabase"""
    try:
        service = SupabaseService()
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        skip = request.args.get('skip', 0, type=int)
        query = {}
        
        # Add filters if provided
        if 'status' in request.args:
            query['status'] = request.args.get('status')
        if 'user_id' in request.args:
            query['user_id'] = request.args.get('user_id')
        if 'patient_name' in request.args:
            query['patient_name'] = request.args.get('patient_name')
        
        # Get referrals
        result = service.get_referrals(query, limit, skip)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting referrals: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_api.route('/referrals', methods=['POST'])
@require_auth
def create_referral():
    """Create a new referral in Supabase"""
    try:
        service = SupabaseService()
        
        # Get request data
        referral_data = request.json
        
        # Add user ID from session
        referral_data['user_id'] = session.get('user_id')
        referral_data['created_by'] = session.get('full_name', '')
        
        # Add timestamp
        from datetime import datetime
        referral_data['created_at'] = datetime.utcnow().isoformat()
        referral_data['updated_at'] = datetime.utcnow().isoformat()
        
        # Create referral
        result = service.create_referral(referral_data)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error creating referral: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_api.route('/referrals/<referral_id>', methods=['GET'])
@require_auth
def get_referral(referral_id):
    """Get a specific referral by ID"""
    try:
        service = SupabaseService()
        
        # Get referral
        result = service.get_referrals({'id': referral_id})
        
        if result.get('success') and result.get('data'):
            referral = result['data'][0] if result['data'] else None
            if referral:
                # Get associated documents
                doc_result = service.get_referral_documents(referral_id)
                referral['documents'] = doc_result.get('data', []) if doc_result.get('success') else []
                
                return jsonify({
                    'success': True,
                    'data': referral
                })
        
        return jsonify({'success': False, 'error': 'Referral not found'}), 404
        
    except Exception as e:
        logger.error(f"Error getting referral {referral_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_api.route('/referrals/<referral_id>', methods=['PUT'])
@require_auth
def update_referral(referral_id):
    """Update a referral in Supabase"""
    try:
        service = SupabaseService()
        
        # Get request data
        referral_data = request.json
        
        # Add update timestamp
        from datetime import datetime
        referral_data['updated_at'] = datetime.utcnow().isoformat()
        referral_data['updated_by'] = session.get('full_name', '')
        
        # Update referral
        result = service.update_referral(referral_id, referral_data)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error updating referral: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_api.route('/documents', methods=['POST'])
@require_auth
def upload_document():
    """Upload a document to Supabase Storage"""
    try:
        service = SupabaseService()
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is empty
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Get referral ID if provided
        referral_id = request.form.get('referral_id')
        file_type = request.form.get('file_type', 'document')
        
        # Generate unique filename
        import uuid
        from datetime import datetime
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}_{file.filename}"
        
        # Upload document
        result = service.upload_document(
            file.read(),
            unique_filename,
            file.content_type
        )
        
        # Link document to referral if provided
        if referral_id and result.get('success') and result.get('data', {}).get('document_id'):
            document_id = result['data']['document_id']
            link_result = service.link_document_to_referral(document_id, referral_id)
            if not link_result.get('success'):
                logger.warning(f"Failed to link document {document_id} to referral {referral_id}")
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_api.route('/documents', methods=['GET'])
@require_auth
def get_documents():
    """Get documents from Supabase"""
    try:
        service = SupabaseService()
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        skip = request.args.get('skip', 0, type=int)
        query = {}
        
        # Add referral ID filter if provided
        if 'referral_id' in request.args:
            query['referral_id'] = request.args.get('referral_id')
        
        # Add user filter to only show user's documents
        query['user_id'] = session.get('user_id')
        
        # Get documents
        result = service.get_documents(query, limit, skip)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_api.route('/documents/<document_id>', methods=['DELETE'])
@require_auth
def delete_document(document_id):
    """Delete a document from Supabase"""
    try:
        service = SupabaseService()
        
        # Delete document
        result = service.delete_document(document_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_api.route('/referrals/search', methods=['GET'])
@require_auth
def search_referrals():
    """Search referrals by term"""
    try:
        service = SupabaseService()
        
        # Get search term
        search_term = request.args.get('q', '').strip()
        if not search_term:
            return jsonify({'success': False, 'error': 'Search term is required'}), 400
        
        limit = request.args.get('limit', 50, type=int)
        
        # Search referrals
        result = service.search_referrals(search_term, limit)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error searching referrals: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_api.route('/referrals/stats', methods=['GET'])
@require_auth
def get_referral_stats():
    """Get referral statistics"""
    try:
        service = SupabaseService()
        
        # Get stats
        result = service.get_referral_stats()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting referral stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Supabase connection"""
    try:
        service = SupabaseService()
        
        # Try a simple query to test connection
        result = service.get_referrals({'limit': 1})
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Supabase connection is healthy',
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Supabase connection failed',
                'error': result.get('error')
            }), 503
            
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Health check failed',
            'error': str(e)
        }), 503