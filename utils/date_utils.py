"""
Date utility functions.
"""
from datetime import datetime, timedelta
from typing import Optional, List
import pytz


# China timezone
CHINA_TZ = pytz.timezone("Asia/Shanghai")


def now_china() -> datetime:
    """Get current datetime in China timezone."""
    return datetime.now(CHINA_TZ)


def parse_date(date_str: str, formats: List[str] = None) -> Optional[datetime]:
    """
    Parse date string with multiple format attempts.

    Args:
        date_str: Date string to parse
        formats: List of date formats to try

    Returns:
        Datetime object or None
    """
    if not date_str:
        return None

    if formats is None:
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y年%m月%d日",
            "%m-%d",
            "%m/%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def format_date(date: datetime, format_str: str = "%Y-%m-%d") -> str:
    """
    Format datetime to string.

    Args:
        date: Datetime object
        format_str: Format string

    Returns:
        Formatted date string
    """
    if date is None:
        return ""

    return date.strftime(format_str)


def days_until(date: datetime) -> Optional[int]:
    """
    Calculate days until a given date.

    Args:
        date: Target date

    Returns:
        Number of days until target, or None if invalid
    """
    if date is None:
        return None

    now = now_china()
    if date.tzinfo is None:
        date = CHINA_TZ.localize(date)

    delta = date - now
    return delta.days


def is_expired(date: datetime, days_threshold: int = 0) -> bool:
    """
    Check if a date has expired.

    Args:
        date: Date to check
        days_threshold: Days after which to consider expired

    Returns:
        True if expired
    """
    if date is None:
        return False

    days = days_until(date)
    return days is not None and days < days_threshold


def get_date_range(days: int = 7) -> tuple[datetime, datetime]:
    """
    Get date range for last N days.

    Args:
        days: Number of days

    Returns:
        Tuple of (start_date, end_date)
    """
    end = now_china()
    start = end - timedelta(days=days)
    return start, end


def get_next_schedule_times(
    start_hour: int = 6, interval_hours: int = 3
) -> List[datetime]:
    """
    Get upcoming schedule times for today.

    Args:
        start_hour: First run hour
        interval_hours: Hours between runs

    Returns:
        List of scheduled times
    """
    now = now_china()
    times = []

    current = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)

    while current.hour < 24:
        if current > now:
            times.append(current)
        current = current + timedelta(hours=interval_hours)

    return times
