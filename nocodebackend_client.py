#!/usr/bin/env python3
"""
NoCodeBackend.com Database Client
Provides integration with the nocodebackend.com database API for Sapyyn
"""

import os
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any


class NoCodeBackendClient:
    """Client for interacting with nocodebackend.com database API"""
    
    def __init__(self, secret_key: Optional[str] = None, api_endpoint: Optional[str] = None):
        """
        Initialize the client with API credentials
        
        Args:
            secret_key: API secret key (defaults to NOCODEBACKEND_SECRET_KEY env var)
            api_endpoint: API endpoint URL (defaults to NOCODEBACKEND_API_ENDPOINT env var)
        """
        self.secret_key = secret_key or os.environ.get('NOCODEBACKEND_SECRET_KEY')
        self.api_endpoint = api_endpoint or os.environ.get(
            'NOCODEBACKEND_API_ENDPOINT', 
            'https://api.nocodebackend.com/api-docs/?Instance=35557_sapyynreferral_db'
        )
        
        if not self.secret_key:
            raise ValueError("NoCodeBackend secret key is required. Set NOCODEBACKEND_SECRET_KEY environment variable.")
        
        # Extract base API URL from the documentation endpoint
        if 'api-docs' in self.api_endpoint:
            # Convert from docs URL to actual API URL
            self.base_url = self.api_endpoint.replace('/api-docs/', '/api/').split('?')[0]
            self.instance_id = '35557_sapyynreferral_db'
        else:
            self.base_url = self.api_endpoint
            self.instance_id = '35557_sapyynreferral_db'
    
    def _get_headers(self) -> Dict[str, str]:
        """Get standard headers for API requests"""
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request to the API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request payload for POST/PUT requests
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.RequestException as e:
            print(f"NoCodeBackend API request failed: {e}")
            raise
    
    # Example methods for common database operations
    
    def create_record(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new record in the specified table
        
        Args:
            table_name: Name of the table to insert into
            data: Record data as key-value pairs
            
        Returns:
            Created record with ID
        """
        endpoint = f"tables/{table_name}/records"
        return self._make_request('POST', endpoint, data)
    
    def get_record(self, table_name: str, record_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific record by ID
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to retrieve
            
        Returns:
            Record data
        """
        endpoint = f"tables/{table_name}/records/{record_id}"
        return self._make_request('GET', endpoint)
    
    def get_records(self, table_name: str, filters: Optional[Dict] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve records from a table with optional filtering
        
        Args:
            table_name: Name of the table
            filters: Optional filtering criteria
            limit: Maximum number of records to return
            
        Returns:
            List of records
        """
        endpoint = f"tables/{table_name}/records"
        params = {'limit': limit}
        if filters:
            params.update(filters)
        
        # Add query parameters to the endpoint
        if params:
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            endpoint = f"{endpoint}?{query_string}"
            
        return self._make_request('GET', endpoint)
    
    def update_record(self, table_name: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing record
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to update
            data: Updated record data
            
        Returns:
            Updated record
        """
        endpoint = f"tables/{table_name}/records/{record_id}"
        return self._make_request('PUT', endpoint, data)
    
    def delete_record(self, table_name: str, record_id: str) -> bool:
        """
        Delete a record by ID
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to delete
            
        Returns:
            True if successful
        """
        endpoint = f"tables/{table_name}/records/{record_id}"
        self._make_request('DELETE', endpoint)
        return True
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the NoCodeBackend API
        
        Returns:
            Status information about the connection
        """
        try:
            # Try to access a basic endpoint to test connectivity
            endpoint = "health"  # Most APIs have a health check endpoint
            response = self._make_request('GET', endpoint)
            return {
                'status': 'connected',
                'response': response,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


def get_client() -> NoCodeBackendClient:
    """
    Factory function to create a NoCodeBackend client with environment configuration
    
    Returns:
        Configured NoCodeBackendClient instance
    """
    return NoCodeBackendClient()


# Example usage functions
def create_patient_record(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example: Create a patient record in the NoCodeBackend database
    
    Args:
        patient_data: Patient information
        
    Returns:
        Created patient record
    """
    client = get_client()
    return client.create_record('patients', patient_data)


def get_patient_records(filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """
    Example: Retrieve patient records from the NoCodeBackend database
    
    Args:
        filters: Optional filtering criteria
        
    Returns:
        List of patient records
    """
    client = get_client()
    return client.get_records('patients', filters)


def sync_referral_to_nocodebackend(referral_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example: Sync a referral from the local database to NoCodeBackend
    
    Args:
        referral_data: Referral information from local database
        
    Returns:
        Created referral record in NoCodeBackend
    """
    client = get_client()
    
    # Transform local referral data for NoCodeBackend format
    nocodebackend_data = {
        'referral_id': referral_data.get('referral_id'),
        'patient_name': referral_data.get('patient_name'),
        'referring_doctor': referral_data.get('referring_doctor'),
        'target_doctor': referral_data.get('target_doctor'),
        'medical_condition': referral_data.get('medical_condition'),
        'urgency_level': referral_data.get('urgency_level', 'normal'),
        'status': referral_data.get('status', 'pending'),
        'notes': referral_data.get('notes', ''),
        'created_at': referral_data.get('created_at'),
        'updated_at': referral_data.get('updated_at')
    }
    
    return client.create_record('referrals', nocodebackend_data)


if __name__ == "__main__":
    """Simple test when running the module directly"""
    try:
        client = get_client()
        result = client.test_connection()
        print(f"NoCodeBackend connection test: {result}")
    except Exception as e:
        print(f"Failed to test NoCodeBackend connection: {e}")