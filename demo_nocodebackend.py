#!/usr/bin/env python3
"""
NoCodeBackend Integration Demo
Demonstrates how to use the NoCodeBackend integration with Sapyyn
"""

import os
import sys
import json
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nocodebackend_client import NoCodeBackendClient, get_client

def demo_client_usage():
    """Demo the NoCodeBackend client functionality"""
    print("🚀 NoCodeBackend Integration Demo")
    print("=" * 50)
    
    # Note: This demo uses a dummy secret key for demonstration
    # In production, use your actual secret key from environment variables
    dummy_secret = "demo_secret_key_replace_with_real_key"
    
    print("🔧 1. Creating NoCodeBackend Client")
    try:
        client = NoCodeBackendClient(
            secret_key=dummy_secret,
            api_endpoint="https://api.nocodebackend.com/api-docs/?Instance=35557_sapyynreferral_db"
        )
        print(f"   ✅ Client created successfully")
        print(f"   📍 API Endpoint: {client.api_endpoint}")
        print(f"   🌐 Base URL: {client.base_url}")
        print(f"   🏷️  Instance ID: {client.instance_id}")
    except Exception as e:
        print(f"   ❌ Failed to create client: {e}")
        return
    
    print("\n📋 2. Example Patient Data")
    patient_data = {
        "patient_name": "Jane Smith",
        "email": "jane.smith@example.com",
        "phone": "+1-555-0123",
        "date_of_birth": "1985-03-15",
        "medical_history": "No known allergies, previous dental work in 2020",
        "emergency_contact": "John Smith +1-555-0124",
        "created_at": datetime.now().isoformat()
    }
    
    print("   Patient Record:")
    for key, value in patient_data.items():
        print(f"     {key}: {value}")
    
    print("\n🔄 3. Example Referral Data")
    referral_data = {
        "referral_id": "REF-2025-001",
        "patient_name": "Jane Smith",
        "referring_doctor": "Dr. Michael Johnson",
        "target_doctor": "Dr. Sarah Wilson",
        "medical_condition": "Orthodontic consultation",
        "urgency_level": "normal",
        "status": "pending",
        "notes": "Patient requires comprehensive orthodontic evaluation for possible braces",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    print("   Referral Record:")
    for key, value in referral_data.items():
        print(f"     {key}: {value}")
    
    print("\n🌐 4. API Methods Available")
    api_methods = [
        ("create_record(table, data)", "Create a new record in specified table"),
        ("get_record(table, id)", "Retrieve a specific record by ID"),
        ("get_records(table, filters)", "Get multiple records with optional filtering"),
        ("update_record(table, id, data)", "Update an existing record"),
        ("delete_record(table, id)", "Delete a record by ID"),
        ("test_connection()", "Test API connectivity")
    ]
    
    for method, description in api_methods:
        print(f"   📌 {method}")
        print(f"      {description}")
    
    print("\n⚡ 5. Example Usage (would require real API)")
    print("   # Test connection")
    print("   result = client.test_connection()")
    print("   ")
    print("   # Create patient record")
    print("   patient = client.create_record('patients', patient_data)")
    print("   ")
    print("   # Create referral record")
    print("   referral = client.create_record('referrals', referral_data)")
    print("   ")
    print("   # Get all patients")
    print("   patients = client.get_records('patients', limit=50)")
    print("   ")
    print("   # Get specific referral")
    print("   referral = client.get_record('referrals', 'REF-2025-001')")
    
    print("\n🔐 6. Security Best Practices")
    security_tips = [
        "Store secret key in environment variables or repository secrets",
        "Never commit secret keys to version control",
        "Use different keys for development and production",
        "Rotate keys regularly for enhanced security",
        "Monitor API usage and access logs",
        "Implement proper error handling for API failures"
    ]
    
    for i, tip in enumerate(security_tips, 1):
        print(f"   {i}. {tip}")
    
    print("\n📚 7. Integration with Flask App")
    flask_examples = [
        "GET /api/nocodebackend/test - Test API connection",
        "POST /api/nocodebackend/create-patient - Create patient record",
        "GET /api/nocodebackend/patients - Retrieve patients",
        "POST /api/nocodebackend/sync-referral/<id> - Sync referral to NoCodeBackend"
    ]
    
    print("   Available API endpoints:")
    for endpoint in flask_examples:
        print(f"     🔗 {endpoint}")
    
    print("\n🎯 8. Next Steps")
    next_steps = [
        "Get your actual secret key from nocodebackend.com",
        "Set NOCODEBACKEND_SECRET_KEY environment variable",
        "Set NOCODEBACKEND_ENABLED=true in your .env file",
        "Test the connection using the test endpoint",
        "Start syncing your patient referral data",
        "Monitor integration performance and errors"
    ]
    
    for i, step in enumerate(next_steps, 1):
        print(f"   {i}. {step}")
    
    print("\n✨ Demo completed! Ready to integrate with NoCodeBackend.")

if __name__ == "__main__":
    demo_client_usage()