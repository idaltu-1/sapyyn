#!/usr/bin/env python3
"""
Cron job to expire outdated promotions
"""

import os
import sys
import logging
from datetime import datetime

# Add parent directory to path so we can import from the main app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db
from services.promotion_service import PromotionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/cron_expire_promotions.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('expire_promotions')

def main():
    """Main function to expire outdated promotions"""
    logger.info("Starting promotion expiration job")
    
    try:
        # Initialize database connection
        from app import app
        with app.app_context():
            # Expire outdated promotions
            expired_count = PromotionService.expire_outdated_promotions()
            logger.info(f"Expired {expired_count} outdated promotions")
            
            # Log current active promotions
            from models import Promotion
            active_count = Promotion.query.filter_by(is_active=True).count()
            logger.info(f"Currently {active_count} active promotions")
    
    except Exception as e:
        logger.error(f"Error expiring promotions: {str(e)}")
        return 1
    
    logger.info("Promotion expiration job completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())