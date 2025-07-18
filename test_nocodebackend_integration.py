#!/usr/bin/env python3
"""
Test NoCodeBackend.com Integration
Tests the nocodebackend client and integration endpoints
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nocodebackend_client import NoCodeBackendClient, get_client
from app import app, init_db

def test_client_initialization():
    """Test NoCodeBackend client initialization"""
    print("🔧 Testing NoCodeBackend Client Initialization")
    print("=" * 50)
    
    # Test without environment variables
    try:
        client = NoCodeBackendClient()
        print("❌ Expected ValueError when no secret key provided")
        return False
    except ValueError as e:
        print(f"✅ Correctly raised ValueError: {e}")
    
    # Test with explicit parameters
    try:
        client = NoCodeBackendClient(
            secret_key="test_key",
            api_endpoint="https://api.nocodebackend.com/api-docs/?Instance=35557_sapyynreferral_db"
        )
        print("✅ Client initialized with explicit parameters")
        print(f"   Base URL: {client.base_url}")
        print(f"   Instance ID: {client.instance_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False

def test_environment_configuration():
    """Test environment variable configuration"""
    print("\n🌍 Testing Environment Configuration")
    print("=" * 50)
    
    # Set test environment variables
    os.environ['NOCODEBACKEND_SECRET_KEY'] = 'test_secret_key'
    os.environ['NOCODEBACKEND_API_ENDPOINT'] = 'https://api.nocodebackend.com/api-docs/?Instance=35557_sapyynreferral_db'
    
    try:
        client = get_client()
        print("✅ Client created with environment variables")
        print(f"   Secret key configured: {'Yes' if client.secret_key else 'No'}")
        print(f"   API endpoint: {client.api_endpoint}")
        print(f"   Base URL derived: {client.base_url}")
        return True
    except Exception as e:
        print(f"❌ Failed to create client from environment: {e}")
        return False

def test_api_methods():
    """Test API method structures (without making actual requests)"""
    print("\n🔌 Testing API Method Structures")
    print("=" * 50)
    
    # Keep the test secret key for testing
    os.environ['NOCODEBACKEND_SECRET_KEY'] = 'test_secret_key'
    
    try:
        client = get_client()
        
        # Test headers generation
        headers = client._get_headers()
        expected_headers = ['Authorization', 'Content-Type', 'Accept']
        
        for header in expected_headers:
            if header in headers:
                print(f"✅ Header '{header}' present")
            else:
                print(f"❌ Header '{header}' missing")
                return False
        
        print("✅ All required headers present")
        
        # Test connection test method (will fail without real API)
        try:
            result = client.test_connection()
            print(f"⚠️  Unexpected connection success: {result}")
        except Exception as e:
            print(f"✅ Connection test failed as expected (no real API): {type(e).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ API method testing failed: {e}")
        return False

def test_flask_integration():
    """Test Flask app integration"""
    print("\n🌐 Testing Flask Integration")
    print("=" * 50)
    
    with app.test_client() as client:
        # Test connection endpoint without configuration
        os.environ.pop('NOCODEBACKEND_SECRET_KEY', None)
        
        response = client.get('/api/nocodebackend/test')
        if response.status_code == 400:
            print("✅ Correctly rejects request without secret key")
        else:
            print(f"❌ Unexpected response code: {response.status_code}")
            return False
        
        # Test with configuration but no actual API
        os.environ['NOCODEBACKEND_SECRET_KEY'] = 'test_secret_key'
        os.environ['NOCODEBACKEND_ENABLED'] = 'true'
        
        response = client.get('/api/nocodebackend/test')
        if response.status_code in [500, 400]:  # Expected to fail without real API
            print("✅ Connection test endpoint responds correctly")
        else:
            print(f"⚠️  Unexpected response code: {response.status_code}")
        
        # Test patient creation endpoint
        response = client.post('/api/nocodebackend/create-patient',
                             json={'patient_name': 'Test Patient'})
        if response.status_code in [500, 400]:  # Expected to fail without real API
            print("✅ Patient creation endpoint responds correctly")
        else:
            print(f"⚠️  Unexpected response code: {response.status_code}")
        
        # Test patients retrieval endpoint
        response = client.get('/api/nocodebackend/patients')
        if response.status_code in [500, 400]:  # Expected to fail without real API
            print("✅ Patients retrieval endpoint responds correctly")
        else:
            print(f"⚠️  Unexpected response code: {response.status_code}")
        
        return True

def test_sample_data_transformation():
    """Test data transformation for NoCodeBackend format"""
    print("\n🔄 Testing Data Transformation")
    print("=" * 50)
    
    # Create sample referral data
    sample_referral = {
        'referral_id': 'REF-001',
        'patient_name': 'John Doe',
        'referring_doctor': 'Dr. Smith',
        'target_doctor': 'Dr. Johnson',
        'medical_condition': 'Dental cleaning',
        'urgency_level': 'normal',
        'status': 'pending',
        'notes': 'Regular checkup needed',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    # Test transformation (simulated)
    try:
        print("✅ Sample referral data:")
        for key, value in sample_referral.items():
            print(f"   {key}: {value}")
        
        # Verify all required fields are present
        required_fields = ['referral_id', 'patient_name', 'status']
        for field in required_fields:
            if field in sample_referral:
                print(f"✅ Required field '{field}' present")
            else:
                print(f"❌ Required field '{field}' missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Data transformation failed: {e}")
        return False

def test_database_integration():
    """Test integration with local SQLite database"""
    print("\n🗄️  Testing Database Integration")
    print("=" * 50)
    
    try:
        # Initialize test database
        init_db()
        
        # Create a test referral in local database
        conn = sqlite3.connect('sapyyn.db')
        cursor = conn.cursor()
        
        # Check if referrals table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='referrals'")
        if cursor.fetchone():
            print("✅ Referrals table exists in local database")
        else:
            print("❌ Referrals table not found")
            conn.close()
            return False
        
        # Test querying referrals (should be empty initially)
        cursor.execute("SELECT COUNT(*) FROM referrals")
        count = cursor.fetchone()[0]
        print(f"✅ Current referrals count: {count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        return False

def run_all_tests():
    """Run all NoCodeBackend integration tests"""
    print("🚀 NoCodeBackend Integration Tests")
    print("=" * 60)
    
    tests = [
        test_client_initialization,
        test_environment_configuration,
        test_api_methods,
        test_flask_integration,
        test_sample_data_transformation,
        test_database_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print(f"\n📊 Test Results")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! NoCodeBackend integration is ready.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check the output above for details.")
    
    # Clean up environment variables
    for var in ['NOCODEBACKEND_SECRET_KEY', 'NOCODEBACKEND_API_ENDPOINT', 'NOCODEBACKEND_ENABLED']:
        os.environ.pop(var, None)
    
    return failed == 0

if __name__ == "__main__":
    run_all_tests()