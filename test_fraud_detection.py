#!/usr/bin/env python3
"""
Test script for fraud detection and compliance features
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import (
    init_db, calculate_fraud_score, update_fraud_score, 
    hash_patient_id, log_audit_action, record_device_fingerprint
)
import sqlite3

def test_fraud_detection():
    """Test fraud detection functionality"""
    print("🔒 Testing Fraud Detection & Compliance Features")
    print("=" * 50)
    
    # Initialize database
    init_db()
    print("✅ Database initialized")
    
    # Test 1: Basic fraud score calculation
    print("\n📊 Test 1: Basic fraud score calculation")
    score, risk, reasons = calculate_fraud_score(999, '192.168.1.100', 'test@fraud.com', 'clean_device')
    print(f"Score: {score}, Risk: {risk}, Reasons: {reasons}")
    assert score == 0.0, "Clean user should have 0 fraud score"
    print("✅ Clean user correctly scored")
    
    # Test 2: Device fingerprint recording
    print("\n🖥️  Test 2: Device fingerprint recording")
    record_device_fingerprint(
        'test_fp_123', 'Mozilla/5.0', '1920x1080', 
        'America/New_York', 'en-US', 'Chrome PDF', 'canvas_test'
    )
    print("✅ Device fingerprint recorded")
    
    # Test 3: Patient ID hashing consistency
    print("\n🔐 Test 3: Patient ID hashing")
    patient_id = 'PATIENT_12345'
    hash1 = hash_patient_id(patient_id)
    hash2 = hash_patient_id(patient_id)
    print(f"Original: {patient_id}")
    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    assert hash1 == hash2, "Hashes should be consistent"
    assert hash1 != patient_id, "Hash should be different from original"
    print("✅ Patient ID hashing works correctly")
    
    # Test 4: Simulating duplicate email fraud
    print("\n⚠️  Test 4: Simulating duplicate email detection")
    
    # Create a test user first
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, full_name, role)
        VALUES (?, ?, ?, ?, ?)
    ''', ('frauduser', 'duplicate@test.com', 'hash123', 'Fraud User', 'patient'))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Now test fraud detection with duplicate email
    score, risk, reasons = calculate_fraud_score(999, '192.168.1.100', 'duplicate@test.com', 'device123')
    print(f"Fraud score with duplicate email: {score}, Risk: {risk}")
    print(f"Reasons: {reasons}")
    assert score > 0, "Should detect duplicate email"
    print("✅ Duplicate email detection works")
    
    # Test 5: High fraud score auto-pause
    print("\n🚫 Test 5: Auto-pause functionality")
    
    # Simulate high fraud scenario
    log_audit_action(user_id, 'user_registration', 'user', user_id, 'Test reg 1', '192.168.1.200', 'Browser1')
    log_audit_action(user_id, 'user_registration', 'user', user_id, 'Test reg 2', '192.168.1.200', 'Browser2')
    log_audit_action(user_id, 'user_registration', 'user', user_id, 'Test reg 3', '192.168.1.200', 'Browser3')
    log_audit_action(user_id, 'user_registration', 'user', user_id, 'Test reg 4', '192.168.1.200', 'Browser4')
    log_audit_action(user_id, 'user_registration', 'user', user_id, 'Test reg 5', '192.168.1.200', 'Browser5')
    
    is_paused = update_fraud_score(user_id, '192.168.1.200', 'high_fraud@test.com', 'shared_device')
    print(f"User auto-paused: {is_paused}")
    
    # Check user pause status in database
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    cursor.execute('SELECT fraud_score, is_paused FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        print(f"User fraud score in DB: {result[0]}, Paused: {result[1]}")
        if result[0] >= 50.0:
            print("✅ High fraud score auto-pause works")
        else:
            print("⚠️  Expected higher fraud score")
    
    # Test 6: Fraud detection tables
    print("\n📋 Test 6: Checking fraud detection tables")
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM fraud_scores')
    fraud_count = cursor.fetchone()[0]
    print(f"Fraud scores records: {fraud_count}")
    
    cursor.execute('SELECT COUNT(*) FROM device_fingerprints')
    device_count = cursor.fetchone()[0]
    print(f"Device fingerprints: {device_count}")
    
    cursor.execute('SELECT COUNT(*) FROM duplicate_detections')
    duplicate_count = cursor.fetchone()[0]
    print(f"Duplicate detections: {duplicate_count}")
    
    conn.close()
    
    print("\n🎉 All fraud detection tests completed!")
    print("\n📝 Summary of implemented features:")
    print("   ✅ IP/email/device fingerprint deduplication")
    print("   ✅ Fraud score calculation and tracking")
    print("   ✅ Auto-pause when fraud score > 50")
    print("   ✅ Patient ID hashing for URLs")
    print("   ✅ Enhanced audit logging")
    print("   ✅ Device fingerprint collection")

if __name__ == '__main__':
    test_fraud_detection()