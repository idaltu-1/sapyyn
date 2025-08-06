"""
NoCodeBackend integration service for Sapyyn application
"""

import os
from services.nocodebackend_client import NoCodeBackendClient
import logging

logger = logging.getLogger(__name__)

class NoCodeBackendService:
    """Service for NoCodeBackend integration"""
    
    def __init__(self):
        """Initialize the service with clients for both databases"""
        self.referral_client = NoCodeBackendClient(
            os.environ.get('NOCODEBACKEND_REFERRAL_INSTANCE', '35557_referralomsdb')
        )
        
        self.uploads_client = NoCodeBackendClient(
            os.environ.get('NOCODEBACKEND_UPLOADS_INSTANCE', '35557_website_uploads')
        )
    
    def get_referrals(self, query=None, limit=100, skip=0):
        """Get referrals from the referral database
        
        Args:
            query (dict, optional): Query parameters
            limit (int, optional): Maximum number of records to return
            skip (int, optional): Number of records to skip
            
        Returns:
            dict: API response with referrals
        """
        return self.referral_client.get_records('referrals', query, limit, skip)
    
    def create_referral(self, referral_data):
        """Create a new referral in the referral database
        
        Args:
            referral_data (dict): The referral data
            
        Returns:
            dict: API response
        """
        return self.referral_client.create_record('referrals', referral_data)
    
    def update_referral(self, referral_id, referral_data):
        """Update a referral in the referral database
        
        Args:
            referral_id (str): The referral ID
            referral_data (dict): The updated referral data
            
        Returns:
            dict: API response
        """
        return self.referral_client.update_record('referrals', referral_id, referral_data)
    
    def upload_document(self, file_data, file_name, content_type):
        """Upload a document to the uploads database
        
        Args:
            file_data (bytes): The file data
            file_name (str): The file name
            content_type (str): The file content type
            
        Returns:
            dict: API response with file URL
        """
        return self.uploads_client.upload_file(file_data, file_name, content_type)
    
    def get_documents(self, query=None, limit=100, skip=0):
        """Get documents from the uploads database
        
        Args:
            query (dict, optional): Query parameters
            limit (int, optional): Maximum number of records to return
            skip (int, optional): Number of records to skip
            
        Returns:
            dict: API response with documents
        """
        return self.uploads_client.get_records('documents', query, limit, skip)
    
    def link_document_to_referral(self, document_id, referral_id):
        """Link a document to a referral
        
        Args:
            document_id (str): The document ID
            referral_id (str): The referral ID
            
        Returns:
            dict: API response
        """
        # Get the document
        document = self.uploads_client.get_records('documents', {'_id': document_id})
        if 'error' in document:
            return document
        
        # Update the document with the referral ID
        document_data = document.get('data', [])[0] if document.get('data') else {}
        document_data['referral_id'] = referral_id
        
        return self.uploads_client.update_record('documents', document_id, document_data)