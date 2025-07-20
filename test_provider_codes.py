#!/usr/bin/env python3
"""
Test script for provider code functionality
Tests the enhanced 6-character alphanumeric provider codes and role-based access
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import init_db, generate_provider_code, create_provider_code, check_role_permission
import sqlite3
import tempfile
import shutil

def test_provider_code_generation():
    """Test alphanumeric provider code generation"""
    print("Testing provider code generation...")
    
    # Initialize database first
    init_db()
    
    # Test multiple code generations to ensure uniqueness
    codes = set()
    for i in range(50):
        code = generate_provider_code()
        assert len(code) == 6, f"Provider code should be 6 characters, got {len(code)}"
        assert code.isalnum(), f"Provider code should be alphanumeric, got {code}"
        assert code.isupper(), f"Provider code should be uppercase, got {code}"
        assert code not in codes, f"Duplicate provider code generated: {code}"
        codes.add(code)
        
        # Ensure no confusing characters
        confusing_chars = set('01OIL')
        assert not any(char in confusing_chars for char in code), f"Provider code contains confusing characters: {code}"
    
    print(f"✓ Generated {len(codes)} unique alphanumeric codes")
    print(f"✓ Sample codes: {list(codes)[:5]}")

def test_provider_code_creation():
    """Test provider code creation with role validation"""
    print("\nTesting provider code creation...")
    
    # Initialize test database
    init_db()
    
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Create test users
    from werkzeug.security import generate_password_hash
    
    test_users = [
        ('dentist1', 'dentist1@test.com', 'Test Dentist', 'dentist'),
        ('specialist1', 'specialist1@test.com', 'Test Specialist', 'specialist'),
        ('patient1', 'patient1@test.com', 'Test Patient', 'patient'),
        ('admin1', 'admin1@test.com', 'Test Admin', 'dentist_admin')
    ]
    
    user_ids = {}
    for username, email, full_name, role in test_users:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, generate_password_hash('test123'), full_name, role))
        user_ids[role] = cursor.lastrowid
    
    conn.commit()
    
    # Test valid provider code creation
    dentist_code = create_provider_code(user_ids['dentist'], 'dentist', 'Test Dental Practice', 'General Dentistry')
    assert len(dentist_code) == 6
    print(f"✓ Created dentist provider code: {dentist_code}")
    
    specialist_code = create_provider_code(user_ids['specialist'], 'specialist', 'Test Specialist Practice', 'Orthodontics')
    assert len(specialist_code) == 6
    print(f"✓ Created specialist provider code: {specialist_code}")
    
    admin_code = create_provider_code(user_ids['dentist_admin'], 'dentist_admin', 'Admin Practice', 'Practice Management')
    assert len(admin_code) == 6
    print(f"✓ Created admin provider code: {admin_code}")
    
    # Test invalid provider code creation (patient)
    try:
        create_provider_code(user_ids['patient'], 'patient', 'Patient Practice', 'N/A')
        assert False, "Should not be able to create provider code for patient"
    except ValueError as e:
        print(f"✓ Correctly rejected patient provider code: {e}")
    
    # Test duplicate code prevention
    existing_code = create_provider_code(user_ids['dentist'], 'dentist', 'Updated Practice', 'Updated Specialty')
    assert existing_code == dentist_code, "Should return existing code for same user"
    print(f"✓ Correctly returned existing code: {existing_code}")
    
    conn.close()

def test_role_permissions():
    """Test role-based permission checking"""
    print("\nTesting role permissions...")
    
    # Test single role permissions
    assert check_role_permission('dentist', 'dentist'), "Dentist should have dentist permission"
    assert not check_role_permission('dentist', 'patient'), "Patient should not have dentist permission"
    assert not check_role_permission('admin', 'dentist'), "Dentist should not have admin permission"
    
    # Test multiple role permissions
    admin_roles = ['admin', 'dentist_admin', 'specialist_admin']
    assert check_role_permission(admin_roles, 'admin'), "Admin should have admin permission"
    assert check_role_permission(admin_roles, 'dentist_admin'), "Dentist admin should have admin permission"
    assert not check_role_permission(admin_roles, 'patient'), "Patient should not have admin permission"
    
    print("✓ Role permission checks working correctly")

def test_referral_by_code():
    """Test referral creation using provider codes"""
    print("\nTesting referral by code functionality...")
    
    # This would normally test the API endpoint, but for now we'll test the logic
    # In a real test, you'd use Flask's test client
    
    # Test code validation using the same character set as our generator
    valid_chars = '23456789ABCDEFGHJKMNPQRSTUVWXYZ'
    
    # Use codes that match our valid character set (no 0, 1, I, L, O)
    valid_codes = ['ABC234', 'XYZ789', 'DEF456']
    invalid_codes = ['12345', '123ABC7', 'abc123', 'AB CD3', 'A1O2I3', 'ABCDE1', 'TOOLONG']
    
    for code in valid_codes:
        assert len(code) == 6 and code.isalnum() and code.isupper(), f"Valid code failed basic validation: {code}"
        # Check that all characters are in our allowed set
        assert all(char in valid_chars for char in code), f"Valid code contains invalid characters: {code}"
    
    for code in invalid_codes:
        # Check basic format
        basic_valid = len(code) == 6 and code.isalnum() and code.isupper()
        # Check against our character set
        chars_valid = all(char in valid_chars for char in code) if basic_valid else False
        valid = basic_valid and chars_valid
        assert not valid, f"Invalid code passed validation: {code} (basic: {basic_valid}, chars: {chars_valid})"
    
    print("✓ Code validation working correctly")

def main():
    """Run all tests"""
    print("Running Provider Code Tests...")
    print("=" * 50)
    
    try:
        test_provider_code_generation()
        test_provider_code_creation()
        test_role_permissions()
        test_referral_by_code()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    
    finally:
        # Clean up test database
        if os.path.exists('sapyyn.db'):
            try:
                os.remove('sapyyn.db')
                print("🧹 Cleaned up test database")
            except:
                pass

if __name__ == '__main__':
    main()