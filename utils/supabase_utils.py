"""
Supabase utilities for Sapyyn application.
This module replaces the NoCodeBackend utilities.
"""

from services.supabase_service import SupabaseService

# Initialize service lazily to avoid requiring env vars at import time
_supabase_service = None

def get_supabase_service():
    """Get or create Supabase service instance"""
    global _supabase_service
    if _supabase_service is None:
        _supabase_service = SupabaseService()
    return _supabase_service

def get_referrals_from_supabase(params=None):
    """Get referrals from Supabase
    
    Args:
        params (dict, optional): Query parameters
        
    Returns:
        dict: API response with referrals
    """
    service = get_supabase_service()
    limit = 100
    skip = 0
    
    if params:
        limit = params.pop('limit', 100)
        skip = params.pop('skip', 0)
    
    return service.get_referrals(params, limit, skip)

def create_referral_in_supabase(referral_data):
    """Create a new referral in Supabase
    
    Args:
        referral_data (dict): The referral data
        
    Returns:
        dict: API response
    """
    service = get_supabase_service()
    return service.create_referral(referral_data)

def update_referral_in_supabase(referral_id, referral_data):
    """Update a referral in Supabase
    
    Args:
        referral_id (str): The referral ID
        referral_data (dict): The updated referral data
        
    Returns:
        dict: API response
    """
    service = get_supabase_service()
    return service.update_referral(referral_id, referral_data)

def upload_document_to_supabase(file_data, file_name, content_type):
    """Upload a document to Supabase
    
    Args:
        file_data (bytes): The file data
        file_name (str): The file name
        content_type (str): The file content type
        
    Returns:
        dict: API response with file URL
    """
    service = get_supabase_service()
    return service.upload_document(file_data, file_name, content_type)

def search_referrals_in_supabase(search_term, limit=50):
    """Search referrals by term in Supabase
    
    Args:
        search_term (str): The search term
        limit (int): Maximum number of results
        
    Returns:
        dict: API response with matching referrals
    """
    service = get_supabase_service()
    return service.search_referrals(search_term, limit)

def get_referral_stats_from_supabase():
    """Get referral statistics from Supabase
    
    Returns:
        dict: Statistics data
    """
    service = get_supabase_service()
    return service.get_referral_stats()

def get_documents_from_supabase(params=None):
    """Get documents from Supabase
    
    Args:
        params (dict, optional): Query parameters
        
    Returns:
        dict: API response with documents
    """
    service = get_supabase_service()
    limit = 100
    skip = 0
    
    if params:
        limit = params.pop('limit', 100)
        skip = params.pop('skip', 0)
    
    return service.get_documents(params, limit, skip)

def delete_document_from_supabase(document_id):
    """Delete a document from Supabase
    
    Args:
        document_id (str): The document ID
        
    Returns:
        dict: API response
    """
    service = get_supabase_service()
    return service.delete_document(document_id)

def link_document_to_referral_in_supabase(document_id, referral_id):
    """Link a document to a referral in Supabase
    
    Args:
        document_id (str): The document ID
        referral_id (str): The referral ID
        
    Returns:
        dict: API response
    """
    service = get_supabase_service()
    return service.link_document_to_referral(document_id, referral_id)