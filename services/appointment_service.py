"""
Appointment service for managing appointments
"""

from datetime import datetime, timedelta
from models import db, Appointment, AppointmentStatus, User, Referral, AppointmentNotification, NotificationType
from sqlalchemy import and_, or_, func

class AppointmentService:
    """Service for managing appointments"""
    
    @staticmethod
    def create_appointment(appointment_data):
        """Create a new appointment
        
        Args:
            appointment_data (dict): Appointment data including patient_id, specialist_id, etc.
            
        Returns:
            Appointment: The created appointment
        """
        # Validate appointment data
        AppointmentService._validate_appointment_data(appointment_data)
        
        # Check for conflicts
        if AppointmentService.check_appointment_conflicts(
            appointment_data['specialist_id'],
            appointment_data['start_time'],
            appointment_data['end_time']
        ):
            raise ValueError("Appointment time conflicts with an existing appointment")
        
        # Create appointment
        appointment = Appointment(
            patient_id=appointment_data['patient_id'],
            specialist_id=appointment_data['specialist_id'],
            referral_id=appointment_data.get('referral_id'),
            title=appointment_data['title'],
            description=appointment_data.get('description', ''),
            start_time=appointment_data['start_time'],
            end_time=appointment_data['end_time'],
            status=AppointmentStatus.SCHEDULED,
            created_by=appointment_data['created_by']
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        return appointment
    
    @staticmethod
    def update_appointment(appointment_id, appointment_data):
        """Update an existing appointment
        
        Args:
            appointment_id (int): ID of the appointment to update
            appointment_data (dict): Updated appointment data
            
        Returns:
            Appointment: The updated appointment or None if not found
        """
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return None
        
        # Update fields if provided
        if 'title' in appointment_data:
            appointment.title = appointment_data['title']
        if 'description' in appointment_data:
            appointment.description = appointment_data['description']
        if 'start_time' in appointment_data and 'end_time' in appointment_data:
            # Check for conflicts with the new time
            if AppointmentService.check_appointment_conflicts(
                appointment.specialist_id,
                appointment_data['start_time'],
                appointment_data['end_time'],
                exclude_appointment_id=appointment_id
            ):
                raise ValueError("New appointment time conflicts with an existing appointment")
            
            appointment.start_time = appointment_data['start_time']
            appointment.end_time = appointment_data['end_time']
        if 'status' in appointment_data:
            appointment.status = appointment_data['status']
        if 'notes' in appointment_data:
            appointment.notes = appointment_data['notes']
        
        appointment.updated_at = datetime.utcnow()
        db.session.commit()
        
        return appointment
    
    @staticmethod
    def get_appointment(appointment_id):
        """Get an appointment by ID
        
        Args:
            appointment_id (int): ID of the appointment
            
        Returns:
            Appointment: The appointment or None if not found
        """
        return Appointment.query.get(appointment_id)
    
    @staticmethod
    def list_appointments(filters=None):
        """List appointments with optional filters
        
        Args:
            filters (dict): Optional filters like patient_id, specialist_id, status, etc.
            
        Returns:
            list: List of appointments matching the filters
        """
        query = Appointment.query
        
        if filters:
            if 'patient_id' in filters:
                query = query.filter(Appointment.patient_id == filters['patient_id'])
            if 'specialist_id' in filters:
                query = query.filter(Appointment.specialist_id == filters['specialist_id'])
            if 'referral_id' in filters:
                query = query.filter(Appointment.referral_id == filters['referral_id'])
            if 'status' in filters:
                query = query.filter(Appointment.status == filters['status'])
            if 'start_date' in filters:
                query = query.filter(func.date(Appointment.start_time) >= filters['start_date'])
            if 'end_date' in filters:
                query = query.filter(func.date(Appointment.start_time) <= filters['end_date'])
            if 'upcoming' in filters and filters['upcoming']:
                query = query.filter(
                    Appointment.start_time >= datetime.utcnow(),
                    Appointment.status == AppointmentStatus.SCHEDULED
                )
        
        return query.order_by(Appointment.start_time).all()
    
    @staticmethod
    def cancel_appointment(appointment_id, cancellation_reason=None):
        """Cancel an appointment
        
        Args:
            appointment_id (int): ID of the appointment to cancel
            cancellation_reason (str): Optional reason for cancellation
            
        Returns:
            Appointment: The canceled appointment or None if not found
        """
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return None
        
        # Only scheduled appointments can be canceled
        if appointment.status != AppointmentStatus.SCHEDULED:
            raise ValueError(f"Cannot cancel appointment with status {appointment.status.value}")
        
        appointment.status = AppointmentStatus.CANCELED
        if cancellation_reason:
            if appointment.notes:
                appointment.notes += f"\n\nCancellation reason: {cancellation_reason}"
            else:
                appointment.notes = f"Cancellation reason: {cancellation_reason}"
        
        appointment.updated_at = datetime.utcnow()
        db.session.commit()
        
        return appointment
    
    @staticmethod
    def complete_appointment(appointment_id, notes=None):
        """Mark an appointment as completed
        
        Args:
            appointment_id (int): ID of the appointment to complete
            notes (str): Optional notes from the appointment
            
        Returns:
            Appointment: The completed appointment or None if not found
        """
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return None
        
        # Only scheduled appointments can be completed
        if appointment.status != AppointmentStatus.SCHEDULED:
            raise ValueError(f"Cannot complete appointment with status {appointment.status.value}")
        
        appointment.status = AppointmentStatus.COMPLETED
        if notes:
            if appointment.notes:
                appointment.notes += f"\n\n{notes}"
            else:
                appointment.notes = notes
        
        appointment.updated_at = datetime.utcnow()
        db.session.commit()
        
        return appointment
    
    @staticmethod
    def mark_as_no_show(appointment_id, notes=None):
        """Mark an appointment as no-show
        
        Args:
            appointment_id (int): ID of the appointment to mark as no-show
            notes (str): Optional notes about the no-show
            
        Returns:
            Appointment: The updated appointment or None if not found
        """
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return None
        
        # Only scheduled appointments can be marked as no-show
        if appointment.status != AppointmentStatus.SCHEDULED:
            raise ValueError(f"Cannot mark appointment with status {appointment.status.value} as no-show")
        
        appointment.status = AppointmentStatus.NO_SHOW
        if notes:
            if appointment.notes:
                appointment.notes += f"\n\nNo-show notes: {notes}"
            else:
                appointment.notes = f"No-show notes: {notes}"
        
        appointment.updated_at = datetime.utcnow()
        db.session.commit()
        
        return appointment
    
    @staticmethod
    def get_available_slots(specialist_id, date):
        """Get available time slots for a specialist on a specific date
        
        Args:
            specialist_id (int): ID of the specialist
            date (date): Date to check availability for
            
        Returns:
            list: List of available time slots as (start_time, end_time) tuples
        """
        from services.availability_service import AvailabilityService
        
        # Get specialist's availability for the date
        availability = AvailabilityService.get_availability(specialist_id, date)
        if not availability:
            return []
        
        # Get all appointments for the specialist on that date
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = datetime.combine(date, datetime.max.time())
        
        appointments = Appointment.query.filter(
            Appointment.specialist_id == specialist_id,
            Appointment.start_time >= start_of_day,
            Appointment.start_time <= end_of_day,
            Appointment.status == AppointmentStatus.SCHEDULED
        ).order_by(Appointment.start_time).all()
        
        # Generate available slots based on availability and existing appointments
        available_slots = []
        for avail in availability:
            # Convert availability times to datetime
            avail_start = datetime.combine(date, avail.start_time)
            avail_end = datetime.combine(date, avail.end_time)
            
            # Default slot duration is 30 minutes
            slot_duration = timedelta(minutes=30)
            
            # Generate potential slots
            current_slot_start = avail_start
            while current_slot_start + slot_duration <= avail_end:
                current_slot_end = current_slot_start + slot_duration
                
                # Check if slot conflicts with any appointment
                is_available = True
                for appt in appointments:
                    if (current_slot_start < appt.end_time and 
                        current_slot_end > appt.start_time):
                        is_available = False
                        break
                
                if is_available:
                    available_slots.append((current_slot_start, current_slot_end))
                
                # Move to next potential slot
                current_slot_start += slot_duration
        
        return available_slots
    
    @staticmethod
    def check_appointment_conflicts(specialist_id, start_time, end_time, exclude_appointment_id=None):
        """Check for appointment conflicts
        
        Args:
            specialist_id (int): ID of the specialist
            start_time (datetime): Start time of the appointment
            end_time (datetime): End time of the appointment
            exclude_appointment_id (int): Optional ID of an appointment to exclude from the check
            
        Returns:
            bool: True if there's a conflict, False otherwise
        """
        query = Appointment.query.filter(
            Appointment.specialist_id == specialist_id,
            Appointment.status == AppointmentStatus.SCHEDULED,
            Appointment.start_time < end_time,
            Appointment.end_time > start_time
        )
        
        if exclude_appointment_id:
            query = query.filter(Appointment.id != exclude_appointment_id)
        
        return query.count() > 0
    
    @staticmethod
    def get_appointments_by_referral(referral_id):
        """Get appointments associated with a referral
        
        Args:
            referral_id (int): ID of the referral
            
        Returns:
            list: List of appointments for the referral
        """
        return Appointment.query.filter_by(referral_id=referral_id).order_by(Appointment.start_time).all()
    
    @staticmethod
    def get_upcoming_appointments(user_id, role):
        """Get upcoming appointments for a user based on their role
        
        Args:
            user_id (int): ID of the user
            role (str): Role of the user (patient, specialist, doctor)
            
        Returns:
            list: List of upcoming appointments
        """
        now = datetime.utcnow()
        
        if role == 'patient':
            return Appointment.query.filter(
                Appointment.patient_id == user_id,
                Appointment.start_time >= now,
                Appointment.status == AppointmentStatus.SCHEDULED
            ).order_by(Appointment.start_time).all()
        
        elif role == 'specialist':
            return Appointment.query.filter(
                Appointment.specialist_id == user_id,
                Appointment.start_time >= now,
                Appointment.status == AppointmentStatus.SCHEDULED
            ).order_by(Appointment.start_time).all()
        
        elif role == 'doctor':
            # For referring doctors, get appointments for their referrals
            referrals = Referral.query.filter_by(user_id=user_id).all()
            referral_ids = [r.id for r in referrals]
            
            if not referral_ids:
                return []
            
            return Appointment.query.filter(
                Appointment.referral_id.in_(referral_ids),
                Appointment.start_time >= now,
                Appointment.status == AppointmentStatus.SCHEDULED
            ).order_by(Appointment.start_time).all()
        
        else:
            return []
    
    @staticmethod
    def _validate_appointment_data(appointment_data):
        """Validate appointment data
        
        Args:
            appointment_data (dict): Appointment data to validate
            
        Raises:
            ValueError: If validation fails
        """
        required_fields = ['patient_id', 'specialist_id', 'title', 'start_time', 'end_time', 'created_by']
        for field in required_fields:
            if field not in appointment_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate patient exists
        patient = User.query.get(appointment_data['patient_id'])
        if not patient:
            raise ValueError(f"Patient with ID {appointment_data['patient_id']} not found")
        
        # Validate specialist exists
        specialist = User.query.get(appointment_data['specialist_id'])
        if not specialist or specialist.role != 'specialist':
            raise ValueError(f"Specialist with ID {appointment_data['specialist_id']} not found")
        
        # Validate creator exists
        creator = User.query.get(appointment_data['created_by'])
        if not creator:
            raise ValueError(f"Creator with ID {appointment_data['created_by']} not found")
        
        # Validate referral if provided
        if 'referral_id' in appointment_data and appointment_data['referral_id']:
            referral = Referral.query.get(appointment_data['referral_id'])
            if not referral:
                raise ValueError(f"Referral with ID {appointment_data['referral_id']} not found")
        
        # Validate times
        start_time = appointment_data['start_time']
        end_time = appointment_data['end_time']
        
        if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
            raise ValueError("Start time and end time must be datetime objects")
        
        if start_time >= end_time:
            raise ValueError("Start time must be before end time")
        
        if start_time < datetime.utcnow():
            raise ValueError("Cannot create appointments in the past")
        
        # Validate duration (minimum 15 minutes, maximum 4 hours)
        duration = (end_time - start_time).total_seconds() / 60
        if duration < 15:
            raise ValueError("Appointment must be at least 15 minutes long")
        if duration > 240:
            raise ValueError("Appointment cannot be longer than 4 hours")