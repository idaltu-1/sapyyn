import os
import requests

class NoCodeBackendClient:
    """
    A simple client for interacting with NoCodeBackend databases.
    This client uses environment variables to configure the secret key and instance names.
    """

    def __init__(self, secret_key: str | None = None) -> None:
        self.base_url = "https://api.nocodebackend.com"
        self.secret_key = secret_key or os.getenv("NOCODEBACKEND_SECRET_KEY")
        if not self.secret_key:
            raise ValueError("NOCODEBACKEND_SECRET_KEY environment variable is not set")
        # Instances for referrals and website uploads
        self.referral_instance = os.getenv("NOCODEBACKEND_REFERRAL_INSTANCE")
        self.uploads_instance = os.getenv("NOCODEBACKEND_UPLOADS_INSTANCE")

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    def create_record(self, instance_name: str, table_name: str, data: dict) -> dict:
        """Create a new record in a NoCodeBackend table."""
        url = f"{self.base_url}/v1/{instance_name}/{table_name}"
        response = requests.post(url, headers=self._get_headers(), json=data)
        response.raise_for_status()
        return response.json()

    def get_records(self, instance_name: str, table_name: str, params: dict | None = None) -> dict:
        """Retrieve records from a NoCodeBackend table."""
        url = f"{self.base_url}/v1/{instance_name}/{table_name}"
        response = requests.get(url, headers=self._get_headers(), params=params or {})
        response.raise_for_status()
        return response.json()

    # Convenience methods for common operations
    def create_referral(self, data: dict) -> dict:
        """Create a new referral record using the configured referral instance."""
        if not self.referral_instance:
            raise ValueError("NOCODEBACKEND_REFERRAL_INSTANCE is not set")
        return self.create_record(self.referral_instance, "referrals", data)

    def create_upload(self, data: dict) -> dict:
        """Create a new upload record using the configured uploads instance."""
        if not self.uploads_instance:
            raise ValueError("NOCODEBACKEND_UPLOADS_INSTANCE is not set")
        return self.create_record(self.uploads_instance, "uploads", data)
