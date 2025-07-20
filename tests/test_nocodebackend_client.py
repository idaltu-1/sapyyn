import os
import pytest
from unittest.mock import patch

from nocodebackend_client import NoCodeBackendClient


def test_create_referral_sends_correct_headers(monkeypatch):
    # Set environment variables for testing
    os.environ['NOCODEBACKEND_SECRET_KEY'] = 'testkey'
    os.environ['NOCODEBACKEND_REFERRAL_INSTANCE'] = 'ref_instance'
    client = NoCodeBackendClient()
    data = {'name': 'John Doe'}
    # Mock requests.post to prevent real HTTP calls
    with patch('nocodebackend_client.requests.post') as mock_post:
        mock_response = mock_post.return_value
        mock_response.json.return_value = {'id': 1}
        mock_response.raise_for_status.return_value = None

        client.create_referral(data)

        # Ensure post was called once
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        # Validate headers include Authorization with Bearer token
        assert kwargs['headers']['Authorization'] == 'Bearer testkey'
        # Validate Instance param uses referral instance
        assert kwargs['params']['Instance'] == 'ref_instance'


def test_create_upload_sends_correct_headers(monkeypatch):
    os.environ['NOCODEBACKEND_SECRET_KEY'] = 'testkey'
    os.environ['NOCODEBACKEND_UPLOADS_INSTANCE'] = 'upload_instance'
    client = NoCodeBackendClient()
    data = {'filename': 'test.txt'}
    with patch('nocodebackend_client.requests.post') as mock_post:
        mock_response = mock_post.return_value
        mock_response.json.return_value = {'id': 2}
        mock_response.raise_for_status.return_value = None

        client.create_upload(data)

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs['headers']['Authorization'] == 'Bearer testkey'
        assert kwargs['params']['Instance'] == 'upload_instance'
