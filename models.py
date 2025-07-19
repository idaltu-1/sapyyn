"""
Database models for Sapyyn Patient Referral System
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='patient')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    referrals = db.relationship('Referral', backref='user', lazy=True)
    documents = db.relationship('Document', backref='user', lazy=True)
    user_rewards = db.relationship('UserReward', backref='user', lazy=True)
    profile = db.relationship('UserProfile', backref='user', uselist=False)


class Referral(db.Model):
    __tablename__ = 'referrals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referral_id = db.Column(db.String(255), unique=True, nullable=False)
    patient_name = db.Column(db.String(255), nullable=False)
    referring_doctor = db.Column(db.String(255))
    target_doctor = db.Column(db.String(255))
    medical_condition = db.Column(db.Text)
    urgency_level = db.Column(db.String(50), default='normal')
    status = db.Column(db.String(50), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = db.relationship('Document', backref='referral', lazy=True)


class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    referral_id = db.Column(db.Integer, db.ForeignKey('referrals.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    file_type = db.Column(db.String(50), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)


class RewardProgram(db.Model):
    __tablename__ = 'reward_programs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    program_type = db.Column(db.String(50), default='referral')
    status = db.Column(db.String(50), default='active')
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    compliance_notes = db.Column(db.Text)
    legal_language = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tiers = db.relationship('RewardTier', backref='program', lazy=True)
    user_rewards = db.relationship('UserReward', backref='program', lazy=True)


class RewardTier(db.Model):
    __tablename__ = 'reward_tiers'
    
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('reward_programs.id'))
    tier_name = db.Column(db.String(255), nullable=False)
    tier_level = db.Column(db.Integer, default=1)
    referrals_required = db.Column(db.Integer, default=1)
    reward_type = db.Column(db.String(50), default='points')
    reward_value = db.Column(db.Numeric(10, 2))
    reward_description = db.Column(db.Text)
    fulfillment_type = db.Column(db.String(50), default='manual')
    fulfillment_config = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserReward(db.Model):
    __tablename__ = 'user_rewards'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    program_id = db.Column(db.Integer, db.ForeignKey('reward_programs.id'))
    tier_id = db.Column(db.Integer, db.ForeignKey('reward_tiers.id'))
    referral_id = db.Column(db.Integer, db.ForeignKey('referrals.id'))
    points_earned = db.Column(db.Numeric(10, 2), default=0)
    reward_status = db.Column(db.String(50), default='pending')
    earned_date = db.Column(db.DateTime, default=datetime.utcnow)
    redeemed_date = db.Column(db.DateTime)
    fulfillment_status = db.Column(db.String(50), default='pending')
    fulfillment_notes = db.Column(db.Text)
    compliance_verified = db.Column(db.Boolean, default=False)
    audit_trail = db.Column(db.Text)
    
    # Relationships
    tier = db.relationship('RewardTier', backref='user_rewards')


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    license_number = db.Column(db.String(100))
    specialization = db.Column(db.String(255))
    practice_name = db.Column(db.String(255))
    practice_address = db.Column(db.Text)
    years_experience = db.Column(db.String(50))
    website = db.Column(db.String(255))
    bio = db.Column(db.Text)
    profile_image = db.Column(db.String(255))
    verification_status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Practice(db.Model):
    __tablename__ = 'practices'
    
    id = db.Column(db.Integer, primary_key=True)
    practice_name = db.Column(db.String(255), nullable=False)
    practice_type = db.Column(db.String(100))
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    website = db.Column(db.String(255))
    admin_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    subscription_id = db.Column(db.Integer)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    admin = db.relationship('User', backref='administered_practices')


class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_name = db.Column(db.String(255), nullable=False)
    plan_type = db.Column(db.String(50), nullable=False)
    price_monthly = db.Column(db.Numeric(10, 2))
    price_annual = db.Column(db.Numeric(10, 2))
    features = db.Column(db.Text)
    max_referrals = db.Column(db.Integer)
    max_users = db.Column(db.Integer)
    storage_gb = db.Column(db.Integer)
    support_level = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserSubscription(db.Model):
    __tablename__ = 'user_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'))
    subscription_status = db.Column(db.String(50), default='active')
    billing_cycle = db.Column(db.String(20), default='monthly')
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    auto_renew = db.Column(db.Boolean, default=True)
    payment_method = db.Column(db.String(50))
    stripe_customer_id = db.Column(db.String(255))
    stripe_subscription_id = db.Column(db.String(255))
    trial_end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='subscriptions')
    plan = db.relationship('SubscriptionPlan', backref='subscriptions')