"""
Data cleaning module for recruitment records.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from config.feishu_config import (
    COMPANY_TYPE_OPTIONS,
    INDUSTRY_OPTIONS,
    EDUCATION_OPTIONS,
    TARGET_OPTIONS,
)


class DataCleaner:
    """
    Clean and validate recruitment data.
    """

    def __init__(self):
        """Initialize the cleaner."""
        self.stats = {
            "processed": 0,
            "cleaned": 0,
            "invalid": 0,
        }

    def clean_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Clean a single recruitment record.

        Args:
            record: Raw record

        Returns:
            Cleaned record or None if invalid
        """
        self.stats["processed"] += 1

        # Check for required fields
        if not self._is_valid(record):
            self.stats["invalid"] += 1
            return None

        cleaned = record.copy()
        self.stats["cleaned"] += 1

        # Clean each field
        cleaned["company_name"] = self._clean_company_name(record.get("company_name"))
        cleaned["position"] = self._clean_position(record.get("position"))
        cleaned["source"] = self._clean_url(record.get("source"))
        cleaned["publish_date"] = self._clean_date(record.get("publish_date"))
        cleaned["deadline"] = self._clean_date(record.get("deadline"))
        cleaned["batch"] = self._clean_batch(record.get("batch"))
        cleaned["company_type"] = self._normalize_company_type(record.get("company_type"))
        cleaned["industry"] = self._normalize_industry(record.get("industry"))
        cleaned["city"] = self._normalize_city(record.get("city"))
        cleaned["education"] = self._normalize_education(record.get("education"))
        cleaned["target"] = self._normalize_target(record.get("target"))
        cleaned["no_written_test"] = self._clean_boolean(record.get("no_written_test"))
        cleaned["referral_code"] = self._clean_referral_code(record.get("referral_code"))

        return cleaned

    def clean_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean multiple recruitment records.

        Args:
            records: List of raw records

        Returns:
            List of cleaned records
        """
        cleaned_records = []

        for record in records:
            cleaned = self.clean_record(record)
            if cleaned:
                cleaned_records.append(cleaned)

        logger.info(
            f"Data cleaning completed: {self.stats['cleaned']}/{self.stats['processed']} valid, "
            f"{self.stats['invalid']} invalid"
        )

        return cleaned_records

    def _is_valid(self, record: Dict[str, Any]) -> bool:
        """Check if record has all required fields."""
        required_fields = ["company_name", "position"]

        for field in required_fields:
            value = record.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                logger.debug(f"Invalid record: missing or empty {field}")
                return False

        return True

    def _clean_company_name(self, value: Any) -> str:
        """Clean company name."""
        if not value:
            return ""

        text = str(value).strip()
        # Remove common suffixes/prefixes
        text = text.replace("（", "(").replace("）", ")")
        # Remove extra whitespace
        text = " ".join(text.split())

        return text

    def _clean_position(self, value: Any) -> str:
        """Clean position name."""
        if not value:
            return ""

        text = str(value).strip()
        # Normalize common variations
        text = text.replace("（", "(").replace("）", ")")
        text = " ".join(text.split())

        return text

    def _clean_url(self, value: Any) -> str:
        """Clean URL."""
        if not value:
            return ""

        url = str(value).strip()

        # Add protocol if missing
        if url and not url.startswith(("http://", "https://")):
            url = "https://" + url

        return url

    def _clean_date(self, value: Any) -> Optional[datetime]:
        """Clean date value."""
        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            # Try to parse common date formats
            formats = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%Y年%m月%d日",
                "%m-%d",
                "%m/%d",
                "%Y-%m-%d %H:%M:%S",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue

        return None

    def _clean_batch(self, value: Any) -> str:
        """Clean batch field."""
        if not value:
            return ""

        text = str(value).strip()

        # Standardize batch names
        batch_mapping = {
            "春招提前批": "春招提前批",
            "春招": "春招",
            "春招补录": "春招补录",
            "秋招提前批": "秋招提前批",
            "秋招": "秋招",
            "秋招补录": "秋招补录",
            "寒假实习": "寒假实习",
            "暑期实习": "暑期实习",
            "日常实习": "日常实习",
        }

        return batch_mapping.get(text, text)

    def _normalize_company_type(self, value: Any) -> str:
        """Normalize company type to standard options."""
        if not value:
            return ""

        text = str(value).strip()

        # Fuzzy matching
        for option in COMPANY_TYPE_OPTIONS:
            if option in text or text in option:
                return option

        # Map common variations
        type_mapping = {
            "民营": "民营企业",
            "国企": "国有企业",
            "央企": "央企",
            "外企": "外资企业",
            "创业": "创业公司",
        }

        for key, val in type_mapping.items():
            if key in text:
                return val

        return "其他" if text else ""

    def _normalize_industry(self, value: Any) -> str:
        """Normalize industry to standard options."""
        if not value:
            return ""

        # Handle list input
        if isinstance(value, list):
            value = value[0] if value else ""

        text = str(value).strip()

        # Fuzzy matching
        for option in INDUSTRY_OPTIONS:
            if option in text or text in option:
                return option

        # Map common variations
        industry_mapping = {
            "IT": "互联网",
            "软件": "互联网",
            "电商": "互联网",
            "游戏": "互联网",
            "银行": "金融",
            "证券": "金融",
            "基金": "金融",
            "保险": "金融",
        }

        for key, val in industry_mapping.items():
            if key in text:
                return val

        return "其他" if text else ""

    def _normalize_city(self, value: Any) -> List[str]:
        """Normalize city to list of cities."""
        if not value:
            return []

        if isinstance(value, list):
            return [str(c).strip() for c in value if c]

        if isinstance(value, str):
            # Split by common separators
            cities = []
            for sep in [",", "、", "/", "|", " ", "；", ";"]:
                if sep in value:
                    cities = [c.strip() for c in value.split(sep) if c.strip()]
                    break

            if not cities:
                cities = [value.strip()] if value.strip() else []

            return cities

        return []

    def _normalize_education(self, value: Any) -> str:
        """Normalize education to standard options."""
        if not value:
            return ""

        text = str(value).strip()

        # Fuzzy matching
        for option in EDUCATION_OPTIONS:
            if option in text or text in option:
                return option

        # Map common variations
        edu_mapping = {
            "本科": "本科",
            "学士": "本科",
            "硕士": "硕士",
            "研究生": "硕士",
            "博士": "博士",
            "不限": "不限",
        }

        for key, val in edu_mapping.items():
            if key in text:
                return val

        # Default to "本科及以上" for unclear values
        return "本科及以上" if text else ""

    def _normalize_target(self, value: Any) -> List[str]:
        """Normalize recruitment target to list of options."""
        if not value:
            return []

        if isinstance(value, list):
            return [str(t).strip() for t in value if t]

        if isinstance(value, str):
            targets = []
            text = value.strip()

            # Check for each target option
            for option in TARGET_OPTIONS:
                if option in text:
                    targets.append(option)

            return targets if targets else ["2026届"]  # Default to 2026

        return []

    def _clean_boolean(self, value: Any) -> bool:
        """Clean boolean value."""
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            text = value.strip().lower()
            return text in ("yes", "是", "true", "1", "免笔试", "免笔")

        return bool(value)

    def _clean_referral_code(self, value: Any) -> str:
        """Clean referral code."""
        if not value:
            return ""

        text = str(value).strip()
        # Remove spaces
        text = text.replace(" ", "")

        return text

    def get_stats(self) -> Dict[str, int]:
        """Get cleaning statistics."""
        return self.stats.copy()
