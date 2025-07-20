"""
Audit logging service for tracking system actions
"""

import logging
import json
import os
from datetime import datetime
from flask import request, session
from models import db, ComplianceAuditTrail

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Configure audit logger
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)

# Add file handler
file_handler = logging.FileHandler('logs/audit.log')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
audit_logger.addHandler(file_handler)

# Add console handler for development
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
audit_logger.addHandler(console_handler)

class AuditService:
    """Service for audit logging"""
    
    @staticmethod
    def log_action(action, entity_type, entity_id, details=None):
        """Log an action in the audit log
        
        Args:
            action (str): The action performed (create, update, delete, etc.)
            entity_type (str): The type of entity (promotion, user, etc.)
            entity_id: The ID of the entity
            details (dict, optional): Additional details about the action
            
        Returns:
            ComplianceAuditTrail: The created audit log entry
        """
        # Get user information from session
        user_id = session.get('user_id')
        username = session.get('username', 'Anonymous')
        
        # Get request information
        ip_address = request.remote_addr
        user_agent = request.user_agent.string
        
        # Create log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'entity_type': entity_type,
            'entity_id': str(entity_id),
            'user_id': user_id,
            'username': username,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'details': details or {}
        }
        
        # Log to application log
        log_message = f"AUDIT: {action} {entity_type} {entity_id} by {username} (ID: {user_id}) from {ip_address}"
        if details:
            log_message += f" - Details: {json.dumps(details)}"
        audit_logger.info(log_message)
        
        # Store in database
        try:
            audit_trail = ComplianceAuditTrail(
                user_id=user_id,
                action_type=f"{entity_type.upper()}_{action.upper()}",
                entity_type=entity_type,
                entity_id=str(entity_id),
                action_details=json.dumps(details) if details else None,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.session.add(audit_trail)
            db.session.commit()
            return audit_trail
        except Exception as e:
            # Log error but don't fail the operation
            audit_logger.error(f"Failed to store audit trail in database: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def log_promotion_action(action_type, promotion_id, details=None):
        """Log a promotion-related action
        
        Args:
            action_type (str): Type of action (create, update, delete, etc.)
            promotion_id (int): ID of the promotion
            details (dict, optional): Additional details about the action
        """
        return AuditService.log_action(action_type, 'promotion', promotion_id, details)
    
    @staticmethod
    def log_promotion_view(promotion_id, location):
        """Log a promotion view (impression)
        
        Args:
            promotion_id (int): ID of the promotion
            location (str): Location where the promotion was displayed
        """
        # Get user information from session
        user_id = session.get('user_id', 'anonymous')
        user_role = session.get('role', 'anonymous')
        
        # Get request information
        ip_address = request.remote_addr
        user_agent = request.user_agent.string
        
        # Create log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action_type': 'view',
            'entity_type': 'promotion',
            'entity_id': promotion_id,
            'user_id': user_id,
            'user_role': user_role,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'location': location
        }
        
        # Log to audit log file (at debug level to avoid flooding)
        audit_logger.debug(f"PROMOTION_VIEW: {log_entry}")
    
    @staticmethod
    def log_promotion_click(promotion_id):
        """Log a promotion click
        
        Args:
            promotion_id (int): ID of the promotion
        """
        # Get user information from session
        user_id = session.get('user_id', 'anonymous')
        user_role = session.get('role', 'anonymous')
        
        # Get request information
        ip_address = request.remote_addr
        user_agent = request.user_agent.string
        
        # Create log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action_type': 'click',
            'entity_type': 'promotion',
            'entity_id': promotion_id,
            'user_id': user_id,
            'user_role': user_role,
            'ip_address': ip_address,
            'user_agent': user_agent
        }
        
        # Log to audit log file
        audit_logger.info(f"PROMOTION_CLICK: {log_entry}")
    
    @staticmethod
    def log_preference_update(user_id, opt_out):
        """Log a user preference update
        
        Args:
            user_id (int): ID of the user
            opt_out (bool): Whether the user opted out of targeted promotions
        """
        # Get request information
        ip_address = request.remote_addr
        user_agent = request.user_agent.string
        
        # Create log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action_type': 'preference_update',
            'entity_type': 'user',
            'entity_id': user_id,
            'user_id': user_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'details': {'opt_out': opt_out}
        }
        
        # Log to audit log file
        audit_logger.info(f"PREFERENCE_UPDATE: {log_entry}")
        
        # Store in database if compliance_audit_trail table exists
        try:
            from models import ComplianceAuditTrail
            
            audit_trail = ComplianceAuditTrail(
                user_id=user_id,
                action_type='PROMOTION_PREFERENCE_UPDATE',
                entity_type='user',
                entity_id=user_id,
                action_details=f"Opt-out: {opt_out}",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.session.add(audit_trail)
            db.session.commit()
        except Exception as e:
            # Log error but don't fail the operation
            audit_logger.error(f"Failed to store audit trail in database: {str(e)}")