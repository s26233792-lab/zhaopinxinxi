"""
Helper for connecting to existing Feishu tables.
This module helps analyze and connect to your existing table structure.
"""
from typing import Dict, List, Any, Optional
from loguru import logger

from .client import get_feishu_client


class ExistingTableAnalyzer:
    """
    Analyze existing Feishu table structure and help with field mapping.
    """

    def __init__(self):
        """Initialize the analyzer."""
        self.client = get_feishu_client()
        self._fields_cache: Optional[List[Dict[str, Any]]] = None

    def get_table_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about the existing table.

        Returns:
            Dictionary with table information
        """
        try:
            fields = self._get_fields()

            info = {
                "app_token": self.client.app_token,
                "table_id": self.client.table_id,
                "total_fields": len(fields),
                "fields": fields,
            }

            # Get record count
            records = self.client.get_records(page_size=1)
            info["total_records"] = records.get("data", {}).get("total", 0)

            return info

        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            return {}

    def _get_fields(self) -> List[Dict[str, Any]]:
        """Get and cache table fields."""
        if self._fields_cache is None:
            try:
                self._fields_cache = self.client.get_table_fields()
            except Exception as e:
                logger.error(f"Error getting fields: {e}")
                self._fields_cache = []
        return self._fields_cache

    def print_field_summary(self) -> None:
        """Print a summary of all fields in the table."""
        fields = self._get_fields()

        print("\n=== Feishu Table Field Summary ===\n")
        print(f"Total fields: {len(fields)}\n")

        for field in fields:
            field_id = field.get("field_id", "N/A")
            field_name = field.get("field_name", "N/A")
            field_type = field.get("type", "N/A")

            print(f"• {field_name} ({field_type})")
            print(f"  Field ID: {field_id}")

            # Print options for select/multiSelect fields
            if field_type in ["select", "multiSelect"]:
                options = field.get("property", {}).get("options", [])
                if options:
                    option_names = [opt.get("name", "") for opt in options]
                    print(f"  Options: {', '.join(option_names)}")

            print()

    def find_field_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Find a field by its display name.

        Args:
            name: Field display name to search for

        Returns:
            Field definition or None
        """
        fields = self._get_fields()

        for field in fields:
            if field.get("field_name") == name:
                return field

        return None

    def suggest_field_mapping(
        self, our_fields: List[str]
    ) -> Dict[str, Optional[str]]:
        """
        Suggest mapping between our internal fields and existing table fields.

        Args:
            our_fields: List of our internal field names

        Returns:
            Dictionary mapping our field names to Feishu field IDs
        """
        fields = self._get_fields()
        feishu_fields = {f.get("field_name"): f.get("field_id") for f in fields}

        mapping = {}
        for our_field in our_fields:
            # Try exact match first
            if our_field in feishu_fields:
                mapping[our_field] = feishu_fields[our_field]
            else:
                # Try partial match
                found = False
                for feishu_name, feishu_id in feishu_fields.items():
                    if our_field.lower() in feishu_name.lower() or feishu_name.lower() in our_field.lower():
                        mapping[our_field] = feishu_id
                        found = True
                        logger.info(f"Suggested mapping: {our_field} -> {feishu_name}")
                        break

                if not found:
                    mapping[our_field] = None
                    logger.warning(f"No matching field found for: {our_field}")

        return mapping

    def validate_field_mapping(self, mapping: Dict[str, str]) -> bool:
        """
        Validate that the field mapping is correct.

        Args:
            mapping: Dictionary mapping our field names to Feishu field IDs

        Returns:
            True if mapping is valid
        """
        fields = self._get_fields()
        valid_field_ids = {f.get("field_id") for f in fields}

        for our_field, feishu_field_id in mapping.items():
            if feishu_field_id and feishu_field_id not in valid_field_ids:
                logger.error(f"Invalid field ID for {our_field}: {feishu_field_id}")
                return False

        logger.info("Field mapping validation passed!")
        return True

    def get_sample_data(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get sample records from the table to understand data format.

        Args:
            limit: Number of sample records to get

        Returns:
            List of sample records
        """
        try:
            data = self.client.get_records(page_size=limit)
            return data.get("data", {}).get("items", [])
        except Exception as e:
            logger.error(f"Error getting sample data: {e}")
            return []


def analyze_existing_table() -> ExistingTableAnalyzer:
    """
    Analyze the existing Feishu table.

    Returns:
        ExistingTableAnalyzer instance
    """
    return ExistingTableAnalyzer()


def print_table_setup_instructions() -> None:
    """Print instructions for setting up Feishu credentials."""
    print("\n=== Feishu Table Setup Instructions ===\n")
    print("To connect to your existing Feishu table, you need:\n")
    print("1. App ID and App Secret:")
    print("   - Go to https://open.feishu.cn/app")
    print("   - Create a new app or use existing one")
    print("   - Copy App ID and App Secret from app credentials\n")
    print("2. App Token (for your existing table):")
    print("   - Open your Feishu Bitable")
    print("   - Click on the table you want to use")
    print("   - The app_token is in the URL after 'app/'")
    print("   - Example: https://example.feishu.cn/base/XXXXX/app/XXXXX/table/XXXXX")
    print("     The first XXXXX after 'app/' is your app_token\n")
    print("3. Table ID:")
    print("   - In the same URL, the last XXXXX after 'table/' is your table_id\n")
    print("4. Set environment variables:")
    print("   export FEISHU_APP_ID='your_app_id'")
    print("   export FEISHU_APP_SECRET='your_app_secret'")
    print("   export FEISHU_APP_TOKEN='your_app_token'")
    print("   export FEISHU_TABLE_ID='your_table_id'\n")
    print("5. Or create a .env file:")
    print("   FEISHU_APP_ID=your_app_id")
    print("   FEISHU_APP_SECRET=your_app_secret")
    print("   FEISHU_APP_TOKEN=your_app_token")
    print("   FEISHU_TABLE_ID=your_table_id\n")
