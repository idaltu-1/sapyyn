#!/usr/bin/env python3
"""
Demo data setup script for Sapyyn Patient Referral System
"""
import sqlite3
from werkzeug.security import generate_password_hash

def create_demo_users():
    """Create demo users for testing"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Demo users
    demo_users = [
        {
            'username': 'doctor1',
            'email': 'doctor@sapyyn.com',
            'password': 'password123',
            'full_name': 'Dr. Sarah Johnson',
            'role': 'doctor'
        },
        {
            'username': 'patient1',
            'email': 'patient@sapyyn.com',
            'password': 'password123',
            'full_name': 'John Smith',
            'role': 'patient'
        },
        {
            'username': 'admin1',
            'email': 'admin@sapyyn.com',
            'password': 'password123',
            'full_name': 'Admin User',
            'role': 'admin'
        }
    ]
    
    for user in demo_users:
        try:
            password_hash = generate_password_hash(user['password'])
            cursor.execute('''
                INSERT OR IGNORE INTO users (username, email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (user['username'], user['email'], password_hash, user['full_name'], user['role']))
            print(f"Created user: {user['username']} ({user['role']})")
        except Exception as e:
            print(f"Error creating user {user['username']}: {e}")
    
    conn.commit()
    conn.close()
    print("Demo users created successfully!")

if __name__ == '__main__':
    create_demo_users()