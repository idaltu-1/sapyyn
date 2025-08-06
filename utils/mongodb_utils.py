"""
MongoDB utilities for Sapyyn application - replaces NoCodeBackend utilities
"""

from services.mongodb_service import MongoDBService
import logging

logger = logging.getLogger(__name__)

# Initialize MongoDB service
_mongodb_service = None

def get_mongodb_service():
    """Get or create MongoDB service instance"""
    global _mongodb_service
    if _mongodb_service is None:
        _mongodb_service = MongoDBService()
    return _mongodb_service

def get_referrals_from_mongodb(params=None):
    """Get referrals from MongoDB
    
    Args:
        params (dict, optional): Query parameters
        
    Returns:
        dict: API response with referrals
    """
    try:
        service = get_mongodb_service()
        
        # Parse parameters
        query = {}
        limit = 100
        skip = 0
        
        if params:
            # Extract pagination parameters
            limit = int(params.get('limit', 100))
            skip = int(params.get('skip', 0))
            
            # Build query from other parameters
            for key, value in params.items():
                if key not in ['limit', 'skip']:
                    query[key] = value
        
        return service.get_referrals(query, limit, skip)
    except Exception as e:
        logger.error(f"Error getting referrals from MongoDB: {e}")
        return {'success': False, 'error': str(e)}

def create_referral_in_mongodb(referral_data):
    """Create a new referral in MongoDB
    
    Args:
        referral_data (dict): The referral data
        
    Returns:
        dict: API response
    """
    try:
        service = get_mongodb_service()
        return service.create_referral(referral_data)
    except Exception as e:
        logger.error(f"Error creating referral in MongoDB: {e}")
        return {'success': False, 'error': str(e)}

def update_referral_in_mongodb(referral_id, referral_data):
    """Update a referral in MongoDB
    
    Args:
        referral_id (str): The referral ID
        referral_data (dict): The updated referral data
        
    Returns:
        dict: API response
    """
    try:
        service = get_mongodb_service()
        return service.update_referral(referral_id, referral_data)
    except Exception as e:
        logger.error(f"Error updating referral in MongoDB: {e}")
        return {'success': False, 'error': str(e)}

def upload_document_to_mongodb(file_data, file_name, content_type):
    """Upload a document to MongoDB
    
    Args:
        file_data (bytes): The file data
        file_name (str): The file name
        content_type (str): The file content type
        
    Returns:
        dict: API response with file URL
    """
    try:
        service = get_mongodb_service()
        return service.upload_document(file_data, file_name, content_type)
    except Exception as e:
        logger.error(f"Error uploading document to MongoDB: {e}")
        return {'success': False, 'error': str(e)}

def get_documents_from_mongodb(params=None):
    """Get documents from MongoDB
    
    Args:
        params (dict, optional): Query parameters
        
    Returns:
        dict: API response with documents
    """
    try:
        service = get_mongodb_service()
        
        # Parse parameters
        query = {}
        limit = 100
        skip = 0
        
        if params:
            # Extract pagination parameters
            limit = int(params.get('limit', 100))
            skip = int(params.get('skip', 0))
            
            # Build query from other parameters
            for key, value in params.items():
                if key not in ['limit', 'skip']:
                    query[key] = value
        
        return service.get_documents(query, limit, skip)
    except Exception as e:
        logger.error(f"Error getting documents from MongoDB: {e}")
        return {'success': False, 'error': str(e)}

def get_referral_by_id(referral_id):
    """Get a single referral by ID
    
    Args:
        referral_id (str): The referral ID
        
    Returns:
        dict: API response with referral data
    """
    try:
        service = get_mongodb_service()
        return service.get_referral(referral_id)
    except Exception as e:
        logger.error(f"Error getting referral by ID from MongoDB: {e}")
        return {'success': False, 'error': str(e)}

def search_referrals_in_mongodb(search_query, limit=100, skip=0):
    """Search referrals in MongoDB
    
    Args:
        search_query (str): Text to search for
        limit (int): Maximum number of records to return
        skip (int): Number of records to skip
        
    Returns:
        dict: API response with matching referrals
    """
    try:
        service = get_mongodb_service()
        return service.search_referrals(search_query, limit, skip)
    except Exception as e:
        logger.error(f"Error searching referrals in MongoDB: {e}")
        return {'success': False, 'error': str(e)}

def get_stats_from_mongodb():
    """Get database statistics from MongoDB
    
    Returns:
        dict: API response with stats
    """
    try:
        service = get_mongodb_service()
        return service.get_stats()
    except Exception as e:
        logger.error(f"Error getting stats from MongoDB: {e}")
        return {'success': False, 'error': str(e)}