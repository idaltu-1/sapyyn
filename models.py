"""
SQLAlchemy models for the Sapyyn Patient Referral System
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time
import enum
import json

db = SQLAlchemy()

class PromotionLocation(enum.Enum):
    """Enum for promotion locations in the application"""
    DASHBOARD_TOP = "dashboard_top"
    DASHBOARD_SIDEBAR = "dashboard_sidebar"
    DOCUMENTS_BANNER = "documents_banner"
    REFERRALS_PAGE = "referrals_page"
    PROFILE_PAGE = "profile_page"

class AppointmentStatus(enum.Enum):
    """Enum for appointment status"""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELED = "canceled"
    NO_SHOW = "no_show"

class NotificationType(enum.Enum):
    """Enum for notification types"""
    CONFIRMATION = "confirmation"
    REMINDER = "reminder"
    UPDATE = "update"
    CANCELLATION = "cancellation"

class DeliveryStatus(enum.Enum):
    """Enum for notification delivery status"""
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"

class User(db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='patient')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    referrals = db.relationship('Referral', backref='user', lazy=True)
    documents = db.relationship('Document', backref='user', lazy=True)
    promotion_preferences = db.relationship('UserPromotionPreference', backref='user', lazy=True, uselist=False)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Promotion(db.Model):
    """Promotion model for partner advertisements"""
    __tablename__ = 'promotions'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=False)
    target_url = db.Column(db.String(255), nullable=False)
    location = db.Column(db.Enum(PromotionLocation), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    impression_count = db.Column(db.Integer, default=0)
    click_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    allowed_roles = db.relationship('PromotionRole', backref='promotion', lazy=True, cascade='all, delete-orphan')
    
    @property
    def click_through_rate(self):
        """Calculate click-through rate"""
        if self.impression_count == 0:
            return 0
        return self.click_count / self.impression_count
    
    def __repr__(self):
        return f'<Promotion {self.title}>'

class PromotionRole(db.Model):
    """Roles that can see a specific promotion"""
    __tablename__ = 'promotion_roles'
    
    id = db.Column(db.Integer, primary_key=True)
    promotion_id = db.Column(db.Integer, db.ForeignKey('promotions.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('promotion_id', 'role', name='uix_promotion_role'),
    )
    
    def __repr__(self):
        return f'<PromotionRole {self.role}>'

class UserPromotionPreference(db.Model):
    """User preferences for promotions"""
    __tablename__ = 'user_promotion_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    opt_out = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserPromotionPreference user_id={self.user_id} opt_out={self.opt_out}>'

class Referral(db.Model):
    """Referral model"""
    __tablename__ = 'referrals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referral_id = db.Column(db.String(8), unique=True, nullable=False)
    patient_name = db.Column(db.String(120), nullable=False)
    referring_doctor = db.Column(db.String(120))
    target_doctor = db.Column(db.String(120))
    medical_condition = db.Column(db.Text)
    urgency_level = db.Column(db.String(20), default='normal')
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text)
    qr_code = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = db.relationship('Document', backref='referral', lazy=True)
    
    def __repr__(self):
        return f'<Referral {self.referral_id}>'

class Document(db.Model):
    """Document model"""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    referral_id = db.Column(db.Integer, db.ForeignKey('referrals.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    file_type = db.Column(db.String(50), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Document {self.file_name}>'

class Appointment(db.Model):
    """Appointment model"""
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    specialist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referral_id = db.Column(db.Integer, db.ForeignKey('referrals.id'))
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED, nullable=False)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('User', foreign_keys=[patient_id], backref='patient_appointments')
    specialist = db.relationship('User', foreign_keys=[specialist_id], backref='specialist_appointments')
    creator = db.relationship('User', foreign_keys=[created_by])
    referral = db.relationship('Referral', backref='appointments')
    notifications = db.relationship('AppointmentNotification', backref='appointment', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Appointment {self.id}: {self.title}>'
    
    @property
    def duration_minutes(self):
        """Calculate appointment duration in minutes"""
        if not self.start_time or not self.end_time:
            return 0
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 60

class Availability(db.Model):
    """Specialist availability model"""
    __tablename__ = 'availability'
    
    id = db.Column(db.Integer, primary_key=True)
    specialist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    day_of_week = db.Column(db.Integer)  # 0-6, where 0 is Monday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_recurring = db.Column(db.Boolean, default=True)
    specific_date = db.Column(db.Date)  # Only for non-recurring availability
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    specialist = db.relationship('User', backref='availability_slots')
    
    def __repr__(self):
        if self.is_recurring:
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            return f'<Availability {day_names[self.day_of_week]}: {self.start_time}-{self.end_time}>'
        else:
            return f'<Availability {self.specific_date}: {self.start_time}-{self.end_time}>'

class AppointmentNotification(db.Model):
    """Appointment notification model"""
    __tablename__ = 'appointment_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.Enum(NotificationType), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_status = db.Column(db.Enum(DeliveryStatus), default=DeliveryStatus.SENT)
    
    # Relationships
    user = db.relationship('User', backref='appointment_notifications')
    
    def __repr__(self):
        return f'<AppointmentNotification {self.notification_type.value} for appointment {self.appointment_id}>'

class ComplianceAuditTrail(db.Model):
    """Audit trail model for compliance tracking"""
    __tablename__ = 'compliance_audit_trail'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action_type = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.String(50), nullable=False)
    action_details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditTrail {self.action_type} {self.entity_type} {self.entity_id}>'
    
    @property
    def details_dict(self):
        """Convert action_details string to dictionary"""
        if not self.action_details:
            return {}
        try:
            return json.loads(self.action_details)
        except json.JSONDecodeError:
            return {"raw": self.action_details}