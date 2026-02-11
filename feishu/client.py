"""
Feishu API client for connecting to existing tables.
"""
import time
import httpx
from typing import Dict, List, Any, Optional
from loguru import logger

from config.settings import (
    FEISHU_APP_ID,
    FEISHU_APP_SECRET,
    FEISHU_APP_TOKEN,
    FEISHU_TABLE_ID,
    FEISHU_API_BASE_URL,
)


class FeishuClient:
    """
    Client for interacting with Feishu Bitable API.
    Handles authentication and API calls to existing Feishu tables.
    """

    def __init__(
        self,
        app_id: str = None,
        app_secret: str = None,
        app_token: str = None,
        table_id: str = None,
    ):
        """
        Initialize Feishu client.

        Args:
            app_id: Feishu app ID
            app_secret: Feishu app secret
            app_token: Feishu app token (for existing table)
            table_id: Feishu table ID
        """
        self.app_id = app_id or FEISHU_APP_ID
        self.app_secret = app_secret or FEISHU_APP_SECRET
        self.app_token = app_token or FEISHU_APP_TOKEN
        self.table_id = table_id or FEISHU_TABLE_ID
        self.base_url = FEISHU_API_BASE_URL

        self._tenant_access_token: Optional[str] = None
        self._token_expires_at: float = 0

        if not all([self.app_id, self.app_secret, self.app_token, self.table_id]):
            logger.warning(
                "Feishu credentials not fully configured. "
                "Please set FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_APP_TOKEN, and FEISHU_TABLE_ID."
            )

    def _get_tenant_access_token(self) -> str:
        """
        Get or refresh tenant access token.

        Returns:
            Tenant access token
        """
        # Check if token is still valid (with 5 min buffer)
        if self._tenant_access_token and time.time() < self._token_expires_at - 300:
            return self._tenant_access_token

        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"

        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }

        try:
            response = httpx.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            if data.get("code") != 0:
                raise Exception(f"Failed to get tenant access token: {data.get('msg')}")

            self._tenant_access_token = data.get("tenant_access_token")
            expire = data.get("expire", 7200)
            self._token_expires_at = time.time() + expire

            logger.info("Successfully obtained tenant access token")
            return self._tenant_access_token

        except Exception as e:
            logger.error(f"Error getting tenant access token: {e}")
            raise

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any] = None,
        json_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to Feishu API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON request body

        Returns:
            API response data
        """
        token = self._get_tenant_access_token()
        url = f"{self.base_url}{endpoint}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            if method.upper() == "GET":
                response = httpx.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = httpx.post(url, headers=headers, json=json_data, timeout=30)
            elif method.upper() == "PATCH":
                response = httpx.patch(url, headers=headers, json=json_data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            data = response.json()

            if data.get("code") != 0:
                logger.warning(f"API returned error: {data.get('msg')}")
                return data

            return data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise

    def get_table_fields(self) -> List[Dict[str, Any]]:
        """
        Get all fields from the table.

        Returns:
            List of field definitions
        """
        endpoint = f"/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"

        data = self._make_request("GET", endpoint)
        return data.get("data", {}).get("items", [])

    def get_records(
        self,
        page_size: int = 100,
        page_token: str = None,
        filter_condition: Dict[str, Any] = None,
        sort: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Get records from the table.

        Args:
            page_size: Number of records per page (max 500)
            page_token: Token for pagination
            filter_condition: Filter conditions
            sort: Sort conditions

        Returns:
            Dictionary with records and pagination info
        """
        endpoint = f"/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"

        params = {"page_size": min(page_size, 500)}

        if page_token:
            params["page_token"] = page_token

        if filter_condition:
            params["filter"] = filter_condition

        if sort:
            params["sort"] = sort

        data = self._make_request("GET", endpoint, params=params)
        return data.get("data", {})

    def get_all_records(self) -> List[Dict[str, Any]]:
        """
        Get all records from the table (handles pagination automatically).

        Returns:
            List of all records
        """
        all_records = []
        page_token = None

        while True:
            result = self.get_records(page_size=500, page_token=page_token)
            records = result.get("items", [])
            all_records.extend(records)

            page_token = result.get("page_token")
            if not page_token or not result.get("has_more"):
                break

            logger.info(f"Fetched {len(all_records)} records so far...")

        logger.info(f"Total records fetched: {len(all_records)}")
        return all_records

    def create_record(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a single record in the table.

        Args:
            fields: Record fields dictionary

        Returns:
            Created record data
        """
        endpoint = f"/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"

        data = self._make_request("POST", endpoint, json_data={"fields": fields})
        return data.get("data", {})

    def batch_create_records(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple records in the table (max 500 per batch).

        Args:
            records: List of record field dictionaries

        Returns:
            Batch create result
        """
        endpoint = f"/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/batch_create"

        # Split into batches of 500
        batch_size = 500
        all_results = []

        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            data = self._make_request("POST", endpoint, json_data={"records": batch})
            all_results.append(data)
            logger.info(f"Created batch {i // batch_size + 1}: {len(batch)} records")

        return {"data": {"results": all_results}}

    def update_record(self, record_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a single record in the table.

        Args:
            record_id: Feishu record ID
            fields: Fields to update

        Returns:
            Updated record data
        """
        endpoint = f"/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/{record_id}"

        data = self._make_request("PATCH", endpoint, json_data={"fields": fields})
        return data.get("data", {})

    def batch_update_records(
        self, updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Update multiple records in the table (max 500 per batch).

        Args:
            updates: List of dictionaries with record_id and fields

        Returns:
            Batch update result
        """
        endpoint = f"/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/batch_update"

        # Split into batches of 500
        batch_size = 500
        all_results = []

        for i in range(0, len(updates), batch_size):
            batch = updates[i : i + batch_size]
            data = self._make_request("POST", endpoint, json_data={"records": batch})
            all_results.append(data)
            logger.info(f"Updated batch {i // batch_size + 1}: {len(batch)} records")

        return {"data": {"results": all_results}}

    def find_record_by_fields(
        self, field_conditions: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Find a record that matches the given field conditions.

        Args:
            field_conditions: Dictionary of field names and values to match

        Returns:
            Matching record or None
        """
        # Build filter condition for API
        # Note: Feishu's filter format is specific, this is a simplified version
        all_records = self.get_all_records()

        for record in all_records:
            fields = record.get("fields", {})
            match = True
            for field_name, expected_value in field_conditions.items():
                if fields.get(field_name) != expected_value:
                    match = False
                    break

            if match:
                return record

        return None

    def test_connection(self) -> bool:
        """
        Test the connection to Feishu API.

        Returns:
            True if connection is successful
        """
        try:
            fields = self.get_table_fields()
            logger.info(f"Connection successful! Found {len(fields)} fields in table.")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


# Singleton instance
_client_instance: Optional[FeishuClient] = None


def get_feishu_client() -> FeishuClient:
    """Get or create the singleton Feishu client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = FeishuClient()
    return _client_instance
