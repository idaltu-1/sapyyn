#!/usr/bin/env python3
"""
Cron job to expire promotions past their end date
Run this script daily to automatically deactivate expired promotions
"""

import sqlite3
from datetime import datetime

def expire_promotions():
    """Deactivate promotions that have passed their end date"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Get current date
    current_date = datetime.now().isoformat()
    
    # Find active promotions past their end date
    cursor.execute('''
        SELECT id, title FROM promotions 
        WHERE is_active = TRUE AND end_date < ?
    ''', (current_date,))
    
    expired_promotions = cursor.fetchall()
    
    # Deactivate expired promotions
    if expired_promotions:
        cursor.execute('''
            UPDATE promotions 
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP 
            WHERE is_active = TRUE AND end_date < ?
        ''', (current_date,))
        
        conn.commit()
        
        # Log expired promotions
        print(f"Expired {len(expired_promotions)} promotions:")
        for promo in expired_promotions:
            print(f"  - ID: {promo[0]}, Title: {promo[1]}")
    else:
        print("No promotions to expire")
    
    conn.close()

if __name__ == "__main__":
    expire_promotions()