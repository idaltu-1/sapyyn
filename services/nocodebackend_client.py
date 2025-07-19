"""
NoCodeBackend API client for Sapyyn application
"""

import os
import requests
import logging
from urllib.parse import urljoin
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class NoCodeBackendClient:
    """Client for interacting with NoCodeBackend APIs"""
    
    BASE_URL = "https://api.nocodebackend.com/api/v1/"
    
    def __init__(self, instance_id):
        """Initialize the client
        
        Args:
            instance_id (str): The instance ID for the database
        """
        self.instance_id = instance_id
        self.secret_key = os.environ.get('NOCODEBACKEND_SECRET_KEY')
        
        if not self.secret_key:
            raise ValueError("NOCODEBACKEND_SECRET_KEY environment variable is required")
    
    def _get_headers(self):
        """Get headers for API requests
        
        Returns:
            dict: Headers with authentication
        """
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Token {self.secret_key}'
        }
    
    def _build_url(self, endpoint):
        """Build the full URL for an API endpoint
        
        Args:
            endpoint (str): The API endpoint
            
        Returns:
            str: The full URL
        """
        return urljoin(f"{self.BASE_URL}{self.instance_id}/", endpoint)
    
    def get_records(self, collection, params=None):
        """Get records from a collection
        
        Args:
            collection (str): The collection name
            params (dict, optional): Query parameters
            
        Returns:
            dict: API response
        """
        url = self._build_url(collection)
        
        try:
            response = requests.get(
                url, 
                headers=self._get_headers(), 
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching records from {collection}: {str(e)}")
            return {'error': str(e)}
    
    def create_record(self, collection, data):
        """Create a new record in a collection
        
        Args:
            collection (str): The collection name
            data (dict): The record data
            
        Returns:
            dict: API response
        """
        url = self._build_url(collection)
        
        try:
            response = requests.post(
                url, 
                headers=self._get_headers(), 
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating record in {collection}: {str(e)}")
            return {'error': str(e)}
    
    def update_record(self, collection, record_id, data):
        """Update a record in a collection
        
        Args:
            collection (str): The collection name
            record_id (str): The record ID
            data (dict): The updated data
            
        Returns:
            dict: API response
        """
        url = self._build_url(f"{collection}/{record_id}")
        
        try:
            response = requests.put(
                url, 
                headers=self._get_headers(), 
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating record: {str(e)}")
            return {'error': str(e)}
    
    def upload_file(self, file_data, file_name, content_type):
        """Upload a file to the storage
        
        Args:
            file_data (bytes): The file data
            file_name (str): The file name
            content_type (str): The file content type
            
        Returns:
            dict: API response with file URL
        """
        url = self._build_url("upload")
        
        files = {
            'file': (file_name, file_data, content_type)
        }
        
        headers = {
            'Authorization': f'Token {self.secret_key}'
        }
        
        try:
            response = requests.post(
                url, 
                headers=headers, 
                files=files,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error uploading file: {str(e)}")
            return {'error': str(e)}