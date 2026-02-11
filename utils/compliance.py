# -*- coding: utf-8 -*-
"""
Legal compliance utilities for web scraping.
"""
import os
import urllib.robotparser
from urllib.parse import urlparse
from typing import Set, Dict
from loguru import logger


class RobotsChecker:
    """
    Check robots.txt compliance before scraping.
    """

    def __init__(self):
        """Initialize the robots checker."""
        self._parsers: Dict[str, urllib.robotparser.RobotFileParser] = {}
        self._user_agent = "*"

    def can_fetch(self, url: str) -> bool:
        """
        Check if the URL can be fetched according to robots.txt.

        Args:
            url: URL to check

        Returns:
            True if allowed to fetch
        """
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

            # Get or create parser for this domain
            if base_url not in self._parsers:
                rp = urllib.robotparser.RobotFileParser()
                robots_url = f"{base_url}/robots.txt"
                try:
                    rp.set_url(robots_url)
                    rp.read()
                    self._parsers[base_url] = rp
                    logger.info(f"Loaded robots.txt for {base_url}")
                except Exception as e:
                    logger.warning(f"Could not load robots.txt for {base_url}: {e}")
                    # If robots.txt is not accessible, allow crawling (conservative approach)
                    return True

            return self._parsers[base_url].can_fetch(self._user_agent, url)

        except Exception as e:
            logger.error(f"Error checking robots.txt for {url}: {e}")
            return False

    def set_user_agent(self, user_agent: str):
        """Set the user agent for robots.txt checks."""
        self._user_agent = user_agent


class EmergencyStopChecker:
    """
    Check for emergency stop signal.
    Allows immediate termination if requested.
    """

    STOP_FILE = "STOP_CRAWLING.txt"
    STOP_MESSAGE = """
================================================================================
爬虫已停止！

检测到 STOP_CRAWLING.txt 文件，爬虫已安全终止。

要重新启动爬虫，请删除此文件后重试。
如需永久停止，请将此文件内容设置为 "PERMANENT"
================================================================================
"""

    def check(self) -> bool:
        """
        Check if emergency stop is requested.

        Returns:
            True if should stop
        """
        if not os.path.exists(self.STOP_FILE):
            return False

        # Check if permanent stop
        try:
            with open(self.STOP_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip().upper()
                if content == "PERMANENT":
                    logger.critical("检测到永久停止信号")
                    return True
        except:
            pass

        logger.warning("检测到停止信号文件")
        print(self.STOP_MESSAGE)
        return True

    def create_stop_file(self, permanent: bool = False):
        """Create the stop file."""
        with open(self.STOP_FILE, "w", encoding="utf-8") as f:
            if permanent:
                f.write("PERMANENT")
        logger.info(f"已创建停止文件: {self.STOP_FILE}")

    def remove_stop_file(self):
        """Remove the stop file."""
        if os.path.exists(self.STOP_FILE):
            os.remove(self.STOP_FILE)
            logger.info(f"已删除停止文件: {self.STOP_FILE}")


class ComplianceLogger:
    """
    Log all scraping activities for audit trail.
    """

    def __init__(self, log_file: str = "logs/compliance.log"):
        """Initialize the compliance logger."""
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

    def log_fetch(self, url: str, source: str, success: bool, record_count: int = 0):
        """
        Log a fetch operation.

        Args:
            url: URL fetched
            source: Source website
            success: Whether the fetch was successful
            record_count: Number of records obtained
        """
        from datetime import datetime

        timestamp = datetime.now().isoformat()
        status = "SUCCESS" if success else "FAILED"

        log_entry = f"{timestamp} | {status} | {source} | {url} | {record_count} records\n"

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"Could not write to compliance log: {e}")


# Global instances
_robots_checker = RobotsChecker()
_emergency_checker = EmergencyStopChecker()
_compliance_logger = ComplianceLogger()


def can_fetch(url: str) -> bool:
    """Check if URL can be fetched (robots.txt compliance)."""
    return _robots_checker.can_fetch(url)


def check_emergency_stop() -> bool:
    """Check if emergency stop is requested."""
    return _emergency_checker.check()


def log_fetch(url: str, source: str, success: bool, record_count: int = 0):
    """Log a fetch operation for compliance."""
    _compliance_logger.log_fetch(url, source, success, record_count)
