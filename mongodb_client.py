"""
MongoDB client for Sapyyn application - replaces NoCodeBackend
"""

import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class MongoDBClient:
    """
    MongoDB client for Sapyyn application.
    Replaces the NoCodeBackend functionality with native MongoDB operations.
    """

    def __init__(self, mongo_url: Optional[str] = None, db_name: Optional[str] = None) -> None:
        """
        Initialize MongoDB client
        
        Args:
            mongo_url: MongoDB connection URL
            db_name: Database name
        """
        self.mongo_url = mongo_url or os.getenv("MONGODB_URL", "mongodb://localhost:27017/sapyyn")
        self.db_name = db_name or os.getenv("MONGODB_DB_NAME", "sapyyn")
        
        try:
            self.client = MongoClient(self.mongo_url)
            self.db = self.client[self.db_name]
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {self.db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise ValueError(f"Could not connect to MongoDB: {e}")

    def create_record(self, collection_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new record in a MongoDB collection.
        
        Args:
            collection_name: Name of the collection
            data: Data to insert
            
        Returns:
            Dictionary containing the created record with its ID
        """
        try:
            collection = self.db[collection_name]
            
            # Add created_at timestamp if not present
            if 'created_at' not in data:
                data['created_at'] = datetime.utcnow()
            
            # Add updated_at timestamp
            data['updated_at'] = datetime.utcnow()
            
            # Insert the record
            result = collection.insert_one(data)
            
            # Return the created record
            created_record = collection.find_one({'_id': result.inserted_id})
            
            # Convert ObjectId to string for JSON serialization
            if created_record:
                created_record['_id'] = str(created_record['_id'])
            
            return {
                'success': True,
                'data': created_record,
                'id': str(result.inserted_id)
            }
            
        except PyMongoError as e:
            logger.error(f"Error creating record in {collection_name}: {e}")
            return {'success': False, 'error': str(e)}

    def get_records(self, collection_name: str, query: Optional[Dict[str, Any]] = None, 
                   limit: int = 100, skip: int = 0) -> Dict[str, Any]:
        """
        Retrieve records from a MongoDB collection.
        
        Args:
            collection_name: Name of the collection
            query: Query filters
            limit: Maximum number of records to return
            skip: Number of records to skip
            
        Returns:
            Dictionary containing the retrieved records
        """
        try:
            collection = self.db[collection_name]
            
            # Build query
            mongo_query = query or {}
            
            # Convert string ObjectId to ObjectId object if _id is in query
            if '_id' in mongo_query and isinstance(mongo_query['_id'], str):
                mongo_query['_id'] = ObjectId(mongo_query['_id'])
            
            # Execute query
            cursor = collection.find(mongo_query).skip(skip).limit(limit)
            records = list(cursor)
            
            # Convert ObjectIds to strings
            for record in records:
                if '_id' in record:
                    record['_id'] = str(record['_id'])
            
            # Get total count
            total_count = collection.count_documents(mongo_query)
            
            return {
                'success': True,
                'data': records,
                'count': len(records),
                'total': total_count,
                'skip': skip,
                'limit': limit
            }
            
        except PyMongoError as e:
            logger.error(f"Error getting records from {collection_name}: {e}")
            return {'success': False, 'error': str(e)}

    def get_record(self, collection_name: str, record_id: str) -> Dict[str, Any]:
        """
        Retrieve a single record by ID.
        
        Args:
            collection_name: Name of the collection
            record_id: ID of the record
            
        Returns:
            Dictionary containing the record
        """
        try:
            collection = self.db[collection_name]
            
            # Convert string to ObjectId
            try:
                object_id = ObjectId(record_id)
            except:
                return {'success': False, 'error': 'Invalid record ID format'}
            
            # Find the record
            record = collection.find_one({'_id': object_id})
            
            if record:
                record['_id'] = str(record['_id'])
                return {'success': True, 'data': record}
            else:
                return {'success': False, 'error': 'Record not found'}
                
        except PyMongoError as e:
            logger.error(f"Error getting record from {collection_name}: {e}")
            return {'success': False, 'error': str(e)}

    def update_record(self, collection_name: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a record in MongoDB collection.
        
        Args:
            collection_name: Name of the collection
            record_id: ID of the record to update
            data: Updated data
            
        Returns:
            Dictionary containing the update result
        """
        try:
            collection = self.db[collection_name]
            
            # Convert string to ObjectId
            try:
                object_id = ObjectId(record_id)
            except:
                return {'success': False, 'error': 'Invalid record ID format'}
            
            # Add updated_at timestamp
            data['updated_at'] = datetime.utcnow()
            
            # Update the record
            result = collection.update_one(
                {'_id': object_id},
                {'$set': data}
            )
            
            if result.matched_count == 0:
                return {'success': False, 'error': 'Record not found'}
            
            # Get the updated record
            updated_record = collection.find_one({'_id': object_id})
            if updated_record:
                updated_record['_id'] = str(updated_record['_id'])
            
            return {
                'success': True,
                'data': updated_record,
                'modified_count': result.modified_count
            }
            
        except PyMongoError as e:
            logger.error(f"Error updating record in {collection_name}: {e}")
            return {'success': False, 'error': str(e)}

    def delete_record(self, collection_name: str, record_id: str) -> Dict[str, Any]:
        """
        Delete a record from MongoDB collection.
        
        Args:
            collection_name: Name of the collection
            record_id: ID of the record to delete
            
        Returns:
            Dictionary containing the delete result
        """
        try:
            collection = self.db[collection_name]
            
            # Convert string to ObjectId
            try:
                object_id = ObjectId(record_id)
            except:
                return {'success': False, 'error': 'Invalid record ID format'}
            
            # Delete the record
            result = collection.delete_one({'_id': object_id})
            
            if result.deleted_count == 0:
                return {'success': False, 'error': 'Record not found'}
            
            return {
                'success': True,
                'deleted_count': result.deleted_count
            }
            
        except PyMongoError as e:
            logger.error(f"Error deleting record from {collection_name}: {e}")
            return {'success': False, 'error': str(e)}

    def upload_file(self, file_data: bytes, file_name: str, content_type: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Store file data in MongoDB GridFS or as a document.
        For now, we'll store file metadata and save files to disk.
        
        Args:
            file_data: The file binary data
            file_name: Name of the file
            content_type: MIME type of the file
            metadata: Additional metadata
            
        Returns:
            Dictionary containing the file information
        """
        try:
            from gridfs import GridFS
            
            fs = GridFS(self.db)
            
            # Prepare metadata
            file_metadata = {
                'filename': file_name,
                'contentType': content_type,
                'uploadDate': datetime.utcnow(),
                **(metadata or {})
            }
            
            # Store file in GridFS
            file_id = fs.put(file_data, **file_metadata)
            
            # Get file info
            file_info = fs.get(file_id)
            
            return {
                'success': True,
                'data': {
                    '_id': str(file_id),
                    'filename': file_info.filename,
                    'contentType': file_info.content_type,
                    'length': file_info.length,
                    'uploadDate': file_info.upload_date,
                    'metadata': file_info.metadata or {}
                }
            }
            
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return {'success': False, 'error': str(e)}

    def get_file(self, file_id: str) -> Dict[str, Any]:
        """
        Retrieve file from MongoDB GridFS.
        
        Args:
            file_id: ID of the file
            
        Returns:
            Dictionary containing file data and metadata
        """
        try:
            from gridfs import GridFS
            from gridfs.errors import NoFile
            
            fs = GridFS(self.db)
            
            try:
                object_id = ObjectId(file_id)
            except:
                return {'success': False, 'error': 'Invalid file ID format'}
            
            try:
                file_obj = fs.get(object_id)
                file_data = file_obj.read()
                
                return {
                    'success': True,
                    'data': file_data,
                    'metadata': {
                        '_id': str(file_obj._id),
                        'filename': file_obj.filename,
                        'contentType': file_obj.content_type,
                        'length': file_obj.length,
                        'uploadDate': file_obj.upload_date
                    }
                }
                
            except NoFile:
                return {'success': False, 'error': 'File not found'}
                
        except Exception as e:
            logger.error(f"Error retrieving file: {e}")
            return {'success': False, 'error': str(e)}

    def close(self):
        """Close the MongoDB connection"""
        if hasattr(self, 'client'):
            self.client.close()
            logger.info("MongoDB connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # Convenience methods for common operations (maintaining compatibility with NoCodeBackend API)
    def create_referral(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new referral record."""
        return self.create_record("referrals", data)

    def get_referrals(self, query: Optional[Dict[str, Any]] = None, limit: int = 100, skip: int = 0) -> Dict[str, Any]:
        """Get referral records."""
        return self.get_records("referrals", query, limit, skip)

    def update_referral(self, referral_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a referral record."""
        return self.update_record("referrals", referral_id, data)

    def create_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document record."""
        return self.create_record("documents", data)

    def get_documents(self, query: Optional[Dict[str, Any]] = None, limit: int = 100, skip: int = 0) -> Dict[str, Any]:
        """Get document records."""
        return self.get_records("documents", query, limit, skip)