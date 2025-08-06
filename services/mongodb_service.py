"""
MongoDB integration service for Sapyyn application - replaces NoCodeBackend service
"""

import os
from mongodb_client import MongoDBClient
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class MongoDBService:
    """Service for MongoDB integration - replaces NoCodeBackendService"""
    
    def __init__(self):
        """Initialize the service with MongoDB client"""
        try:
            self.client = MongoDBClient()
            logger.info("MongoDB service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB service: {e}")
            raise
    
    def get_referrals(self, query: Optional[Dict[str, Any]] = None, limit: int = 100, skip: int = 0) -> Dict[str, Any]:
        """Get referrals from MongoDB
        
        Args:
            query (dict, optional): Query parameters
            limit (int, optional): Maximum number of records to return
            skip (int, optional): Number of records to skip
            
        Returns:
            dict: Response with referrals
        """
        try:
            return self.client.get_referrals(query, limit, skip)
        except Exception as e:
            logger.error(f"Error getting referrals: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_referral(self, referral_id: str) -> Dict[str, Any]:
        """Get a single referral by ID
        
        Args:
            referral_id (str): The referral ID
            
        Returns:
            dict: Response with referral data
        """
        try:
            return self.client.get_record("referrals", referral_id)
        except Exception as e:
            logger.error(f"Error getting referral {referral_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_referral(self, referral_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new referral in MongoDB
        
        Args:
            referral_data (dict): The referral data
            
        Returns:
            dict: Response with created referral
        """
        try:
            return self.client.create_referral(referral_data)
        except Exception as e:
            logger.error(f"Error creating referral: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_referral(self, referral_id: str, referral_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a referral in MongoDB
        
        Args:
            referral_id (str): The referral ID
            referral_data (dict): The updated referral data
            
        Returns:
            dict: Response with updated referral
        """
        try:
            return self.client.update_referral(referral_id, referral_data)
        except Exception as e:
            logger.error(f"Error updating referral {referral_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_referral(self, referral_id: str) -> Dict[str, Any]:
        """Delete a referral from MongoDB
        
        Args:
            referral_id (str): The referral ID
            
        Returns:
            dict: Response with deletion result
        """
        try:
            return self.client.delete_record("referrals", referral_id)
        except Exception as e:
            logger.error(f"Error deleting referral {referral_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def upload_document(self, file_data: bytes, file_name: str, content_type: str, 
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Upload a document to MongoDB
        
        Args:
            file_data (bytes): The file data
            file_name (str): The file name
            content_type (str): The file content type
            metadata (dict, optional): Additional metadata
            
        Returns:
            dict: Response with uploaded document info
        """
        try:
            # Upload file using GridFS
            file_result = self.client.upload_file(file_data, file_name, content_type, metadata)
            
            if file_result['success']:
                # Create document record in documents collection
                document_data = {
                    'file_id': file_result['data']['_id'],
                    'filename': file_name,
                    'content_type': content_type,
                    'file_size': len(file_data),
                    'metadata': metadata or {}
                }
                
                doc_result = self.client.create_document(document_data)
                
                if doc_result['success']:
                    # Add file info to document record
                    doc_result['data']['file_info'] = file_result['data']
                
                return doc_result
            else:
                return file_result
                
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_documents(self, query: Optional[Dict[str, Any]] = None, limit: int = 100, skip: int = 0) -> Dict[str, Any]:
        """Get documents from MongoDB
        
        Args:
            query (dict, optional): Query parameters
            limit (int, optional): Maximum number of records to return
            skip (int, optional): Number of records to skip
            
        Returns:
            dict: Response with documents
        """
        try:
            return self.client.get_documents(query, limit, skip)
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get a single document by ID
        
        Args:
            document_id (str): The document ID
            
        Returns:
            dict: Response with document data
        """
        try:
            return self.client.get_record("documents", document_id)
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_document_file(self, file_id: str) -> Dict[str, Any]:
        """Get file data from GridFS
        
        Args:
            file_id (str): The file ID
            
        Returns:
            dict: Response with file data and metadata
        """
        try:
            return self.client.get_file(file_id)
        except Exception as e:
            logger.error(f"Error getting file {file_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def link_document_to_referral(self, document_id: str, referral_id: str) -> Dict[str, Any]:
        """Link a document to a referral
        
        Args:
            document_id (str): The document ID
            referral_id (str): The referral ID
            
        Returns:
            dict: Response with update result
        """
        try:
            # Update the document with the referral ID
            update_data = {'referral_id': referral_id}
            return self.client.update_record("documents", document_id, update_data)
        except Exception as e:
            logger.error(f"Error linking document {document_id} to referral {referral_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_referral_documents(self, referral_id: str) -> Dict[str, Any]:
        """Get all documents linked to a referral
        
        Args:
            referral_id (str): The referral ID
            
        Returns:
            dict: Response with referral documents
        """
        try:
            query = {'referral_id': referral_id}
            return self.client.get_documents(query)
        except Exception as e:
            logger.error(f"Error getting documents for referral {referral_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def search_referrals(self, search_query: str, limit: int = 100, skip: int = 0) -> Dict[str, Any]:
        """Search referrals by text
        
        Args:
            search_query (str): Text to search for
            limit (int, optional): Maximum number of records to return
            skip (int, optional): Number of records to skip
            
        Returns:
            dict: Response with matching referrals
        """
        try:
            # MongoDB text search query
            query = {
                '$or': [
                    {'patient_name': {'$regex': search_query, '$options': 'i'}},
                    {'referring_doctor': {'$regex': search_query, '$options': 'i'}},
                    {'target_doctor': {'$regex': search_query, '$options': 'i'}},
                    {'medical_condition': {'$regex': search_query, '$options': 'i'}},
                    {'notes': {'$regex': search_query, '$options': 'i'}}
                ]
            }
            return self.client.get_referrals(query, limit, skip)
        except Exception as e:
            logger.error(f"Error searching referrals: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_referrals_by_status(self, status: str, limit: int = 100, skip: int = 0) -> Dict[str, Any]:
        """Get referrals by status
        
        Args:
            status (str): The status to filter by
            limit (int, optional): Maximum number of records to return
            skip (int, optional): Number of records to skip
            
        Returns:
            dict: Response with referrals matching status
        """
        try:
            query = {'status': status}
            return self.client.get_referrals(query, limit, skip)
        except Exception as e:
            logger.error(f"Error getting referrals by status {status}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_user_referrals(self, user_id: str, limit: int = 100, skip: int = 0) -> Dict[str, Any]:
        """Get referrals for a specific user
        
        Args:
            user_id (str): The user ID
            limit (int, optional): Maximum number of records to return
            skip (int, optional): Number of records to skip
            
        Returns:
            dict: Response with user's referrals
        """
        try:
            query = {'user_id': user_id}
            return self.client.get_referrals(query, limit, skip)
        except Exception as e:
            logger.error(f"Error getting referrals for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics
        
        Returns:
            dict: Response with database stats
        """
        try:
            stats = {}
            
            # Get referral counts by status
            referral_stats = {}
            statuses = ['pending', 'completed', 'cancelled', 'in_progress']
            
            for status in statuses:
                result = self.client.get_referrals({'status': status}, limit=0)
                if result['success']:
                    referral_stats[status] = result['total']
            
            # Get total referrals
            all_referrals = self.client.get_referrals({}, limit=0)
            if all_referrals['success']:
                referral_stats['total'] = all_referrals['total']
            
            # Get document count
            all_documents = self.client.get_documents({}, limit=0)
            document_count = all_documents['total'] if all_documents['success'] else 0
            
            stats = {
                'referrals': referral_stats,
                'documents': {'total': document_count}
            }
            
            return {'success': True, 'data': stats}
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'success': False, 'error': str(e)}
    
    def close(self):
        """Close MongoDB connection"""
        if hasattr(self, 'client'):
            self.client.close()