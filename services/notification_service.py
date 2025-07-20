"""
Notification service for appointment-related notifications
"""

from datetime import datetime
from models import db, Appointment, AppointmentNotification, NotificationType, DeliveryStatus, User

class NotificationService:
    """Service for appointment-related notifications"""
    
    @staticmethod
    def send_appointment_confirmation(appointment_id):
        """Send appointment confirmation notifications
        
        Args:
            appointment_id (int): ID of the appointment
            
        Returns:
            bool: True if notifications were sent, False otherwise
        """
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return False
        
        # Create notifications for patient and specialist
        patient_notification = AppointmentNotification(
            appointment_id=appointment_id,
            user_id=appointment.patient_id,
            notification_type=NotificationType.CONFIRMATION
        )
        
        specialist_notification = AppointmentNotification(
            appointment_id=appointment_id,
            user_id=appointment.specialist_id,
            notification_type=NotificationType.CONFIRMATION
        )
        
        db.session.add_all([patient_notification, specialist_notification])
        
        # If this appointment is linked to a referral, notify the referring doctor
        if appointment.referral_id:
            referral = appointment.referral
            if referral and referral.user_id:
                referring_doctor_notification = AppointmentNotification(
                    appointment_id=appointment_id,
                    user_id=referral.user_id,
                    notification_type=NotificationType.CONFIRMATION
                )
                db.session.add(referring_doctor_notification)
        
        db.session.commit()
        
        # Send emails (this would integrate with an email service)
        NotificationService._send_confirmation_emails(appointment)
        
        return True
    
    @staticmethod
    def send_appointment_reminder(appointment_id):
        """Send appointment reminder notifications
        
        Args:
            appointment_id (int): ID of the appointment
            
        Returns:
            bool: True if notifications were sent, False otherwise
        """
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return False
        
        # Only send reminders for scheduled appointments
        if appointment.status != 'scheduled':
            return False
        
        # Create notification for patient
        patient_notification = AppointmentNotification(
            appointment_id=appointment_id,
            user_id=appointment.patient_id,
            notification_type=NotificationType.REMINDER
        )
        
        db.session.add(patient_notification)
        db.session.commit()
        
        # Send email reminder (this would integrate with an email service)
        NotificationService._send_reminder_email(appointment)
        
        return True
    
    @staticmethod
    def send_appointment_update(appointment_id, update_type):
        """Send appointment update notifications
        
        Args:
            appointment_id (int): ID of the appointment
            update_type (str): Type of update (e.g., 'rescheduled', 'notes_added')
            
        Returns:
            bool: True if notifications were sent, False otherwise
        """
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return False
        
        # Create notifications for patient and specialist
        patient_notification = AppointmentNotification(
            appointment_id=appointment_id,
            user_id=appointment.patient_id,
            notification_type=NotificationType.UPDATE
        )
        
        specialist_notification = AppointmentNotification(
            appointment_id=appointment_id,
            user_id=appointment.specialist_id,
            notification_type=NotificationType.UPDATE
        )
        
        db.session.add_all([patient_notification, specialist_notification])
        
        # If this appointment is linked to a referral, notify the referring doctor
        if appointment.referral_id:
            referral = appointment.referral
            if referral and referral.user_id:
                referring_doctor_notification = AppointmentNotification(
                    appointment_id=appointment_id,
                    user_id=referral.user_id,
                    notification_type=NotificationType.UPDATE
                )
                db.session.add(referring_doctor_notification)
        
        db.session.commit()
        
        # Send emails (this would integrate with an email service)
        NotificationService._send_update_emails(appointment, update_type)
        
        return True
    
    @staticmethod
    def send_appointment_cancellation(appointment_id, cancellation_reason=None):
        """Send appointment cancellation notifications
        
        Args:
            appointment_id (int): ID of the appointment
            cancellation_reason (str): Optional reason for cancellation
            
        Returns:
            bool: True if notifications were sent, False otherwise
        """
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return False
        
        # Create notifications for patient and specialist
        patient_notification = AppointmentNotification(
            appointment_id=appointment_id,
            user_id=appointment.patient_id,
            notification_type=NotificationType.CANCELLATION
        )
        
        specialist_notification = AppointmentNotification(
            appointment_id=appointment_id,
            user_id=appointment.specialist_id,
            notification_type=NotificationType.CANCELLATION
        )
        
        db.session.add_all([patient_notification, specialist_notification])
        
        # If this appointment is linked to a referral, notify the referring doctor
        if appointment.referral_id:
            referral = appointment.referral
            if referral and referral.user_id:
                referring_doctor_notification = AppointmentNotification(
                    appointment_id=appointment_id,
                    user_id=referral.user_id,
                    notification_type=NotificationType.CANCELLATION
                )
                db.session.add(referring_doctor_notification)
        
        db.session.commit()
        
        # Send emails (this would integrate with an email service)
        NotificationService._send_cancellation_emails(appointment, cancellation_reason)
        
        return True
    
    @staticmethod
    def _send_confirmation_emails(appointment):
        """Send confirmation emails for an appointment
        
        Args:
            appointment (Appointment): The appointment
        """
        # This is a placeholder for actual email sending logic
        # In a real implementation, this would use an email service
        
        # Get user information
        patient = User.query.get(appointment.patient_id)
        specialist = User.query.get(appointment.specialist_id)
        
        if patient and patient.email:
            # Send patient confirmation email
            print(f"[EMAIL] To: {patient.email}")
            print(f"[EMAIL] Subject: Your appointment with {specialist.full_name} is confirmed")
            print(f"[EMAIL] Body: Your appointment on {appointment.start_time.strftime('%Y-%m-%d at %H:%M')} has been confirmed.")
        
        if specialist and specialist.email:
            # Send specialist confirmation email
            print(f"[EMAIL] To: {specialist.email}")
            print(f"[EMAIL] Subject: New appointment with {patient.full_name}")
            print(f"[EMAIL] Body: You have a new appointment on {appointment.start_time.strftime('%Y-%m-%d at %H:%M')}.")
        
        # If this appointment is linked to a referral, notify the referring doctor
        if appointment.referral_id:
            referral = appointment.referral
            if referral and referral.user_id:
                referring_doctor = User.query.get(referral.user_id)
                if referring_doctor and referring_doctor.email:
                    print(f"[EMAIL] To: {referring_doctor.email}")
                    print(f"[EMAIL] Subject: Referral appointment scheduled")
                    print(f"[EMAIL] Body: An appointment has been scheduled for your referral {referral.referral_id}.")
    
    @staticmethod
    def _send_reminder_email(appointment):
        """Send reminder email for an appointment
        
        Args:
            appointment (Appointment): The appointment
        """
        # This is a placeholder for actual email sending logic
        # In a real implementation, this would use an email service
        
        # Get user information
        patient = User.query.get(appointment.patient_id)
        specialist = User.query.get(appointment.specialist_id)
        
        if patient and patient.email:
            # Send patient reminder email
            print(f"[EMAIL] To: {patient.email}")
            print(f"[EMAIL] Subject: Reminder: Your appointment with {specialist.full_name}")
            print(f"[EMAIL] Body: This is a reminder for your appointment on {appointment.start_time.strftime('%Y-%m-%d at %H:%M')}.")
    
    @staticmethod
    def _send_update_emails(appointment, update_type):
        """Send update emails for an appointment
        
        Args:
            appointment (Appointment): The appointment
            update_type (str): Type of update
        """
        # This is a placeholder for actual email sending logic
        # In a real implementation, this would use an email service
        
        # Get user information
        patient = User.query.get(appointment.patient_id)
        specialist = User.query.get(appointment.specialist_id)
        
        if patient and patient.email:
            # Send patient update email
            print(f"[EMAIL] To: {patient.email}")
            print(f"[EMAIL] Subject: Your appointment with {specialist.full_name} has been updated")
            print(f"[EMAIL] Body: Your appointment on {appointment.start_time.strftime('%Y-%m-%d at %H:%M')} has been updated.")
        
        if specialist and specialist.email:
            # Send specialist update email
            print(f"[EMAIL] To: {specialist.email}")
            print(f"[EMAIL] Subject: Updated appointment with {patient.full_name}")
            print(f"[EMAIL] Body: The appointment on {appointment.start_time.strftime('%Y-%m-%d at %H:%M')} has been updated.")
        
        # If this appointment is linked to a referral, notify the referring doctor
        if appointment.referral_id:
            referral = appointment.referral
            if referral and referral.user_id:
                referring_doctor = User.query.get(referral.user_id)
                if referring_doctor and referring_doctor.email:
                    print(f"[EMAIL] To: {referring_doctor.email}")
                    print(f"[EMAIL] Subject: Referral appointment updated")
                    print(f"[EMAIL] Body: An appointment for your referral {referral.referral_id} has been updated.")
    
    @staticmethod
    def _send_cancellation_emails(appointment, cancellation_reason=None):
        """Send cancellation emails for an appointment
        
        Args:
            appointment (Appointment): The appointment
            cancellation_reason (str): Optional reason for cancellation
        """
        # This is a placeholder for actual email sending logic
        # In a real implementation, this would use an email service
        
        # Get user information
        patient = User.query.get(appointment.patient_id)
        specialist = User.query.get(appointment.specialist_id)
        
        reason_text = f"Reason: {cancellation_reason}" if cancellation_reason else ""
        
        if patient and patient.email:
            # Send patient cancellation email
            print(f"[EMAIL] To: {patient.email}")
            print(f"[EMAIL] Subject: Your appointment with {specialist.full_name} has been cancelled")
            print(f"[EMAIL] Body: Your appointment on {appointment.start_time.strftime('%Y-%m-%d at %H:%M')} has been cancelled. {reason_text}")
        
        if specialist and specialist.email:
            # Send specialist cancellation email
            print(f"[EMAIL] To: {specialist.email}")
            print(f"[EMAIL] Subject: Cancelled appointment with {patient.full_name}")
            print(f"[EMAIL] Body: The appointment on {appointment.start_time.strftime('%Y-%m-%d at %H:%M')} has been cancelled. {reason_text}")
        
        # If this appointment is linked to a referral, notify the referring doctor
        if appointment.referral_id:
            referral = appointment.referral
            if referral and referral.user_id:
                referring_doctor = User.query.get(referral.user_id)
                if referring_doctor and referring_doctor.email:
                    print(f"[EMAIL] To: {referring_doctor.email}")
                    print(f"[EMAIL] Subject: Referral appointment cancelled")
                    print(f"[EMAIL] Body: An appointment for your referral {referral.referral_id} has been cancelled. {reason_text}")