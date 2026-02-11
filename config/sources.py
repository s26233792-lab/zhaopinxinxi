"""
Data source configuration.
Define which websites to crawl and their settings.
"""
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class SourceType(Enum):
    """Type of data source."""
    STATIC = "static"  # Simple HTML parsing
    DYNAMIC = "dynamic"  # JavaScript rendering needed
    API = "api"  # Direct API access


@dataclass
class DataSource:
    """Configuration for a single data source."""
    name: str
    url: str
    source_type: SourceType
    enabled: bool = True
    rate_limit: float = 1.0  # Seconds between requests
    timeout: int = 30
    headers: Dict[str, str] = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


# Data source configurations
DATA_SOURCES: Dict[str, DataSource] = {
    "yingjiesheng": DataSource(
        name="应届生求职网",
        url="https://www.yingjiesheng.com",
        source_type=SourceType.STATIC,
        enabled=True,
        rate_limit=2.0,
    ),
    "shixiseng": DataSource(
        name="实习僧",
        url="https://www.shixiseng.com",
        source_type=SourceType.DYNAMIC,
        enabled=True,
        rate_limit=2.0,
    ),
    "nowcoder": DataSource(
        name="牛客网",
        url="https://www.nowcoder.com",
        source_type=SourceType.STATIC,
        enabled=True,
        rate_limit=1.5,
    ),
    "haitou": DataSource(
        name="海投网",
        url="https://www.haitou.cc",
        source_type=SourceType.DYNAMIC,
        enabled=True,
        rate_limit=2.0,
    ),
}


def get_enabled_sources() -> List[DataSource]:
    """Get list of enabled data sources."""
    return [source for source in DATA_SOURCES.values() if source.enabled]


def get_source(name: str) -> DataSource:
    """Get a specific data source by name."""
    return DATA_SOURCES.get(name)
