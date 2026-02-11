"""
Data normalization module for recruitment records.
"""
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger

from config.feishu_config import (
    COMPANY_TYPE_OPTIONS,
    INDUSTRY_OPTIONS,
    EDUCATION_OPTIONS,
    TARGET_OPTIONS,
)


class DataNormalizer:
    """
    Normalize recruitment data to standard format.
    """

    def __init__(self):
        """Initialize the normalizer."""
        self.stats = {
            "processed": 0,
            "normalized": 0,
        }

    def normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a single recruitment record to standard format.

        Args:
            record: Input record (may have non-standard field names)

        Returns:
            Normalized record with standard field names and values
        """
        self.stats["processed"] += 1

        normalized = {}

        # Map common field name variations
        field_mapping = {
            # Company
            "company": "company_name",
            "公司": "company_name",
            "公司名称": "company_name",
            "企业": "company_name",
            "企业名称": "company_name",
            # Position
            "job": "position",
            "职位": "position",
            "岗位": "position",
            "title": "position",
            # Date
            "date": "publish_date",
            "发布日期": "publish_date",
            "更新日期": "publish_date",
            "发布时间": "publish_date",
            # Source
            "url": "source",
            "链接": "source",
            "申请链接": "source",
            # City
            "location": "city",
            "地点": "city",
            "工作地点": "city",
            "工作城市": "city",
            # Education
            "学历": "education",
            "学位": "education",
            "学历要求": "education",
            # Deadline
            "截止日期": "deadline",
            "申请截止": "deadline",
        }

        # First, map any non-standard field names
        mapped_record = {}
        for key, value in record.items():
            standard_key = field_mapping.get(key, key)
            mapped_record[standard_key] = value

        # Now normalize each field
        normalized["company_name"] = self._normalize_text(mapped_record.get("company_name", ""))
        normalized["position"] = self._normalize_text(mapped_record.get("position", ""))
        normalized["source"] = self._normalize_url(mapped_record.get("source", ""))
        normalized["publish_date"] = self._normalize_date(mapped_record.get("publish_date"))
        normalized["deadline"] = self._normalize_date(mapped_record.get("deadline"))
        normalized["batch"] = self._normalize_batch(mapped_record.get("batch"))
        normalized["company_type"] = self._normalize_enum(mapped_record.get("company_type"), COMPANY_TYPE_OPTIONS, "民营企业")
        normalized["industry"] = self._normalize_enum(mapped_record.get("industry"), INDUSTRY_OPTIONS, "互联网")
        normalized["city"] = self._normalize_list(mapped_record.get("city"))
        normalized["education"] = self._normalize_enum(mapped_record.get("education"), EDUCATION_OPTIONS, "本科及以上")
        normalized["target"] = self._normalize_target_list(mapped_record.get("target"))
        normalized["no_written_test"] = self._normalize_boolean(mapped_record.get("no_written_test"))
        normalized["referral_code"] = self._normalize_text(mapped_record.get("referral_code", ""))

        self.stats["normalized"] += 1

        return normalized

    def normalize_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize multiple recruitment records.

        Args:
            records: List of input records

        Returns:
            List of normalized records
        """
        normalized_records = []

        for record in records:
            try:
                normalized = self.normalize_record(record)
                normalized_records.append(normalized)
            except Exception as e:
                logger.warning(f"Error normalizing record: {e}")
                continue

        logger.info(f"Normalized {len(normalized_records)} records")

        return normalized_records

    def _normalize_text(self, value: Any) -> str:
        """Normalize text field."""
        if value is None:
            return ""

        text = str(value).strip()
        return " ".join(text.split())

    def _normalize_url(self, value: Any) -> str:
        """Normalize URL field."""
        if not value:
            return ""

        url = str(value).strip()

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        return url

    def _normalize_date(self, value: Any) -> datetime:
        """Normalize date field."""
        if value is None:
            return datetime.now()

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            formats = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%Y年%m月%d日",
                "%m-%d",
                "%m/%d",
            ]

            for fmt in formats:
                try:
                    parsed = datetime.strptime(value, fmt)
                    # If only month-day is provided, use current year
                    if "%Y" not in fmt:
                        parsed = parsed.replace(year=datetime.now().year)
                    return parsed
                except ValueError:
                    continue

        return datetime.now()

    def _normalize_batch(self, value: Any) -> str:
        """Normalize batch field."""
        if not value:
            return ""

        text = str(value).strip()

        # Detect batch from content
        batch_keywords = {
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

        for keyword, batch in batch_keywords.items():
            if keyword in text:
                return batch

        return text if text else "春招"

    def _normalize_enum(self, value: Any, options: List[str], default: str) -> str:
        """Normalize enum field against known options."""
        if not value:
            return default

        # Handle list input
        if isinstance(value, list):
            if value:
                value = value[0]
            else:
                return default

        text = str(value).strip()

        # Exact match
        if text in options:
            return text

        # Fuzzy match
        for option in options:
            if option in text or text in option:
                return option

        return default

    def _normalize_list(self, value: Any) -> List[str]:
        """Normalize list field."""
        if not value:
            return []

        if isinstance(value, list):
            return [str(v).strip() for v in value if v]

        if isinstance(value, str):
            # Split by common separators
            for sep in [",", "、", "/", "|", "；", ";"]:
                if sep in value:
                    return [v.strip() for v in value.split(sep) if v.strip()]

            return [value.strip()]

        return []

    def _normalize_target_list(self, value: Any) -> List[str]:
        """Normalize target recruitment list."""
        if not value:
            return ["2026届"]  # Default

        if isinstance(value, list):
            targets = []
            for v in value:
                v_str = str(v).strip()
                if v_str in TARGET_OPTIONS:
                    targets.append(v_str)
            return targets if targets else ["2026届"]

        if isinstance(value, str):
            targets = []
            for option in TARGET_OPTIONS:
                if option in value:
                    targets.append(option)
            return targets if targets else ["2026届"]

        return ["2026届"]

    def _normalize_boolean(self, value: Any) -> bool:
        """Normalize boolean field."""
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.lower() in ("yes", "是", "true", "1", "免笔试")

        return bool(value)

    def get_stats(self) -> Dict[str, int]:
        """Get normalization statistics."""
        return self.stats.copy()
