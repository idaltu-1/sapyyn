#!/usr/bin/env python3
"""
Test script for NoCodeBackend integration
"""

import os
import sys
import json
import requests

# Set the API key for testing
os.environ['NOCODEBACKEND_API_KEY'] = '18f1e232c27cfc1da36cbb74cc922b0a9f1fb385428ca769524c83102bf2'

# Import the app after setting the environment variable
from nocodebackend_client import create_nocodebackend_clients, ReferralOMSDBClient, WebsiteUploadsClient

def test_nocodebackend_integration():
    """Test the NoCodeBackend integration"""
    
    print("Testing NoCodeBackend Integration...")
    print("=" * 50)
    
    # Test configuration
    config = {
        'API_KEY': os.environ.get('NOCODEBACKEND_API_KEY'),
        'BASE_URL': 'https://api.nocodebackend.com',
        'REFERRALOMSDB_INSTANCE': '35557_referralomsdb',
        'WEBSITE_UPLOADS_INSTANCE': '35557_website_uploads'
    }
    
    print(f"API Key set: {'Yes' if config['API_KEY'] else 'No'}")
    print(f"Base URL: {config['BASE_URL']}")
    print(f"Referral Instance: {config['REFERRALOMSDB_INSTANCE']}")
    print(f"Uploads Instance: {config['WEBSITE_UPLOADS_INSTANCE']}")
    print()
    
    # Create clients
    referral_client, uploads_client = create_nocodebackend_clients(config)
    
    if not referral_client or not uploads_client:
        print("❌ Failed to create NoCodeBackend clients")
        return False
        
    print("✅ NoCodeBackend clients created successfully")
    
    # Test referral client connection
    print("\nTesting Referral Database Connection...")
    try:
        referrals = referral_client.get_referrals(limit=1)
        if referrals is not None:
            print(f"✅ Connected to referralomsdb - returned {len(referrals)} records")
            if referrals:
                print(f"Sample referral keys: {list(referrals[0].keys()) if referrals else 'No data'}")
        else:
            print("⚠️  Connected but no data returned (may be empty or API error)")
    except Exception as e:
        print(f"❌ Failed to connect to referralomsdb: {e}")
    
    # Test uploads client connection
    print("\nTesting Uploads Database Connection...")
    try:
        uploads = uploads_client.get_uploads(limit=1)
        if uploads is not None:
            print(f"✅ Connected to website_uploads - returned {len(uploads)} records")
            if uploads:
                print(f"Sample upload keys: {list(uploads[0].keys()) if uploads else 'No data'}")
        else:
            print("⚠️  Connected but no data returned (may be empty or API error)")
    except Exception as e:
        print(f"❌ Failed to connect to website_uploads: {e}")
    
    print("\nTesting complete!")
    return True

def test_api_endpoints():
    """Test the Flask API endpoints"""
    print("\nTesting Flask API Endpoints...")
    print("=" * 50)
    
    # Import app with the environment variable set
    import app
    
    # Test the status endpoint
    with app.app.test_client() as client:
        print("Testing /api/nocodebackend/status...")
        response = client.get('/api/nocodebackend/status')
        
        if response.status_code == 200:
            data = response.get_json()
            print("✅ Status endpoint working")
            print(f"Status: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
            
        print("\nTesting /api/nocodebackend/referrals...")
        response = client.get('/api/nocodebackend/referrals?limit=1')
        
        if response.status_code == 200:
            data = response.get_json()
            print("✅ Referrals endpoint working")
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Referrals endpoint failed: {response.status_code}")
            print(f"Response: {response.get_data(as_text=True)}")
            
        print("\nTesting /api/nocodebackend/uploads...")
        response = client.get('/api/nocodebackend/uploads?limit=1')
        
        if response.status_code == 200:
            data = response.get_json()
            print("✅ Uploads endpoint working")
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Uploads endpoint failed: {response.status_code}")
            print(f"Response: {response.get_data(as_text=True)}")

if __name__ == '__main__':
    print("NoCodeBackend Integration Test")
    print("=" * 50)
    
    # Test the integration
    success = test_nocodebackend_integration()
    
    if success:
        test_api_endpoints()
    else:
        print("❌ Basic integration test failed")
        sys.exit(1)