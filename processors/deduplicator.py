"""
Data deduplication module using SQLite cache.
"""
import sqlite3
import hashlib
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from pathlib import Path
from loguru import logger

from config.settings import CACHE_DB, DEDUPLICATION_FIELDS


class Deduplicator:
    """
    Deduplicate recruitment records using SQLite cache.
    """

    def __init__(self, cache_db: Path = None):
        """
        Initialize the deduplicator.

        Args:
            cache_db: Path to SQLite cache database
        """
        self.cache_db = cache_db or CACHE_DB
        self._init_db()

        self.stats = {
            "checked": 0,
            "duplicates": 0,
            "unique": 0,
        }

    def _init_db(self):
        """Initialize the cache database."""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()

        # Create records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_hash TEXT UNIQUE NOT NULL,
                company_name TEXT,
                position TEXT,
                publish_date TEXT,
                source_url TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                feishu_record_id TEXT
            )
        """)

        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_record_hash
            ON records(record_hash)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_company_position
            ON records(company_name, position)
        """)

        conn.commit()
        conn.close()

        logger.info(f"Cache database initialized: {self.cache_db}")

    def _generate_hash(self, record: Dict[str, Any]) -> str:
        """
        Generate a unique hash for a record.

        Args:
            record: Record dictionary

        Returns:
            MD5 hash string
        """
        # Use deduplication fields to generate hash
        hash_parts = []
        for field in DEDUPLICATION_FIELDS:
            value = record.get(field, "")
            if isinstance(value, datetime):
                value = value.strftime("%Y-%m-%d")
            elif isinstance(value, list):
                value = ",".join(sorted(str(v) for v in value))
            hash_parts.append(str(value))

        hash_string = "|".join(hash_parts)
        return hashlib.md5(hash_string.encode()).hexdigest()

    def is_duplicate(self, record: Dict[str, Any]) -> bool:
        """
        Check if a record is a duplicate.

        Args:
            record: Record to check

        Returns:
            True if duplicate exists
        """
        self.stats["checked"] += 1

        record_hash = self._generate_hash(record)

        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM records WHERE record_hash = ?", (record_hash,)
        )
        result = cursor.fetchone()

        conn.close()

        is_dup = result is not None
        if is_dup:
            self.stats["duplicates"] += 1
        else:
            self.stats["unique"] += 1

        return is_dup

    def add_record(self, record: Dict[str, Any], feishu_record_id: str = None):
        """
        Add a record to the cache.

        Args:
            record: Record to add
            feishu_record_id: Feishu record ID (if synced)
        """
        record_hash = self._generate_hash(record)

        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        try:
            cursor.execute(
                """
                INSERT INTO records
                (record_hash, company_name, position, publish_date, source_url, first_seen, last_seen, feishu_record_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_hash,
                    record.get("company_name", ""),
                    record.get("position", ""),
                    record.get("publish_date", ""),
                    record.get("source", ""),
                    now,
                    now,
                    feishu_record_id,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # Record already exists, update last_seen
            cursor.execute(
                "UPDATE records SET last_seen = ?, feishu_record_id = ? WHERE record_hash = ?",
                (now, feishu_record_id, record_hash)
            )
            conn.commit()

        conn.close()

    def filter_duplicates(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter out duplicate records from a list.

        Args:
            records: List of records to filter

        Returns:
            List of unique records
        """
        unique_records = []
        seen_hashes: Set[str] = set()

        for record in records:
            record_hash = self._generate_hash(record)

            # Check if we've seen it in this batch
            if record_hash in seen_hashes:
                self.stats["duplicates"] += 1
                continue

            # Check if it exists in cache
            if self.is_duplicate(record):
                continue

            seen_hashes.add(record_hash)
            unique_records.append(record)

        logger.info(
            f"Deduplication: {len(unique_records)} unique, {self.stats['duplicates']} duplicates"
        )

        return unique_records

    def mark_synced(self, record: Dict[str, Any], feishu_record_id: str):
        """
        Mark a record as synced to Feishu.

        Args:
            record: Record that was synced
            feishu_record_id: Feishu record ID
        """
        record_hash = self._generate_hash(record)

        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE records SET feishu_record_id = ? WHERE record_hash = ?",
            (feishu_record_id, record_hash)
        )
        conn.commit()
        conn.close()

    def get_cache_size(self) -> int:
        """Get the number of records in cache."""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM records")
        count = cursor.fetchone()[0]

        conn.close()
        return count

    def cleanup_old_records(self, days: int = 90):
        """
        Remove records older than specified days.

        Args:
            days: Number of days to keep
        """
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()

        cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff = cutoff.replace(day=cutoff.day - days)

        cursor.execute(
            "DELETE FROM records WHERE first_seen < ?",
            (cutoff.isoformat(),)
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"Cleaned up {deleted} old records from cache")

    def get_stats(self) -> Dict[str, int]:
        """Get deduplication statistics."""
        return self.stats.copy()

    def reset_stats(self):
        """Reset statistics counters."""
        self.stats = {
            "checked": 0,
            "duplicates": 0,
            "unique": 0,
        }
