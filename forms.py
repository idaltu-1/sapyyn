"""
Flask-WTF forms for authentication and user management
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from wtforms.widgets import TextArea
from config import Config
from auth_utils import validate_password_complexity, validate_domain_restriction
import re

class PasswordComplexityValidator:
    """Custom validator for password complexity"""
    
    def __init__(self, message=None):
        if not message:
            message = Config.get_password_requirements_text()
        self.message = message
    
    def __call__(self, form, field):
        is_valid, errors = validate_password_complexity(field.data)
        if not is_valid:
            raise ValidationError(self.message + " Issues: " + "; ".join(errors))

class DomainRestrictionValidator:
    """Custom validator for email domain restrictions"""
    
    def __init__(self, message=None):
        if not message:
            message = "Email domain is not in the allowed domains list. Access restricted to authorized domains only."
        self.message = message
    
    def __call__(self, form, field):
        is_valid, error_message = validate_domain_restriction(field.data)
        if not is_valid:
            raise ValidationError(error_message)

class LoginForm(FlaskForm):
    """Enhanced login form with domain validation"""
    
    username = StringField('Username', validators=[
        DataRequired(message="Username is required")
    ], render_kw={
        'class': 'form-control form-control-lg',
        'placeholder': 'Enter your username or email',
        'autocomplete': 'username'
    })
    
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required")
    ], render_kw={
        'class': 'form-control form-control-lg',
        'placeholder': 'Enter your password',
        'autocomplete': 'current-password'
    })
    
    remember_me = BooleanField('Remember me', render_kw={
        'class': 'form-check-input'
    })
    
    def validate_username(self, field):
        """Validate username/email domain if it's an email"""
        if '@' in field.data:
            # This is an email, check domain restrictions
            is_valid, error_message = validate_domain_restriction(field.data)
            if not is_valid:
                raise ValidationError(error_message)

class RegistrationForm(FlaskForm):
    """Enhanced registration form with password complexity and domain validation"""
    
    full_name = StringField('Full Name', validators=[
        DataRequired(message="Full name is required"),
        Length(min=2, max=100, message="Full name must be between 2 and 100 characters")
    ], render_kw={
        'class': 'form-control',
        'placeholder': 'Enter your full name'
    })
    
    username = StringField('Username', validators=[
        DataRequired(message="Username is required"),
        Length(min=3, max=50, message="Username must be between 3 and 50 characters")
    ], render_kw={
        'class': 'form-control',
        'placeholder': 'Choose a username'
    })
    
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address"),
        DomainRestrictionValidator()
    ], render_kw={
        'class': 'form-control',
        'placeholder': 'Enter your email address'
    })
    
    role = SelectField('Account Type', choices=[
        ('', 'Select your role'),
        ('patient', 'Patient'),
        ('dentist', 'Dentist'),
        ('specialist', 'Specialist'),
        ('dentist_admin', 'Dental Practice Administrator'),
        ('specialist_admin', 'Specialist Practice Administrator')
    ], validators=[
        DataRequired(message="Please select your account type")
    ], render_kw={
        'class': 'form-select'
    })
    
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required"),
        PasswordComplexityValidator()
    ], render_kw={
        'class': 'form-control',
        'placeholder': 'Create a secure password'
    })
    
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo('password', message="Passwords must match")
    ], render_kw={
        'class': 'form-control',
        'placeholder': 'Re-enter your password'
    })
    
    agree_terms = BooleanField('I agree to the Terms of Service and Privacy Policy', validators=[
        DataRequired(message="You must agree to the terms and privacy policy")
    ], render_kw={
        'class': 'form-check-input'
    })
    
    hipaa_acknowledge = BooleanField('I understand this system handles protected health information (PHI) and agree to use it in compliance with HIPAA regulations', validators=[
        DataRequired(message="You must acknowledge HIPAA compliance requirements")
    ], render_kw={
        'class': 'form-check-input'
    })
    
    def validate_username(self, field):
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_]+$', field.data):
            raise ValidationError("Username can only contain letters, numbers, and underscores")

class PasswordResetRequestForm(FlaskForm):
    """Form for requesting password reset"""
    
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address"),
        DomainRestrictionValidator()
    ], render_kw={
        'class': 'form-control form-control-lg',
        'placeholder': 'Enter your email address'
    })

class PasswordResetForm(FlaskForm):
    """Form for resetting password with token"""
    
    password = PasswordField('New Password', validators=[
        DataRequired(message="Password is required"),
        PasswordComplexityValidator()
    ], render_kw={
        'class': 'form-control form-control-lg',
        'placeholder': 'Enter new password'
    })
    
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo('password', message="Passwords must match")
    ], render_kw={
        'class': 'form-control form-control-lg',
        'placeholder': 'Confirm new password'
    })

class ChangePasswordForm(FlaskForm):
    """Form for changing password while logged in"""
    
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message="Current password is required")
    ], render_kw={
        'class': 'form-control',
        'placeholder': 'Enter current password'
    })
    
    new_password = PasswordField('New Password', validators=[
        DataRequired(message="New password is required"),
        PasswordComplexityValidator()
    ], render_kw={
        'class': 'form-control',
        'placeholder': 'Enter new password'
    })
    
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message="Please confirm your new password"),
        EqualTo('new_password', message="Passwords must match")
    ], render_kw={
        'class': 'form-control',
        'placeholder': 'Confirm new password'
    })

class ProfileForm(FlaskForm):
    """Form for updating user profile"""
    
    full_name = StringField('Full Name', validators=[
        DataRequired(message="Full name is required"),
        Length(min=2, max=100, message="Full name must be between 2 and 100 characters")
    ], render_kw={
        'class': 'form-control'
    })
    
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address"),
        DomainRestrictionValidator()
    ], render_kw={
        'class': 'form-control'
    })
    
    phone = StringField('Phone Number', validators=[
        Length(max=20, message="Phone number must be less than 20 characters")
    ], render_kw={
        'class': 'form-control',
        'placeholder': 'Optional'
    })
    
    practice_name = StringField('Practice Name', render_kw={
        'class': 'form-control',
        'placeholder': 'Optional'
    })
    
    specialization = StringField('Specialization', render_kw={
        'class': 'form-control',
        'placeholder': 'Optional'
    })
    
    bio = TextAreaField('Bio/Notes', render_kw={
        'class': 'form-control',
        'rows': 4,
        'placeholder': 'Optional professional bio or notes'
    })