"""
Tests for NoCodeBackend integration
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import json
from io import BytesIO

# Set environment variables for testing
os.environ['NOCODEBACKEND_SECRET_KEY'] = 'test_secret_key'

from services.nocodebackend_client import NoCodeBackendClient
from utils.nocodebackend_utils import get_referrals_from_nocode

class TestNoCodeBackendClient(unittest.TestCase):
    """Test NoCodeBackend client"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = NoCodeBackendClient('35557_referralomsdb')
    
    def test_build_url(self):
        """Test URL building"""
        url = self.client._build_url('referrals')
        self.assertEqual(url, 'https://api.nocodebackend.com/api/v1/35557_referralomsdb/referrals')
    
    @patch('requests.get')
    def test_get_records(self, mock_get):
        """Test getting records"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {'data': [{'id': '1', 'name': 'Test'}]}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call method
        result = self.client.get_records('referrals')
        
        # Assertions
        self.assertEqual(result, {'data': [{'id': '1', 'name': 'Test'}]})
        mock_get.assert_called_once()
        
        # Check headers
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['Authorization'], 'Token test_secret_key')
    
    @patch('requests.get')
    def test_auth_failure(self, mock_get):
        """Test authentication failure"""
        # Mock response for auth failure
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
        mock_get.return_value = mock_response
        
        # Call method
        result = self.client.get_records('referrals')
        
        # Assertions
        self.assertIn('error', result)
        self.assertIn('401 Unauthorized', result['error'])

if __name__ == '__main__':
    unittest.main()