#!/usr/bin/env python3
"""
Create sample promotion data for testing PromotionSlot component
"""

import sqlite3
from datetime import datetime, timedelta

def create_sample_promotions():
    """Create sample promotion data for testing"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Clear existing promotions
    cursor.execute('DELETE FROM promotions')
    
    # Sample partner promotions
    partner_promotions = [
        {
            'title': 'Advanced 3D Imaging Solutions',
            'content': 'Get precise diagnosis with our state-of-the-art 3D imaging technology. Special rates for Sapyyn partners.',
            'promotion_type': 'partner',
            'location': 'DASHBOARD_TOP',
            'weight': 3,
            'link_url': 'https://example.com/3d-imaging',
            'image_url': '/static/images/3d-imaging-promo.jpg',
            'partner_name': 'TechDental Solutions'
        },
        {
            'title': 'Premium Dental Insurance Plans',
            'content': 'Comprehensive coverage for your patients. Streamlined approval process for Sapyyn providers.',
            'promotion_type': 'partner',
            'location': 'DASHBOARD_TOP',
            'weight': 2,
            'link_url': 'https://example.com/insurance',
            'image_url': '/static/images/insurance-promo.jpg',
            'partner_name': 'HealthGuard Insurance'
        },
        {
            'title': 'Professional Development Courses',
            'content': 'Enhance your skills with our CE-accredited courses. Special discount for Sapyyn users.',
            'promotion_type': 'partner',
            'location': 'DASHBOARD_TOP',
            'weight': 1,
            'link_url': 'https://example.com/courses',
            'image_url': '/static/images/education-promo.jpg',
            'partner_name': 'DentalEd Academy'
        }
    ]
    
    # Sample house promotions (fallback)
    house_promotions = [
        {
            'title': 'Upgrade to Sapyyn Pro',
            'content': 'Unlock advanced features including analytics dashboard, priority support, and custom branding.',
            'promotion_type': 'house',
            'location': 'DASHBOARD_TOP',
            'weight': 1,
            'link_url': '/pricing',
            'image_url': '/static/images/sapyyn-pro.jpg',
            'partner_name': None
        },
        {
            'title': 'Join Our Webinar Series',
            'content': 'Learn best practices for patient referrals. Free monthly webinars for all Sapyyn users.',
            'promotion_type': 'house',
            'location': 'DASHBOARD_TOP',
            'weight': 1,
            'link_url': '/tutorials',
            'image_url': '/static/images/webinar-promo.jpg',
            'partner_name': None
        }
    ]
    
    # Insert promotions
    all_promotions = partner_promotions + house_promotions
    
    for promo in all_promotions:
        cursor.execute('''
            INSERT INTO promotions 
            (title, content, promotion_type, location, weight, is_active, 
             link_url, image_url, partner_name, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
        ''', (
            promo['title'],
            promo['content'],
            promo['promotion_type'],
            promo['location'],
            promo['weight'],
            promo['link_url'],
            promo['image_url'],
            promo['partner_name'],
            datetime.now().isoformat(),
            (datetime.now() + timedelta(days=30)).isoformat()
        ))
    
    conn.commit()
    
    # Verify insertion
    cursor.execute('SELECT COUNT(*) FROM promotions')
    count = cursor.fetchone()[0]
    print(f'Created {count} sample promotions')
    
    # Show created promotions
    cursor.execute('SELECT title, promotion_type, weight, partner_name FROM promotions ORDER BY promotion_type DESC, weight DESC')
    promotions = cursor.fetchall()
    print('\nCreated promotions:')
    for promo in promotions:
        partner_info = f" (by {promo[3]})" if promo[3] else ""
        print(f"  - {promo[0]} [{promo[1]}, weight: {promo[2]}]{partner_info}")
    
    conn.close()

if __name__ == '__main__':
    create_sample_promotions()