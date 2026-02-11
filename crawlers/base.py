"""
Base crawler class for all recruitment websites.
"""
import time
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

import httpx
from bs4 import BeautifulSoup

from config.settings import (
    REQUEST_TIMEOUT,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
    MAX_RETRIES,
    USER_AGENTS,
)


class BaseCrawler(ABC):
    """
    Abstract base class for all recruitment crawlers.
    Provides common functionality for HTTP requests, rate limiting, etc.
    """

    def __init__(self, name: str, base_url: str):
        """
        Initialize the crawler.

        Args:
            name: Crawler name (e.g., "yingjiesheng")
            base_url: Base URL of the website
        """
        self.name = name
        self.base_url = base_url
        self.session = httpx.Client(timeout=REQUEST_TIMEOUT)

        # Statistics
        self.stats = {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "records_fetched": 0,
        }

    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the pool."""
        return random.choice(USER_AGENTS)

    def _get_random_delay(self) -> float:
        """Get a random delay between requests."""
        return random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)

    def _make_request(
        self,
        url: str,
        method: str = "GET",
        params: Dict[str, Any] = None,
        data: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        retry_count: int = 0,
    ) -> Optional[httpx.Response]:
        """
        Make an HTTP request with retry logic and rate limiting.

        Args:
            url: Request URL
            method: HTTP method
            params: Query parameters
            data: Request body
            headers: Request headers
            retry_count: Current retry attempt

        Returns:
            Response object or None if failed
        """
        self.stats["requests"] += 1

        # Prepare headers
        if headers is None:
            headers = {}
        headers.setdefault("User-Agent", self._get_random_user_agent())

        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, headers=headers)
            elif method.upper() == "POST":
                response = self.session.post(url, data=data, headers=headers)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None

            # Rate limiting delay
            time.sleep(self._get_random_delay())

            # Check response status
            if response.status_code == 200:
                self.stats["successes"] += 1
                return response
            elif response.status_code == 429:  # Rate limited
                if retry_count < MAX_RETRIES:
                    wait_time = 2 ** (retry_count + 1)  # Exponential backoff
                    logger.warning(
                        f"Rate limited, waiting {wait_time}s before retry..."
                    )
                    time.sleep(wait_time)
                    return self._make_request(
                        url, method, params, data, headers, retry_count + 1
                    )
                else:
                    logger.error(f"Max retries reached for URL: {url}")
                    self.stats["failures"] += 1
                    return None
            else:
                logger.warning(
                    f"Unexpected status code {response.status_code} for URL: {url}"
                )
                self.stats["failures"] += 1
                return None

        except httpx.TimeoutException:
            logger.error(f"Timeout while fetching URL: {url}")
            self.stats["failures"] += 1
            return None
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
            self.stats["failures"] += 1
            return None

    def _parse_html(self, html: str) -> BeautifulSoup:
        """
        Parse HTML content with BeautifulSoup.

        Args:
            html: HTML content string

        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, "lxml")

    def _clean_text(self, text: Optional[str]) -> str:
        """
        Clean and normalize text content.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        if text is None:
            return ""

        # Remove extra whitespace
        text = " ".join(text.split())

        return text.strip()

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string to datetime object.

        Args:
            date_str: Date string

        Returns:
            Datetime object or None
        """
        if not date_str:
            return None

        # Common date formats for Chinese websites
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
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # Handle relative dates like "今天", "昨天"
        today = datetime.now()
        if "今天" in date_str:
            return today
        elif "昨天" in date_str:
            return today.replace(day=today.day - 1)

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def normalize_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a raw record from the website to our standard format.

        Args:
            raw_record: Raw record from website

        Returns:
            Normalized record dictionary
        """
        return raw_record

    @abstractmethod
    def fetch_records(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch recruitment records from the website.
        Must be implemented by subclasses.

        Args:
            **kwargs: Additional parameters for fetching

        Returns:
            List of normalized recruitment records
        """
        pass

    def run(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Run the crawler and return all fetched records.

        Args:
            **kwargs: Additional parameters for fetching

        Returns:
            List of normalized recruitment records
        """
        logger.info(f"Starting crawler: {self.name}")
        start_time = time.time()

        try:
            records = self.fetch_records(**kwargs)
            self.stats["records_fetched"] = len(records)

            elapsed = time.time() - start_time
            logger.info(
                f"Crawler {self.name} completed: {len(records)} records in {elapsed:.2f}s"
            )
            logger.info(f"Stats: {self.stats}")

            return records

        except Exception as e:
            logger.error(f"Error running crawler {self.name}: {e}")
            return []

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
