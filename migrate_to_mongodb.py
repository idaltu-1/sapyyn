#!/usr/bin/env python3
"""
Data migration script to migrate existing referral and document data to MongoDB
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mongodb_client import MongoDBClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataMigrator:
    """Handles migration from SQLite to MongoDB"""
    
    def __init__(self, sqlite_db_path='sapyyn.db', mongodb_url=None, mongodb_db=None):
        """Initialize the migrator
        
        Args:
            sqlite_db_path: Path to SQLite database
            mongodb_url: MongoDB connection URL
            mongodb_db: MongoDB database name
        """
        self.sqlite_db_path = sqlite_db_path
        self.mongodb_client = MongoDBClient(mongodb_url, mongodb_db)
        
    def migrate_referrals(self):
        """Migrate referrals from SQLite to MongoDB"""
        logger.info("Starting referral migration...")
        
        try:
            # Connect to SQLite
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            # Get all referrals
            cursor.execute('''
                SELECT 
                    id, user_id, referral_id, patient_name, referring_doctor, 
                    target_doctor, medical_condition, urgency_level, status,
                    notes, qr_code, created_at, updated_at, case_status,
                    consultation_date, case_accepted_date, treatment_start_date,
                    treatment_complete_date, rejection_reason, estimated_value,
                    actual_value, patient_id, dentist_id
                FROM referrals
            ''')
            
            referrals = cursor.fetchall()
            conn.close()
            
            logger.info(f"Found {len(referrals)} referrals to migrate")
            
            # Migrate each referral
            migrated_count = 0
            failed_count = 0
            
            for referral in referrals:
                try:
                    # Convert to dict
                    referral_data = {
                        'sqlite_id': referral[0],  # Keep original ID for reference
                        'user_id': str(referral[1]) if referral[1] else None,
                        'referral_id': referral[2],
                        'patient_name': referral[3],
                        'referring_doctor': referral[4],
                        'target_doctor': referral[5],
                        'medical_condition': referral[6],
                        'urgency_level': referral[7] or 'normal',
                        'status': referral[8] or 'pending',
                        'notes': referral[9],
                        'qr_code': referral[10],
                        'created_at': datetime.fromisoformat(referral[11]) if referral[11] else datetime.utcnow(),
                        'updated_at': datetime.fromisoformat(referral[12]) if referral[12] else datetime.utcnow(),
                        'case_status': referral[13],
                        'consultation_date': datetime.fromisoformat(referral[14]) if referral[14] else None,
                        'case_accepted_date': datetime.fromisoformat(referral[15]) if referral[15] else None,
                        'treatment_start_date': datetime.fromisoformat(referral[16]) if referral[16] else None,
                        'treatment_complete_date': datetime.fromisoformat(referral[17]) if referral[17] else None,
                        'rejection_reason': referral[18],
                        'estimated_value': float(referral[19]) if referral[19] else None,
                        'actual_value': float(referral[20]) if referral[20] else None,
                        'patient_id': str(referral[21]) if referral[21] else None,
                        'dentist_id': str(referral[22]) if referral[22] else None
                    }
                    
                    # Remove None values
                    referral_data = {k: v for k, v in referral_data.items() if v is not None}
                    
                    # Create in MongoDB
                    result = self.mongodb_client.create_referral(referral_data)
                    
                    if result.get('success'):
                        migrated_count += 1
                        if migrated_count % 10 == 0:
                            logger.info(f"Migrated {migrated_count} referrals...")
                    else:
                        logger.error(f"Failed to migrate referral {referral[0]}: {result.get('error')}")
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error migrating referral {referral[0]}: {e}")
                    failed_count += 1
            
            logger.info(f"Referral migration completed: {migrated_count} migrated, {failed_count} failed")
            return migrated_count, failed_count
            
        except Exception as e:
            logger.error(f"Error during referral migration: {e}")
            return 0, len(referrals) if 'referrals' in locals() else 0
    
    def migrate_documents(self):
        """Migrate documents from SQLite to MongoDB"""
        logger.info("Starting document migration...")
        
        try:
            # Connect to SQLite
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            # Get all documents
            cursor.execute('''
                SELECT 
                    id, referral_id, user_id, file_type, file_name, 
                    file_path, file_size, upload_date
                FROM documents
            ''')
            
            documents = cursor.fetchall()
            conn.close()
            
            logger.info(f"Found {len(documents)} documents to migrate")
            
            # Migrate each document
            migrated_count = 0
            failed_count = 0
            
            for document in documents:
                try:
                    # Convert to dict
                    document_data = {
                        'sqlite_id': document[0],  # Keep original ID for reference
                        'referral_id': str(document[1]) if document[1] else None,
                        'user_id': str(document[2]) if document[2] else None,
                        'file_type': document[3],
                        'filename': document[4],
                        'file_path': document[5],
                        'file_size': document[6],
                        'upload_date': datetime.fromisoformat(document[7]) if document[7] else datetime.utcnow(),
                        'migrated_from_sqlite': True
                    }
                    
                    # Remove None values
                    document_data = {k: v for k, v in document_data.items() if v is not None}
                    
                    # For actual file data migration, you would need to:
                    # 1. Read the file from file_path
                    # 2. Upload it using upload_document method
                    # For now, we'll just migrate the metadata
                    
                    # Create in MongoDB
                    result = self.mongodb_client.create_document(document_data)
                    
                    if result.get('success'):
                        migrated_count += 1
                        if migrated_count % 10 == 0:
                            logger.info(f"Migrated {migrated_count} documents...")
                    else:
                        logger.error(f"Failed to migrate document {document[0]}: {result.get('error')}")
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error migrating document {document[0]}: {e}")
                    failed_count += 1
            
            logger.info(f"Document migration completed: {migrated_count} migrated, {failed_count} failed")
            return migrated_count, failed_count
            
        except Exception as e:
            logger.error(f"Error during document migration: {e}")
            return 0, len(documents) if 'documents' in locals() else 0
    
    def migrate_all(self):
        """Migrate all data"""
        logger.info("Starting full data migration from SQLite to MongoDB")
        
        total_migrated = 0
        total_failed = 0
        
        # Check if SQLite database exists
        if not os.path.exists(self.sqlite_db_path):
            logger.warning(f"SQLite database not found at {self.sqlite_db_path}")
            return total_migrated, total_failed
        
        # Migrate referrals
        ref_migrated, ref_failed = self.migrate_referrals()
        total_migrated += ref_migrated
        total_failed += ref_failed
        
        # Migrate documents
        doc_migrated, doc_failed = self.migrate_documents()
        total_migrated += doc_migrated
        total_failed += doc_failed
        
        logger.info(f"Migration completed: {total_migrated} items migrated, {total_failed} failed")
        return total_migrated, total_failed

def main():
    """Main migration function"""
    # Get configuration from environment
    sqlite_db = os.getenv('DATABASE_NAME', 'sapyyn.db')
    mongodb_url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/sapyyn')
    mongodb_db = os.getenv('MONGODB_DB_NAME', 'sapyyn')
    
    logger.info(f"Starting migration from {sqlite_db} to MongoDB")
    logger.info(f"MongoDB URL: {mongodb_url}")
    logger.info(f"MongoDB DB: {mongodb_db}")
    
    try:
        # Create migrator and run migration
        migrator = DataMigrator(sqlite_db, mongodb_url, mongodb_db)
        migrated, failed = migrator.migrate_all()
        
        if failed == 0:
            logger.info("✅ Migration completed successfully!")
        else:
            logger.warning(f"⚠️ Migration completed with {failed} failures. Check migration.log for details.")
        
        # Close MongoDB connection
        migrator.mongodb_client.close()
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()