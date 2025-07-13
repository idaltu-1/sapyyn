#!/usr/bin/env python3
"""
Initialize Rewards System with Sample Data
This script creates sample reward programs, achievements, and demo rewards
"""
import sqlite3
from datetime import datetime, timedelta

def init_rewards_sample_data():
    """Initialize the rewards system with sample data"""
    conn = sqlite3.connect('sapyyn.db')
    cursor = conn.cursor()
    
    # Sample Reward Program
    cursor.execute('''
        INSERT OR IGNORE INTO reward_programs 
        (name, description, program_type, status, start_date, created_by, compliance_notes, legal_language)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Professional Referral Excellence Program',
        'A comprehensive reward program designed to recognize healthcare professionals who make quality patient referrals while maintaining the highest standards of medical ethics and compliance.',
        'referral',
        'active',
        datetime.now().strftime('%Y-%m-%d'),
        1,  # Admin user
        '''This program has been reviewed for compliance with:
- HIPAA Privacy and Security Rules
- Stark Law Anti-Kickback Provisions  
- AMA Code of Medical Ethics
- State medical board regulations

All rewards are based on referral quality and appropriateness, not volume or financial value. Legal review completed on ''' + datetime.now().strftime('%Y-%m-%d'),
        '''PROFESSIONAL REFERRAL EXCELLENCE PROGRAM
TERMS AND CONDITIONS

COMPLIANCE NOTICE:
This referral reward program is designed to recognize and appreciate healthcare professionals who make appropriate patient referrals while maintaining the highest standards of medical ethics and regulatory compliance.

• This program complies with all applicable healthcare regulations including HIPAA Privacy and Security Rules and Stark Law Anti-Kickback Provisions
• Rewards are provided for appropriate and medically necessary referrals only, not for volume or value of services
• All participant information is maintained in strict confidence per HIPAA requirements
• Participants must comply with all professional and ethical standards

ELIGIBILITY:
• Licensed healthcare professionals only
• Referrals must be medically appropriate and in patient's best interest
• No rewards for self-referrals or inappropriate referrals
• Compliance with all professional licensing requirements

PRIVACY AND SECURITY:
• All personal and professional information protected under HIPAA
• De-identified data may be used for program analytics and improvement
• Participants may opt-out at any time
• Secure data handling and storage protocols implemented

REWARD STRUCTURE:
• Points awarded based on referral completion and quality metrics
• Tiered rewards system with progressive benefits
• Recognition and professional development opportunities
• All rewards subject to tax reporting requirements where applicable

By participating, you acknowledge understanding and agreement to these terms and confirm your commitment to maintaining the highest standards of patient care and regulatory compliance.

Last Updated: ''' + datetime.now().strftime('%Y-%m-%d')
    ))
    
    program_id = cursor.lastrowid
    
    # Sample Reward Tiers
    tiers = [
        ('Bronze Referrer', 1, 1, 'points', 10, 'Entry level recognition for quality referrals', 'automatic', ''),
        ('Silver Referrer', 2, 5, 'points', 25, 'Enhanced recognition for consistent quality referrals', 'automatic', ''),
        ('Gold Referrer', 3, 15, 'points', 50, 'Premium recognition for exceptional referral quality and consistency', 'manual', 'requires_approval'),
        ('Platinum Excellence', 4, 30, 'recognition', 100, 'Highest tier recognition with professional development opportunities', 'manual', 'committee_review')
    ]
    
    for tier in tiers:
        cursor.execute('''
            INSERT OR IGNORE INTO reward_tiers 
            (program_id, tier_name, tier_level, referrals_required, reward_type, reward_value, reward_description, fulfillment_type, fulfillment_config)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (program_id,) + tier)
    
    # Sample Reward Triggers
    triggers = [
        ('referral_completed', 'status=completed', 'completed', 10, False, True),
        ('referral_quality_high', 'quality_score>=4', 'high_quality', 25, False, True),
        ('first_referral', 'user_referral_count=1', 'first_time', 50, False, True),
        ('monthly_milestone', 'monthly_referrals>=5', 'monthly_5', 100, True, True)
    ]
    
    for trigger in triggers:
        cursor.execute('''
            INSERT OR IGNORE INTO reward_triggers 
            (program_id, trigger_type, trigger_condition, trigger_value, points_awarded, tier_advancement, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (program_id,) + trigger)
    
    # Sample Achievements
    achievements = [
        ('First Referral', 'Complete your first patient referral', 'bi-star', 'referral', 1, 50, True),
        ('Referral Streak', 'Complete 5 referrals in a row', 'bi-lightning', 'streak', 5, 100, True),
        ('Quality Champion', 'Maintain 4+ star rating for 10 referrals', 'bi-award', 'quality', 10, 200, True),
        ('Rapid Responder', 'Complete referral within 24 hours', 'bi-stopwatch', 'speed', 1, 75, True),
        ('Community Builder', 'Help 25 different patients', 'bi-people', 'community', 25, 300, True),
        ('Excellence Milestone', 'Reach 100 total referrals', 'bi-trophy', 'milestone', 100, 500, True)
    ]
    
    for achievement in achievements:
        cursor.execute('''
            INSERT OR IGNORE INTO achievements 
            (name, description, icon, achievement_type, requirement_value, points_value, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', achievement)
    
    # Sample User Rewards for existing users (demo data)
    # Get existing users
    cursor.execute('SELECT id FROM users WHERE role IN ("doctor", "patient")')
    users = cursor.fetchall()
    
    if users:
        # Add some sample rewards for the first user
        user_id = users[0][0]
        
        # Recent rewards
        sample_rewards = [
            (user_id, program_id, None, None, 10, 'earned', datetime.now() - timedelta(days=1), None, 'completed', '', True),
            (user_id, program_id, None, None, 25, 'earned', datetime.now() - timedelta(days=3), None, 'completed', '', True),
            (user_id, program_id, None, None, 50, 'pending', datetime.now() - timedelta(hours=2), None, 'pending', 'Awaiting approval', False)
        ]
        
        for reward in sample_rewards:
            cursor.execute('''
                INSERT OR IGNORE INTO user_rewards 
                (user_id, program_id, tier_id, referral_id, points_earned, reward_status, earned_date, redeemed_date, fulfillment_status, fulfillment_notes, compliance_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', reward)
        
        # Sample achievement progress
        cursor.execute('SELECT id FROM achievements LIMIT 3')
        achievement_ids = cursor.fetchall()
        
        for i, (achievement_id,) in enumerate(achievement_ids):
            if i == 0:  # First achievement - completed
                cursor.execute('''
                    INSERT OR IGNORE INTO user_achievements 
                    (user_id, achievement_id, earned_date, progress)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, achievement_id, datetime.now() - timedelta(days=5), 1))
            else:  # Others - in progress
                cursor.execute('''
                    INSERT OR IGNORE INTO user_achievements 
                    (user_id, achievement_id, earned_date, progress)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, achievement_id, None, i))
        
        # Sample notifications
        notifications = [
            (user_id, 'reward_earned', 'Congratulations!', 'You earned 10 points for your recent referral completion.'),
            (user_id, 'achievement_unlocked', 'Achievement Unlocked!', 'You have unlocked the "First Referral" achievement!'),
            (user_id, 'tier_advancement', 'Tier Advancement', 'You have been promoted to Silver Referrer tier!')
        ]
        
        for notification in notifications:
            cursor.execute('''
                INSERT OR IGNORE INTO reward_notifications 
                (user_id, notification_type, title, message)
                VALUES (?, ?, ?, ?)
            ''', notification)
    
    conn.commit()
    conn.close()
    print("✅ Rewards system initialized with sample data!")
    print("📊 Sample program: 'Professional Referral Excellence Program'")
    print("🏆 Sample achievements and tiers created")
    print("🎯 Sample rewards and notifications added")

if __name__ == '__main__':
    init_rewards_sample_data()
