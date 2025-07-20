"""
Availability service for managing specialist availability
"""

from datetime import datetime, time, timedelta
from models import db, Availability, User
from sqlalchemy import and_, or_, func

class AvailabilityService:
    """Service for managing specialist availability"""
    
    @staticmethod
    def set_availability(specialist_id, availability_data):
        """Set availability for a specialist
        
        Args:
            specialist_id (int): ID of the specialist
            availability_data (dict): Availability data including day_of_week/specific_date, start_time, end_time
            
        Returns:
            Availability: The created availability
        """
        # Validate specialist exists and is a specialist
        specialist = User.query.get(specialist_id)
        if not specialist or specialist.role != 'specialist':
            raise ValueError(f"Specialist with ID {specialist_id} not found")
        
        # Validate availability data
        AvailabilityService._validate_availability_data(availability_data)
        
        # Create availability
        availability = Availability(
            specialist_id=specialist_id,
            day_of_week=availability_data.get('day_of_week'),
            start_time=availability_data['start_time'],
            end_time=availability_data['end_time'],
            is_recurring=availability_data.get('is_recurring', True),
            specific_date=availability_data.get('specific_date')
        )
        
        db.session.add(availability)
        db.session.commit()
        
        return availability
    
    @staticmethod
    def get_availability(specialist_id, date=None):
        """Get availability for a specialist
        
        Args:
            specialist_id (int): ID of the specialist
            date (date): Optional specific date to get availability for
            
        Returns:
            list: List of availability slots
        """
        # If date is provided, get availability for that specific date
        if date:
            # Get day of week (0 = Monday, 6 = Sunday)
            day_of_week = date.weekday()
            
            # Get recurring availability for this day of week
            recurring_availability = Availability.query.filter(
                Availability.specialist_id == specialist_id,
                Availability.is_recurring == True,
                Availability.day_of_week == day_of_week
            ).all()
            
            # Get specific availability for this date
            specific_availability = Availability.query.filter(
                Availability.specialist_id == specialist_id,
                Availability.is_recurring == False,
                Availability.specific_date == date
            ).all()
            
            # Combine both types of availability
            return recurring_availability + specific_availability
        
        # If no date is provided, get all availability
        return Availability.query.filter_by(specialist_id=specialist_id).all()
    
    @staticmethod
    def remove_availability(availability_id):
        """Remove an availability slot
        
        Args:
            availability_id (int): ID of the availability to remove
            
        Returns:
            bool: True if removed, False if not found
        """
        availability = Availability.query.get(availability_id)
        if not availability:
            return False
        
        db.session.delete(availability)
        db.session.commit()
        return True
    
    @staticmethod
    def get_available_specialists(date, specialty=None):
        """Get specialists available on a specific date
        
        Args:
            date (date): Date to check availability for
            specialty (str): Optional specialty to filter by
            
        Returns:
            list: List of available specialists
        """
        # Get day of week (0 = Monday, 6 = Sunday)
        day_of_week = date.weekday()
        
        # Find specialists with availability on this day
        query = db.session.query(User).join(
            Availability, User.id == Availability.specialist_id
        ).filter(
            User.role == 'specialist',
            or_(
                and_(
                    Availability.is_recurring == True,
                    Availability.day_of_week == day_of_week
                ),
                and_(
                    Availability.is_recurring == False,
                    Availability.specific_date == date
                )
            )
        ).distinct()
        
        # Filter by specialty if provided
        if specialty:
            query = query.filter(User.specialization == specialty)
        
        return query.all()
    
    @staticmethod
    def _validate_availability_data(availability_data):
        """Validate availability data
        
        Args:
            availability_data (dict): Availability data to validate
            
        Raises:
            ValueError: If validation fails
        """
        # Check required fields
        if 'start_time' not in availability_data or 'end_time' not in availability_data:
            raise ValueError("Missing required fields: start_time and end_time")
        
        # Validate times
        start_time = availability_data['start_time']
        end_time = availability_data['end_time']
        
        if not isinstance(start_time, time) or not isinstance(end_time, time):
            raise ValueError("Start time and end time must be time objects")
        
        if start_time >= end_time:
            raise ValueError("Start time must be before end time")
        
        # Validate recurring vs specific date
        is_recurring = availability_data.get('is_recurring', True)
        
        if is_recurring and 'day_of_week' not in availability_data:
            raise ValueError("Day of week is required for recurring availability")
        
        if not is_recurring and 'specific_date' not in availability_data:
            raise ValueError("Specific date is required for non-recurring availability")
        
        # Validate day of week
        if is_recurring:
            day_of_week = availability_data['day_of_week']
            if not isinstance(day_of_week, int) or day_of_week < 0 or day_of_week > 6:
                raise ValueError("Day of week must be an integer between 0 and 6")
        
        # Validate specific date
        if not is_recurring:
            specific_date = availability_data['specific_date']
            if not hasattr(specific_date, 'year'):  # Simple check if it's a date object
                raise ValueError("Specific date must be a date object")
            
            # Cannot set availability in the past
            if specific_date < datetime.utcnow().date():
                raise ValueError("Cannot set availability for past dates")