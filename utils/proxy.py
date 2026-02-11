"""
Proxy management module for web scraping.
"""
from typing import List, Optional
import random


class ProxyManager:
    """
    Manage proxy servers for web scraping.
    """

    def __init__(self, proxy_list: List[str] = None):
        """
        Initialize the proxy manager.

        Args:
            proxy_list: List of proxy URLs (format: http://host:port or https://host:port)
        """
        self.proxy_list = proxy_list or []
        self.failed_proxies: set = set()

    def add_proxy(self, proxy_url: str):
        """
        Add a proxy to the list.

        Args:
            proxy_url: Proxy URL
        """
        if proxy_url and proxy_url not in self.proxy_list:
            self.proxy_list.append(proxy_url)

    def get_proxy(self) -> Optional[str]:
        """
        Get a random working proxy.

        Returns:
            Proxy URL or None if no proxies available
        """
        available = [p for p in self.proxy_list if p not in self.failed_proxies]

        if not available:
            # Reset failed proxies and try again
            if self.failed_proxies:
                self.failed_proxies.clear()
                available = self.proxy_list

        if not available:
            return None

        return random.choice(available)

    def mark_failed(self, proxy_url: str):
        """
        Mark a proxy as failed.

        Args:
            proxy_url: Failed proxy URL
        """
        self.failed_proxies.add(proxy_url)

    def mark_success(self, proxy_url: str):
        """
        Mark a proxy as working (remove from failed list).

        Args:
            proxy_url: Working proxy URL
        """
        self.failed_proxies.discard(proxy_url)

    def get_proxies_dict(self) -> dict:
        """
        Get proxy in format for httpx/requests.

        Returns:
            Dictionary with http and https keys
        """
        proxy = self.get_proxy()
        if not proxy:
            return {}

        return {
            "http://": proxy,
            "https://": proxy,
        }

    @staticmethod
    def from_file(file_path: str) -> "ProxyManager":
        """
        Create proxy manager from file.

        Args:
            file_path: Path to file with one proxy per line

        Returns:
            ProxyManager instance
        """
        proxies = []

        try:
            with open(file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        proxies.append(line)

            from loguru import logger
            logger.info(f"Loaded {len(proxies)} proxies from {file_path}")

        except FileNotFoundError:
            from loguru import logger
            logger.warning(f"Proxy file not found: {file_path}")

        return ProxyManager(proxies)
