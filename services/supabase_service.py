"""
Supabase integration service for Sapyyn application.
This service replaces the NoCodeBackend functionality with Supabase.
"""

import os
import sys
import logging

# Add the current directory to Python path to import supabase_client
sys.path.append(os.path.dirname(os.path.abspath(__file__ + '/..')))

from supabase_client import SupabaseClient

logger = logging.getLogger(__name__)

class SupabaseService:
    """Service for Supabase integration - replaces NoCodeBackendService"""
    
    def __init__(self):
        """Initialize the service with Supabase client"""
        self.client = SupabaseClient()
        
        # Storage buckets configuration
        self.documents_bucket = os.environ.get('SUPABASE_DOCUMENTS_BUCKET', 'documents')
        self.uploads_bucket = os.environ.get('SUPABASE_UPLOADS_BUCKET', 'uploads')
    
    def get_referrals(self, query=None, limit=100, skip=0):
        """Get referrals from Supabase database
        
        Args:
            query (dict, optional): Query parameters
            limit (int, optional): Maximum number of records to return
            skip (int, optional): Number of records to skip
            
        Returns:
            dict: API response with referrals
        """
        params = {}
        if query:
            params.update(query)
        if limit:
            params['limit'] = limit
        if skip:
            params['offset'] = skip
            
        return self.client.get_referrals(params)
    
    def create_referral(self, referral_data):
        """Create a new referral in Supabase database
        
        Args:
            referral_data (dict): The referral data
            
        Returns:
            dict: API response
        """
        return self.client.create_referral(referral_data)
    
    def update_referral(self, referral_id, referral_data):
        """Update a referral in Supabase database
        
        Args:
            referral_id (str): The referral ID
            referral_data (dict): The updated referral data
            
        Returns:
            dict: API response
        """
        return self.client.update_referral(referral_id, referral_data)
    
    def upload_document(self, file_data, file_name, content_type):
        """Upload a document to Supabase Storage
        
        Args:
            file_data (bytes): The file data
            file_name (str): The file name
            content_type (str): The file content type
            
        Returns:
            dict: API response with file URL
        """
        # Upload file to storage bucket
        upload_result = self.client.upload_document(file_name, file_data, content_type)
        
        if upload_result.get('success'):
            # Create document record in database
            document_data = {
                'file_name': file_name,
                'file_path': upload_result['data']['path'],
                'file_url': upload_result['data']['public_url'],
                'content_type': content_type,
                'file_size': len(file_data)
            }
            
            # Store document metadata in database
            doc_result = self.client.create_document(document_data)
            
            if doc_result.get('success'):
                # Return combined result
                return {
                    'success': True,
                    'data': {
                        **upload_result['data'],
                        'document_id': doc_result['data']['id']
                    },
                    'message': 'Document uploaded and recorded successfully'
                }
            else:
                logger.warning(f"File uploaded but failed to create document record: {doc_result.get('error')}")
                return upload_result
        
        return upload_result
    
    def get_documents(self, query=None, limit=100, skip=0):
        """Get documents from Supabase database
        
        Args:
            query (dict, optional): Query parameters
            limit (int, optional): Maximum number of records to return
            skip (int, optional): Number of records to skip
            
        Returns:
            dict: API response with documents
        """
        params = {}
        if query:
            params.update(query)
        if limit:
            params['limit'] = limit
        if skip:
            params['offset'] = skip
            
        return self.client.get_documents(params)
    
    def link_document_to_referral(self, document_id, referral_id):
        """Link a document to a referral
        
        Args:
            document_id (str): The document ID
            referral_id (str): The referral ID
            
        Returns:
            dict: API response
        """
        # Update the document record with referral ID
        return self.client.update_record('documents', document_id, {
            'referral_id': referral_id
        })

    def get_referral_documents(self, referral_id):
        """Get all documents linked to a specific referral
        
        Args:
            referral_id (str): The referral ID
            
        Returns:
            dict: API response with documents
        """
        return self.get_documents({'referral_id': referral_id})

    def delete_document(self, document_id):
        """Delete a document from both database and storage
        
        Args:
            document_id (str): The document ID
            
        Returns:
            dict: API response
        """
        # First get document details
        doc_result = self.client.get_records('documents', {'id': document_id})
        
        if not doc_result.get('success') or not doc_result.get('data'):
            return {'success': False, 'error': 'Document not found'}
        
        document = doc_result['data'][0]
        file_path = document.get('file_path')
        
        # Delete from storage if file_path exists
        if file_path:
            self.client.delete_file(self.documents_bucket, file_path)
        
        # Delete from database
        return self.client.delete_record('documents', document_id)

    def search_referrals(self, search_term, limit=50):
        """Search referrals by patient name, doctor, or condition
        
        Args:
            search_term (str): The search term
            limit (int): Maximum number of results
            
        Returns:
            dict: API response with matching referrals
        """
        # This is a simplified search - in production you might use full-text search
        # For now, we'll search across multiple fields using OR conditions
        try:
            result = self.client.client.table('referrals').select('*').or_(
                f'patient_name.ilike.%{search_term}%,'
                f'referring_doctor.ilike.%{search_term}%,'
                f'target_doctor.ilike.%{search_term}%,'
                f'medical_condition.ilike.%{search_term}%'
            ).limit(limit).execute()
            
            return {
                'success': True,
                'data': result.data,
                'count': len(result.data) if result.data else 0
            }
        except Exception as e:
            logger.error(f"Error searching referrals: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_referral_stats(self):
        """Get statistics about referrals
        
        Returns:
            dict: Statistics data
        """
        try:
            # Get total referrals count
            total_result = self.client.client.table('referrals').select('id', count='exact').execute()
            total_count = total_result.count if hasattr(total_result, 'count') else 0
            
            # Get pending referrals count  
            pending_result = self.client.client.table('referrals').select('id', count='exact').eq('status', 'pending').execute()
            pending_count = pending_result.count if hasattr(pending_result, 'count') else 0
            
            # Get completed referrals count
            completed_result = self.client.client.table('referrals').select('id', count='exact').eq('status', 'completed').execute()
            completed_count = completed_result.count if hasattr(completed_result, 'count') else 0
            
            return {
                'success': True,
                'data': {
                    'total_referrals': total_count,
                    'pending_referrals': pending_count,
                    'completed_referrals': completed_count,
                    'completion_rate': (completed_count / total_count * 100) if total_count > 0 else 0
                }
            }
        except Exception as e:
            logger.error(f"Error getting referral stats: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }