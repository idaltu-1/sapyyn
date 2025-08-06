import os
import logging
from supabase import create_client, Client
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class SupabaseClient:
    """
    A client for interacting with Supabase database and storage.
    This client replaces the NoCodeBackend functionality with Supabase APIs.
    """

    def __init__(self, supabase_url: str | None = None, supabase_key: str | None = None) -> None:
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL environment variable is not set")
        if not self.supabase_key:
            raise ValueError("SUPABASE_ANON_KEY environment variable is not set")
            
        # Initialize Supabase client
        self.client: Client = create_client(self.supabase_url, self.supabase_key)

    def create_record(self, table_name: str, data: dict) -> dict:
        """Create a new record in a Supabase table."""
        try:
            result = self.client.table(table_name).insert(data).execute()
            if result.data:
                return {
                    "success": True,
                    "data": result.data[0] if result.data else None,
                    "message": "Record created successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "No data returned from insert operation"
                }
        except Exception as e:
            logger.error(f"Error creating record in {table_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_records(self, table_name: str, params: dict | None = None) -> dict:
        """Retrieve records from a Supabase table."""
        try:
            query = self.client.table(table_name).select("*")
            
            # Apply filters if provided
            if params:
                for key, value in params.items():
                    if key == "limit":
                        query = query.limit(value)
                    elif key == "offset":
                        query = query.offset(value)
                    elif key == "order":
                        # order should be like "column:desc" or "column:asc"
                        if ":" in value:
                            column, direction = value.split(":")
                            ascending = direction.lower() == "asc"
                            query = query.order(column, desc=not ascending)
                        else:
                            query = query.order(value)
                    else:
                        # Simple equality filter
                        query = query.eq(key, value)
            
            result = query.execute()
            return {
                "success": True,
                "data": result.data,
                "count": len(result.data) if result.data else 0
            }
        except Exception as e:
            logger.error(f"Error fetching records from {table_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def update_record(self, table_name: str, record_id: str, data: dict) -> dict:
        """Update a record in a Supabase table."""
        try:
            result = self.client.table(table_name).update(data).eq("id", record_id).execute()
            if result.data:
                return {
                    "success": True,
                    "data": result.data[0] if result.data else None,
                    "message": "Record updated successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "No data returned from update operation"
                }
        except Exception as e:
            logger.error(f"Error updating record in {table_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def delete_record(self, table_name: str, record_id: str) -> dict:
        """Delete a record from a Supabase table."""
        try:
            result = self.client.table(table_name).delete().eq("id", record_id).execute()
            return {
                "success": True,
                "message": "Record deleted successfully"
            }
        except Exception as e:
            logger.error(f"Error deleting record from {table_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def upload_file(self, bucket_name: str, file_path: str, file_data: bytes, content_type: str = None) -> dict:
        """Upload a file to Supabase Storage."""
        try:
            # Upload file to storage
            result = self.client.storage.from_(bucket_name).upload(
                path=file_path,
                file=file_data,
                file_options={
                    "content-type": content_type or "application/octet-stream"
                }
            )
            
            if result:
                # Get public URL for the uploaded file
                public_url = self.client.storage.from_(bucket_name).get_public_url(file_path)
                
                return {
                    "success": True,
                    "data": {
                        "path": file_path,
                        "public_url": public_url
                    },
                    "message": "File uploaded successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "File upload failed"
                }
        except Exception as e:
            logger.error(f"Error uploading file to {bucket_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_file_url(self, bucket_name: str, file_path: str) -> str:
        """Get public URL for a file in Supabase Storage."""
        try:
            return self.client.storage.from_(bucket_name).get_public_url(file_path)
        except Exception as e:
            logger.error(f"Error getting file URL: {str(e)}")
            return None

    def delete_file(self, bucket_name: str, file_path: str) -> dict:
        """Delete a file from Supabase Storage."""
        try:
            result = self.client.storage.from_(bucket_name).remove([file_path])
            return {
                "success": True,
                "message": "File deleted successfully"
            }
        except Exception as e:
            logger.error(f"Error deleting file from {bucket_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    # Convenience methods for common operations
    def create_referral(self, data: dict) -> dict:
        """Create a new referral record."""
        return self.create_record("referrals", data)

    def get_referrals(self, params: dict | None = None) -> dict:
        """Get referral records with optional filtering."""
        return self.get_records("referrals", params)

    def update_referral(self, referral_id: str, data: dict) -> dict:
        """Update a referral record."""
        return self.update_record("referrals", referral_id, data)

    def create_document(self, data: dict) -> dict:
        """Create a new document record."""
        return self.create_record("documents", data)

    def get_documents(self, params: dict | None = None) -> dict:
        """Get document records with optional filtering."""
        return self.get_records("documents", params)

    def upload_document(self, file_name: str, file_data: bytes, content_type: str = None) -> dict:
        """Upload a document file to storage."""
        return self.upload_file("documents", file_name, file_data, content_type)