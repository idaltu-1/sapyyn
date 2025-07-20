"""
Promotion service for managing promotional content
"""

from datetime import datetime
from models import db, Promotion, PromotionRole, UserPromotionPreference, User
from sqlalchemy import func
import random
import logging

class PromotionService:
    """Service for managing promotions"""
    
    @staticmethod
    def create_promotion(promotion_data):
        """Create a new promotion
        
        Args:
            promotion_data (dict): Promotion data including title, image_url, target_url, etc.
            
        Returns:
            Promotion: The created promotion
        """
        promotion = Promotion(
            title=promotion_data['title'],
            description=promotion_data.get('description'),
            image_url=promotion_data['image_url'],
            target_url=promotion_data['target_url'],
            location=promotion_data['location'],
            start_date=promotion_data['start_date'],
            end_date=promotion_data['end_date'],
            is_active=promotion_data.get('is_active', True)
        )
        
        db.session.add(promotion)
        db.session.flush()  # Get the ID without committing
        
        # Add allowed roles if provided
        if 'allowed_roles' in promotion_data and promotion_data['allowed_roles']:
            for role in promotion_data['allowed_roles']:
                promotion_role = PromotionRole(promotion_id=promotion.id, role=role)
                db.session.add(promotion_role)
        
        db.session.commit()
        return promotion
    
    @staticmethod
    def update_promotion(promotion_id, promotion_data):
        """Update an existing promotion
        
        Args:
            promotion_id (int): ID of the promotion to update
            promotion_data (dict): Updated promotion data
            
        Returns:
            Promotion: The updated promotion or None if not found
        """
        promotion = Promotion.query.get(promotion_id)
        if not promotion:
            return None
        
        # Update basic fields
        if 'title' in promotion_data:
            promotion.title = promotion_data['title']
        if 'description' in promotion_data:
            promotion.description = promotion_data['description']
        if 'image_url' in promotion_data:
            promotion.image_url = promotion_data['image_url']
        if 'target_url' in promotion_data:
            promotion.target_url = promotion_data['target_url']
        if 'location' in promotion_data:
            promotion.location = promotion_data['location']
        if 'start_date' in promotion_data:
            promotion.start_date = promotion_data['start_date']
        if 'end_date' in promotion_data:
            promotion.end_date = promotion_data['end_date']
        if 'is_active' in promotion_data:
            promotion.is_active = promotion_data['is_active']
        
        # Update allowed roles if provided
        if 'allowed_roles' in promotion_data:
            # Remove existing roles
            PromotionRole.query.filter_by(promotion_id=promotion.id).delete()
            
            # Add new roles
            for role in promotion_data['allowed_roles']:
                promotion_role = PromotionRole(promotion_id=promotion.id, role=role)
                db.session.add(promotion_role)
        
        promotion.updated_at = datetime.utcnow()
        db.session.commit()
        return promotion
    
    @staticmethod
    def get_promotion(promotion_id):
        """Get a promotion by ID
        
        Args:
            promotion_id (int): ID of the promotion
            
        Returns:
            Promotion: The promotion or None if not found
        """
        return Promotion.query.get(promotion_id)
    
    @staticmethod
    def list_promotions(filters=None):
        """List promotions with optional filters
        
        Args:
            filters (dict): Optional filters like is_active, location, etc.
            
        Returns:
            list: List of promotions matching the filters
        """
        query = Promotion.query
        
        if filters:
            if 'is_active' in filters:
                query = query.filter(Promotion.is_active == filters['is_active'])
            if 'location' in filters:
                query = query.filter(Promotion.location == filters['location'])
            if 'start_date_after' in filters:
                query = query.filter(Promotion.start_date >= filters['start_date_after'])
            if 'end_date_before' in filters:
                query = query.filter(Promotion.end_date <= filters['end_date_before'])
        
        return query.order_by(Promotion.created_at.desc()).all()
    
    @staticmethod
    def delete_promotion(promotion_id):
        """Delete a promotion
        
        Args:
            promotion_id (int): ID of the promotion to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        promotion = Promotion.query.get(promotion_id)
        if not promotion:
            return False
        
        db.session.delete(promotion)
        db.session.commit()
        return True
    
    @staticmethod
    def toggle_promotion_status(promotion_id, is_active):
        """Activate or deactivate a promotion
        
        Args:
            promotion_id (int): ID of the promotion
            is_active (bool): New active status
            
        Returns:
            Promotion: The updated promotion or None if not found
        """
        promotion = Promotion.query.get(promotion_id)
        if not promotion:
            return None
        
        promotion.is_active = is_active
        promotion.updated_at = datetime.utcnow()
        db.session.commit()
        return promotion
    
    @staticmethod
    def get_promotion_for_location(location, user=None):
        """Get an appropriate promotion for the given location and user
        
        Uses weighted round-robin selection based on impression count
        
        Args:
            location (PromotionLocation): Location to get promotion for
            user (User): Optional user to personalize promotion
            
        Returns:
            Promotion: Selected promotion or None if none available
        """
        now = datetime.utcnow()
        
        # Base query for active promotions at this location
        query = Promotion.query.filter(
            Promotion.location == location,
            Promotion.is_active == True,
            Promotion.start_date <= now,
            Promotion.end_date >= now
        )
        
        # Filter by user role if user is provided
        if user:
            # Check if user has opted out
            user_prefs = UserPromotionPreference.query.filter_by(user_id=user.id).first()
            if user_prefs and user_prefs.opt_out:
                # Return None or a house ad
                return None
            
            # Get promotions that either have no role restrictions or match this user's role
            role_specific_promo_ids = db.session.query(PromotionRole.promotion_id).filter_by(role=user.role).all()
            role_specific_promo_ids = [r[0] for r in role_specific_promo_ids]
            
            # Get promotions with no role restrictions
            no_role_promo_ids = db.session.query(Promotion.id).outerjoin(
                PromotionRole, Promotion.id == PromotionRole.promotion_id
            ).filter(PromotionRole.id == None).all()
            no_role_promo_ids = [r[0] for r in no_role_promo_ids]
            
            # Combine both sets of IDs
            allowed_promo_ids = role_specific_promo_ids + no_role_promo_ids
            if allowed_promo_ids:
                query = query.filter(Promotion.id.in_(allowed_promo_ids))
        
        # Get all eligible promotions
        promotions = query.all()
        if not promotions:
            return None
        
        # Weighted selection based on inverse of impression count
        # (fewer impressions = higher chance of selection)
        total_impressions = sum(p.impression_count for p in promotions) or len(promotions)
        weights = []
        
        for promo in promotions:
            # Base weight is inverse of impression share
            weight = 1 - (promo.impression_count / total_impressions) if total_impressions > 0 else 1
            # Ensure minimum weight
            weight = max(0.1, weight)
            weights.append(weight)
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        else:
            weights = [1 / len(promotions)] * len(promotions)
        
        # Select promotion based on weights
        selected_promotion = random.choices(promotions, weights=weights, k=1)[0]
        return selected_promotion
    
    @staticmethod
    def record_impression(promotion_id):
        """Increment impression count for a promotion
        Uses an isolated transaction to avoid any connection to PHI
        
        Args:
            promotion_id (int): ID of the promotion
            
        Returns:
            bool: True if successful, False if promotion not found
        """
        try:
            # Use atomic update to avoid race conditions
            result = db.session.query(Promotion).filter(
                Promotion.id == promotion_id
            ).update(
                {Promotion.impression_count: Promotion.impression_count + 1},
                synchronize_session=False
            )
            db.session.commit()
            return result > 0
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error recording impression: {str(e)}")
            return False
    
    @staticmethod
    def record_click(promotion_id):
        """Increment click count for a promotion
        Uses an isolated transaction to avoid any connection to PHI
        
        Args:
            promotion_id (int): ID of the promotion
            
        Returns:
            bool: True if successful, False if promotion not found
        """
        try:
            # Use atomic update to avoid race conditions
            result = db.session.query(Promotion).filter(
                Promotion.id == promotion_id
            ).update(
                {Promotion.click_count: Promotion.click_count + 1},
                synchronize_session=False
            )
            db.session.commit()
            return result > 0
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error recording click: {str(e)}")
            return False
    
    @staticmethod
    def expire_outdated_promotions():
        """Deactivate promotions past their end date
        
        Returns:
            int: Number of promotions deactivated
        """
        now = datetime.utcnow()
        result = db.session.query(Promotion).filter(
            Promotion.is_active == True,
            Promotion.end_date < now
        ).update(
            {Promotion.is_active: False},
            synchronize_session=False
        )
        
        db.session.commit()
        return result