"""
NoCodeBackend API Client
Client for integrating with nocodebackend.com databases
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class NoCodeBackendClient:
    """Client for interacting with NoCodeBackend API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.nocodebackend.com"):
        """
        Initialize the NoCodeBackend client
        
        Args:
            api_key: Secret key for authentication
            base_url: Base URL for the NoCodeBackend API
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make HTTP request to NoCodeBackend API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request data for POST/PUT requests
            
        Returns:
            API response as dictionary or None on error
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
                
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None


class ReferralOMSDBClient(NoCodeBackendClient):
    """Client for referralomsdb database"""
    
    def __init__(self, api_key: str, instance: str, base_url: str = "https://api.nocodebackend.com"):
        super().__init__(api_key, base_url)
        self.instance = instance
        
    def get_referrals(self, limit: int = 100, offset: int = 0) -> Optional[List[Dict]]:
        """
        Get referrals from the database
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of referral records or None on error
        """
        endpoint = f"api/v1/{self.instance}/referrals"
        params = f"?limit={limit}&offset={offset}"
        
        response = self._make_request('GET', f"{endpoint}{params}")
        return response.get('data', []) if response else None
        
    def get_referral_by_id(self, referral_id: str) -> Optional[Dict]:
        """
        Get a specific referral by ID
        
        Args:
            referral_id: Unique referral identifier
            
        Returns:
            Referral record or None if not found
        """
        endpoint = f"api/v1/{self.instance}/referrals/{referral_id}"
        return self._make_request('GET', endpoint)
        
    def create_referral(self, referral_data: Dict) -> Optional[Dict]:
        """
        Create a new referral record
        
        Args:
            referral_data: Referral information
            
        Returns:
            Created referral record or None on error
        """
        endpoint = f"api/v1/{self.instance}/referrals"
        return self._make_request('POST', endpoint, referral_data)
        
    def update_referral(self, referral_id: str, referral_data: Dict) -> Optional[Dict]:
        """
        Update an existing referral record
        
        Args:
            referral_id: Unique referral identifier
            referral_data: Updated referral information
            
        Returns:
            Updated referral record or None on error
        """
        endpoint = f"api/v1/{self.instance}/referrals/{referral_id}"
        return self._make_request('PUT', endpoint, referral_data)


class WebsiteUploadsClient(NoCodeBackendClient):
    """Client for website_uploads database"""
    
    def __init__(self, api_key: str, instance: str, base_url: str = "https://api.nocodebackend.com"):
        super().__init__(api_key, base_url)
        self.instance = instance
        
    def get_uploads(self, limit: int = 100, offset: int = 0) -> Optional[List[Dict]]:
        """
        Get uploaded files from the database
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of upload records or None on error
        """
        endpoint = f"api/v1/{self.instance}/uploads"
        params = f"?limit={limit}&offset={offset}"
        
        response = self._make_request('GET', f"{endpoint}{params}")
        return response.get('data', []) if response else None
        
    def get_upload_by_id(self, upload_id: str) -> Optional[Dict]:
        """
        Get a specific upload by ID
        
        Args:
            upload_id: Unique upload identifier
            
        Returns:
            Upload record or None if not found
        """
        endpoint = f"api/v1/{self.instance}/uploads/{upload_id}"
        return self._make_request('GET', endpoint)
        
    def create_upload_record(self, upload_data: Dict) -> Optional[Dict]:
        """
        Create a new upload record
        
        Args:
            upload_data: Upload information
            
        Returns:
            Created upload record or None on error
        """
        endpoint = f"api/v1/{self.instance}/uploads"
        return self._make_request('POST', endpoint, upload_data)
        
    def update_upload_record(self, upload_id: str, upload_data: Dict) -> Optional[Dict]:
        """
        Update an existing upload record
        
        Args:
            upload_id: Unique upload identifier
            upload_data: Updated upload information
            
        Returns:
            Updated upload record or None on error
        """
        endpoint = f"api/v1/{self.instance}/uploads/{upload_id}"
        return self._make_request('PUT', endpoint, upload_data)
        
    def get_uploads_by_referral(self, referral_id: str) -> Optional[List[Dict]]:
        """
        Get uploads associated with a specific referral
        
        Args:
            referral_id: Referral identifier
            
        Returns:
            List of upload records for the referral or None on error
        """
        endpoint = f"api/v1/{self.instance}/uploads"
        params = f"?filter[referral_id]={referral_id}"
        
        response = self._make_request('GET', f"{endpoint}{params}")
        return response.get('data', []) if response else None


def create_nocodebackend_clients(config: Dict) -> tuple:
    """
    Factory function to create NoCodeBackend clients
    
    Args:
        config: Configuration dictionary with API credentials
        
    Returns:
        Tuple of (ReferralOMSDBClient, WebsiteUploadsClient)
    """
    api_key = config.get('API_KEY')
    base_url = config.get('BASE_URL', 'https://api.nocodebackend.com')
    referral_instance = config.get('REFERRALOMSDB_INSTANCE')
    uploads_instance = config.get('WEBSITE_UPLOADS_INSTANCE')
    
    if not api_key:
        logger.error("NoCodeBackend API key not configured")
        return None, None
        
    referral_client = ReferralOMSDBClient(api_key, referral_instance, base_url)
    uploads_client = WebsiteUploadsClient(api_key, uploads_instance, base_url)
    
    return referral_client, uploads_client