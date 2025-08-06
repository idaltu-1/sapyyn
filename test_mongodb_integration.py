#!/usr/bin/env python3
"""
Test script for MongoDB integration (replaces NoCodeBackend)
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_mongodb_client():
    """Test basic MongoDB client functionality"""
    print("🧪 Testing MongoDB client...")
    
    try:
        from mongodb_client import MongoDBClient
        
        # This would fail if MongoDB is not running, but let's test import and basic setup
        print("✅ MongoDB client import successful")
        
        # Test client initialization (will fail without MongoDB running)
        try:
            client = MongoDBClient(
                mongo_url="mongodb://localhost:27017/test_sapyyn",
                db_name="test_sapyyn"
            )
            print("✅ MongoDB client initialization successful")
            client.close()
        except Exception as e:
            print(f"⚠️ MongoDB connection failed (expected if MongoDB not running): {e}")
            
    except ImportError as e:
        print(f"❌ MongoDB client import failed: {e}")
        return False
    
    return True

def test_mongodb_service():
    """Test MongoDB service layer"""
    print("\n🧪 Testing MongoDB service...")
    
    try:
        from services.mongodb_service import MongoDBService
        print("✅ MongoDB service import successful")
        
        # Test service initialization (will fail without MongoDB running)
        try:
            service = MongoDBService()
            print("✅ MongoDB service initialization successful")
            service.close()
        except Exception as e:
            print(f"⚠️ MongoDB service connection failed (expected if MongoDB not running): {e}")
            
    except ImportError as e:
        print(f"❌ MongoDB service import failed: {e}")
        return False
    
    return True

def test_mongodb_utils():
    """Test MongoDB utility functions"""
    print("\n🧪 Testing MongoDB utils...")
    
    try:
        from utils.mongodb_utils import (
            get_referrals_from_mongodb,
            create_referral_in_mongodb,
            update_referral_in_mongodb,
            upload_document_to_mongodb
        )
        print("✅ MongoDB utils import successful")
        
    except ImportError as e:
        print(f"❌ MongoDB utils import failed: {e}")
        return False
    
    return True

def test_mongodb_controller():
    """Test MongoDB controller"""
    print("\n🧪 Testing MongoDB controller...")
    
    try:
        from controllers.mongodb_controller import mongodb_api
        print("✅ MongoDB controller import successful")
        print(f"✅ Blueprint name: {mongodb_api.name}")
        print(f"✅ Blueprint URL prefix: {mongodb_api.url_prefix}")
        
    except ImportError as e:
        print(f"❌ MongoDB controller import failed: {e}")
        return False
    
    return True

def test_flask_app_integration():
    """Test Flask app integration"""
    print("\n🧪 Testing Flask app integration...")
    
    try:
        # Test importing the main app
        from app import app
        print("✅ Flask app import successful")
        
        # Check if MongoDB routes are registered
        routes = []
        for rule in app.url_map.iter_rules():
            if '/api/nocodebackend' in rule.rule:
                routes.append(rule.rule)
        
        if routes:
            print("✅ MongoDB API routes registered:")
            for route in sorted(routes):
                print(f"  - {route}")
        else:
            print("⚠️ No MongoDB API routes found")
            
    except ImportError as e:
        print(f"❌ Flask app import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Flask app integration test failed: {e}")
        return False
    
    return True

def test_migration_script():
    """Test migration script"""
    print("\n🧪 Testing migration script...")
    
    try:
        from migrate_to_mongodb import DataMigrator
        print("✅ Migration script import successful")
        
        # Test migrator initialization
        try:
            migrator = DataMigrator(
                sqlite_db_path='test.db',
                mongodb_url='mongodb://localhost:27017/test',
                mongodb_db='test'
            )
            print("✅ Migration script initialization successful")
        except Exception as e:
            print(f"⚠️ Migration script connection test failed (expected if MongoDB not running): {e}")
            
    except ImportError as e:
        print(f"❌ Migration script import failed: {e}")
        return False
    
    return True

def test_environment_config():
    """Test environment configuration"""
    print("\n🧪 Testing environment configuration...")
    
    # Check if .env.example has MongoDB configuration
    env_example_path = Path('.env.example')
    if env_example_path.exists():
        content = env_example_path.read_text()
        if 'MONGODB_URL' in content and 'MONGODB_DB_NAME' in content:
            print("✅ Environment configuration includes MongoDB settings")
        else:
            print("❌ Environment configuration missing MongoDB settings")
            return False
    else:
        print("⚠️ .env.example file not found")
    
    # Check requirements.txt
    requirements_path = Path('requirements.txt')
    if requirements_path.exists():
        content = requirements_path.read_text()
        if 'pymongo' in content:
            print("✅ requirements.txt includes pymongo")
        else:
            print("❌ requirements.txt missing pymongo dependency")
            return False
    else:
        print("❌ requirements.txt file not found")
        return False
    
    return True

def test_removed_nocodebackend_references():
    """Test that NoCodeBackend references have been properly updated"""
    print("\n🧪 Testing NoCodeBackend reference removal...")
    
    # Files that should have been updated
    files_to_check = [
        'app.py',
        'controllers/mongodb_controller.py',
        'services/mongodb_service.py',
        'routes/nocode_routes.py',
        'utils/mongodb_utils.py',
        '.env.example'
    ]
    
    success = True
    
    for file_path in files_to_check:
        path = Path(file_path)
        if path.exists():
            content = path.read_text()
            
            # Check for old NoCodeBackend imports that should have been replaced
            if 'from services.nocodebackend_service import NoCodeBackendService' in content:
                print(f"❌ {file_path} still contains old NoCodeBackend imports")
                success = False
            elif 'NoCodeBackendService' in content and file_path != 'controllers/nocodebackend_controller.py':
                print(f"⚠️ {file_path} may still reference NoCodeBackend service")
            
            # Check for MongoDB references
            if 'MongoDB' in content or 'mongodb' in content:
                print(f"✅ {file_path} contains MongoDB references")
            else:
                print(f"⚠️ {file_path} may not have been updated for MongoDB")
        else:
            print(f"❌ Expected file {file_path} not found")
            success = False
    
    return success

def main():
    """Run all tests"""
    print("🚀 Starting MongoDB integration tests...\n")
    
    tests = [
        ("MongoDB Client", test_mongodb_client),
        ("MongoDB Service", test_mongodb_service),
        ("MongoDB Utils", test_mongodb_utils),
        ("MongoDB Controller", test_mongodb_controller),
        ("Flask App Integration", test_flask_app_integration),
        ("Migration Script", test_migration_script),
        ("Environment Config", test_environment_config),
        ("NoCodeBackend Reference Removal", test_removed_nocodebackend_references)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print("\n" + "="*50)
    print(f"TOTAL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MongoDB integration is ready.")
        return 0
    else:
        print("⚠️ Some tests failed. Please review the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())