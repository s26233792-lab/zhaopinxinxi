"""
High-level Bitable operations for recruitment data.
"""
from typing import List, Dict, Any, Optional
from loguru import logger

from .client import FeishuClient, get_feishu_client
from config.feishu_config import FIELD_MAPPING, build_feishu_record


class RecruitmentTable:
    """
    High-level interface for managing recruitment data in Feishu Bitable.
    """

    def __init__(self, client: FeishuClient = None):
        """
        Initialize recruitment table manager.

        Args:
            client: Feishu client instance (uses singleton if not provided)
        """
        self.client = client or get_feishu_client()

    def add_recruitment(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Add a single recruitment record.

        Args:
            data: Recruitment data dictionary

        Returns:
            Record ID if successful, None otherwise
        """
        try:
            # Convert to Feishu format
            record = build_feishu_record(data)

            # Check for duplicates
            existing = self._find_duplicate(data)
            if existing:
                logger.info(f"Duplicate found, updating existing record: {existing.get('record_id')}")
                return self._update_record(existing.get("record_id"), data)

            # Create new record
            result = self.client.create_record(record.get("fields", {}))
            record_id = result.get("record", {}).get("record_id")

            if record_id:
                logger.info(f"Successfully created record: {record_id}")
                return record_id
            else:
                logger.warning(f"Failed to create record: {result}")
                return None

        except Exception as e:
            logger.error(f"Error adding recruitment: {e}")
            return None

    def add_recruitments(self, data_list: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Add multiple recruitment records in batch.

        Args:
            data_list: List of recruitment data dictionaries

        Returns:
            Dictionary with created, updated, and failed counts
        """
        result = {"created": 0, "updated": 0, "failed": 0, "skipped": 0}

        try:
            # Get existing records for deduplication check
            existing_records = self.client.get_all_records()
            existing_map = self._build_existing_map(existing_records)

            records_to_create = []
            records_to_update = []

            for data in data_list:
                # Check for duplicate
                duplicate_key = self._get_duplicate_key(data)
                existing = existing_map.get(duplicate_key)

                if existing:
                    # Update existing record
                    records_to_update.append(
                        {
                            "record_id": existing.get("record_id"),
                            "fields": build_feishu_record(data).get("fields", {}),
                        }
                    )
                else:
                    # Create new record
                    records_to_create.append(build_feishu_record(data).get("fields", {}))

            # Batch create new records
            if records_to_create:
                self.client.batch_create_records(records_to_create)
                result["created"] = len(records_to_create)

            # Batch update existing records
            if records_to_update:
                self.client.batch_update_records(records_to_update)
                result["updated"] = len(records_to_update)

            logger.info(
                f"Batch operation completed: {result['created']} created, "
                f"{result['updated']} updated"
            )

        except Exception as e:
            logger.error(f"Error in batch operation: {e}")
            result["failed"] = len(data_list)

        return result

    def get_all_recruitments(self) -> List[Dict[str, Any]]:
        """
        Get all recruitment records from the table.

        Returns:
            List of recruitment records
        """
        try:
            records = self.client.get_all_records()
            return records
        except Exception as e:
            logger.error(f"Error getting recruitments: {e}")
            return []

    def get_recent_recruitments(self, days: int = 1) -> List[Dict[str, Any]]:
        """
        Get recruitment records from the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of recent recruitment records
        """
        # This requires proper filtering with Feishu API
        # For now, get all and filter client-side
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        all_records = self.get_all_recruitments()

        recent = []
        for record in all_records:
            fields = record.get("fields", {})
            publish_date_str = fields.get(FIELD_MAPPING.get("publish_date", ""))
            if publish_date_str:
                try:
                    publish_date = datetime.fromisoformat(str(publish_date_str))
                    if publish_date >= cutoff_date:
                        recent.append(record)
                except:
                    pass

        return recent

    def _find_duplicate(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if a duplicate record exists.

        Args:
            data: Recruitment data

        Returns:
            Existing record if found, None otherwise
        """
        duplicate_key = self._get_duplicate_key(data)

        # Get existing records
        existing_records = self.client.get_all_records()
        existing_map = self._build_existing_map(existing_records)

        return existing_map.get(duplicate_key)

    def _get_duplicate_key(self, data: Dict[str, Any]) -> str:
        """
        Generate a unique key for deduplication.

        Args:
            data: Recruitment data

        Returns:
            Unique key string
        """
        company = data.get("company_name", "")
        position = data.get("position", "")
        date = data.get("publish_date", "")
        return f"{company}|{position}|{date}"

    def _build_existing_map(self, records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Build a map of existing records for quick duplicate lookup.

        Args:
            records: List of existing records

        Returns:
            Dictionary mapping duplicate keys to records
        """
        existing_map = {}

        for record in records:
            fields = record.get("fields", {})
            company = fields.get(FIELD_MAPPING.get("company_name", ""), "")
            position = fields.get(FIELD_MAPPING.get("position", ""), "")
            date = fields.get(FIELD_MAPPING.get("publish_date", ""), "")
            key = f"{company}|{position}|{date}"

            existing_map[key] = {
                "record_id": record.get("record_id"),
                "fields": fields,
            }

        return existing_map

    def _update_record(self, record_id: str, data: Dict[str, Any]) -> Optional[str]:
        """
        Update an existing record.

        Args:
            record_id: Feishu record ID
            data: Updated data

        Returns:
            Record ID if successful, None otherwise
        """
        try:
            record = build_feishu_record(data)
            result = self.client.update_record(record_id, record.get("fields", {}))
            logger.info(f"Updated record: {record_id}")
            return record_id
        except Exception as e:
            logger.error(f"Error updating record {record_id}: {e}")
            return None

    def sync_data(
        self, new_data: List[Dict[str, Any]], incremental: bool = True
    ) -> Dict[str, int]:
        """
        Sync new data to the table.

        Args:
            new_data: List of new recruitment data
            incremental: If True, only add new records; if False, replace all

        Returns:
            Sync result statistics
        """
        if incremental:
            return self.add_recruitments(new_data)
        else:
            # Full sync: clear existing and add all new
            # Note: This is dangerous, so we require explicit confirmation
            logger.warning("Full sync requested - this will replace all existing data!")
            # Implementation would require careful consideration
            return {"created": 0, "updated": 0, "failed": 0, "skipped": 0}


def get_recruitment_table() -> RecruitmentTable:
    """Get the recruitment table manager instance."""
    return RecruitmentTable()
