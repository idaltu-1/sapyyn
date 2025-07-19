"""
NoCodeBackend utilities for Sapyyn application
"""

from dotenv import load_dotenv
# Load environment variables early to ensure they're available for client initialization
load_dotenv()

from services.nocodebackend_client import NoCodeBackendClient

# Initialize clients
referrals_client = NoCodeBackendClient('35557_referralomsdb')
uploads_client = NoCodeBackendClient('35557_website_uploads')

def get_referrals_from_nocode(params=None):
    """Get referrals from NoCodeBackend
    
    Args:
        params (dict, optional): Query parameters
        
    Returns:
        dict: API response with referrals
    """
    return referrals_client.get_records('referrals', params)

def create_referral_in_nocode(referral_data):
    """Create a new referral in NoCodeBackend
    
    Args:
        referral_data (dict): The referral data
        
    Returns:
        dict: API response
    """
    return referrals_client.create_record('referrals', referral_data)

def update_referral_in_nocode(referral_id, referral_data):
    """Update a referral in NoCodeBackend
    
    Args:
        referral_id (str): The referral ID
        referral_data (dict): The updated referral data
        
    Returns:
        dict: API response
    """
    return referrals_client.update_record('referrals', referral_id, referral_data)

def upload_document_to_nocode(file_data, file_name, content_type):
    """Upload a document to NoCodeBackend
    
    Args:
        file_data (bytes): The file data
        file_name (str): The file name
        content_type (str): The file content type
        
    Returns:
        dict: API response with file URL
    """
    return uploads_client.upload_file(file_data, file_name, content_type)