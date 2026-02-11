"""
Crawler for yingjiesheng.com (应届生求职网).
"""
from typing import List, Dict, Any
from urllib.parse import urljoin
from loguru import logger

from .base import BaseCrawler


class YingjieshengCrawler(BaseCrawler):
    """
    Crawler for yingjiesheng.com recruitment website.
    """

    def __init__(self):
        """Initialize the crawler."""
        super().__init__(
            name="yingjiesheng",
            base_url="https://www.yingjiesheng.com",
        )

    def fetch_records(
        self, category: str = "xiaozhao", page: int = 1, max_pages: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fetch recruitment records from yingjiesheng.com.

        Args:
            category: Job category (xiaozhao, shixi, etc.)
            page: Starting page number
            max_pages: Maximum number of pages to crawl

        Returns:
            List of normalized recruitment records
        """
        records = []

        # Category URLs
        category_urls = {
            "xiaozhao": "/job-00-00-0-0-0-0-0-0-0-{}.html",  # 校招
            "shixi": "/intern-00-00-0-0-0-0-0-0-0-{}.html",  # 实习
        }

        if category not in category_urls:
            logger.error(f"Unknown category: {category}")
            return records

        for page_num in range(page, page + max_pages):
            logger.info(f"Fetching page {page_num} of category {category}...")

            url = urljoin(
                self.base_url, category_urls[category].format(page_num)
            )
            response = self._make_request(url)

            if not response:
                logger.warning(f"Failed to fetch page {page_num}")
                continue

            # Parse response
            page_records = self._parse_job_list_page(response.text)
            records.extend(page_records)

            # Check if we've reached the last page
            if len(page_records) == 0:
                logger.info(f"No more records on page {page_num}, stopping")
                break

        return records

    def _parse_job_list_page(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse the job list page HTML.

        Args:
            html: HTML content

        Returns:
            List of job records
        """
        records = []
        soup = self._parse_html(html)

        # Note: The actual HTML structure may vary
        # This is a template that needs to be adapted to the real structure

        # Common selectors for job listing pages
        job_items = soup.select(".job-list-item") or soup.select(".job-item") or soup.select("li.job")

        for item in job_items:
            try:
                record = self._parse_job_item(item)
                if record:
                    records.append(record)
            except Exception as e:
                logger.warning(f"Error parsing job item: {e}")
                continue

        return records

    def _parse_job_item(self, item) -> Dict[str, Any]:
        """
        Parse a single job item from the list.

        Args:
            item: BeautifulSoup element for a job item

        Returns:
            Normalized job record
        """
        # Extract job details - selectors need to match actual site structure
        company_elem = (
            item.select_one(".company-name")
            or item.select_one(".company")
            or item.select_one("h3")
        )
        position_elem = (
            item.select_one(".job-title")
            or item.select_one(".position")
            or item.select_one("h2")
        )
        link_elem = item.select_one("a")
        date_elem = item.select_one(".date") or item.select_one(".publish-date")

        company_name = self._clean_text(company_elem.get_text()) if company_elem else ""
        position = self._clean_text(position_elem.get_text()) if position_elem else ""
        job_url = urljoin(self.base_url, link_elem.get("href")) if link_elem else ""
        publish_date = self._parse_date(date_elem.get_text()) if date_elem else None

        # Extract additional info from the job detail page if needed
        # For now, return basic info
        record = {
            "company_name": company_name,
            "position": position,
            "source": job_url,
            "publish_date": publish_date,
            "batch": "春招",  # Default, should be detected from page
            "company_type": "民营企业",  # Default
            "industry": "互联网",  # Default
            "city": [],  # To be extracted
            "education": "本科及以上",
            "deadline": None,
            "target": ["2026届"],
            "no_written_test": False,
            "referral_code": "",
        }

        return self.normalize_record(record)

    def normalize_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a raw record to our standard format.

        Args:
            raw_record: Raw record from website

        Returns:
            Normalized record
        """
        normalized = {}

        # Map fields
        normalized["company_name"] = raw_record.get("company_name", "")
        normalized["position"] = raw_record.get("position", "")
        normalized["source"] = raw_record.get("source", "")
        normalized["publish_date"] = raw_record.get("publish_date")
        normalized["batch"] = raw_record.get("batch", "")
        normalized["company_type"] = raw_record.get("company_type", "")
        normalized["industry"] = raw_record.get("industry", "")
        normalized["city"] = raw_record.get("city", [])
        normalized["education"] = raw_record.get("education", "")
        normalized["deadline"] = raw_record.get("deadline")
        normalized["target"] = raw_record.get("target", [])
        normalized["no_written_test"] = raw_record.get("no_written_test", False)
        normalized["referral_code"] = raw_record.get("referral_code", "")

        return normalized


# Example usage of a more generic crawler pattern
class GenericJobCrawler(BaseCrawler):
    """
    Generic job crawler that can be configured for different sites.
    This is useful for sites with simple HTML structure.
    """

    def __init__(self, name: str, base_url: str, list_url_pattern: str):
        """
        Initialize the generic crawler.

        Args:
            name: Crawler name
            base_url: Base URL
            list_url_pattern: URL pattern for list pages (use {page} placeholder)
        """
        super().__init__(name, base_url)
        self.list_url_pattern = list_url_pattern

    def fetch_records(
        self, start_page: int = 1, max_pages: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fetch records using the configured URL pattern.

        Args:
            start_page: Starting page
            max_pages: Maximum pages to crawl

        Returns:
            List of job records
        """
        records = []

        for page in range(start_page, start_page + max_pages):
            url = self.base_url + self.list_url_pattern.format(page=page)
            logger.info(f"Fetching {url}")

            response = self._make_request(url)
            if not response:
                continue

            # This needs to be customized for each site
            page_records = self._parse_generic_page(response.text)
            records.extend(page_records)

            if len(page_records) == 0:
                break

        return records

    def _parse_generic_page(self, html: str) -> List[Dict[str, Any]]:
        """
        Generic page parser - to be overridden or configured.

        Args:
            html: HTML content

        Returns:
            List of job records
        """
        # Placeholder - implement based on actual site structure
        return []
