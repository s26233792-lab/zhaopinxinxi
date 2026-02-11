"""
Monitoring and alerting module for the crawler system.
"""
import smtplib
from email.mime.text import MIMEText
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger

from config.settings import LOGS_DIR


class CrawlerMonitor:
    """
    Monitor crawler execution and send alerts on issues.
    """

    def __init__(self, alert_email: str = None):
        """
        Initialize the monitor.

        Args:
            alert_email: Email address for alerts (optional)
        """
        self.alert_email = alert_email
        self.alert_history: List[Dict[str, Any]] = []

    def check_job_result(self, result: Dict[str, Any]) -> bool:
        """
        Check if a job result indicates a problem.

        Args:
            result: Job result dictionary

        Returns:
            True if job was successful
        """
        # Check for errors
        if result.get("errors"):
            self._send_alert(
                f"Crawler Error: {result.get('crawler')}",
                f"Errors occurred:\n" + "\n".join(result.get("errors", []))
            )
            return False

        # Check for zero records
        if result.get("unique_records", 0) == 0:
            logger.warning(f"Job {result.get('crawler')} returned no unique records")
            # This might be normal if no new jobs are posted

        return True

    def check_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check multiple job results and generate summary.

        Args:
            results: List of job results

        Returns:
            Summary dictionary
        """
        summary = {
            "total_jobs": len(results),
            "successful_jobs": 0,
            "failed_jobs": 0,
            "total_records": 0,
            "total_synced": 0,
            "timestamp": datetime.now().isoformat(),
        }

        for result in results:
            if self.check_job_result(result):
                summary["successful_jobs"] += 1
            else:
                summary["failed_jobs"] += 1

            summary["total_records"] += result.get("unique_records", 0)
            summary["total_synced"] += result.get("synced_records", 0)

        return summary

    def _send_alert(self, subject: str, message: str):
        """
        Send an alert notification.

        Args:
            subject: Alert subject
            message: Alert message
        """
        logger.warning(f"ALERT: {subject}")

        # Store alert in history
        alert = {
            "timestamp": datetime.now().isoformat(),
            "subject": subject,
            "message": message,
        }
        self.alert_history.append(alert)

        # Send email if configured
        if self.alert_email:
            self._send_email_alert(subject, message)

        # Could also integrate with Feishu message, webhook, etc.

    def _send_email_alert(self, subject: str, message: str):
        """
        Send alert via email.

        Args:
            subject: Email subject
            message: Email body
        """
        # This is a placeholder - implement actual email sending
        # You would need SMTP server configuration
        logger.info(f"Email alert would be sent to {self.alert_email}: {subject}")


class HealthChecker:
    """
    Health check endpoints and utilities.
    """

    @staticmethod
    def check_database() -> bool:
        """Check if database is accessible."""
        try:
            from processors.deduplicator import Deduplicator
            dedup = Deduplicator()
            size = dedup.get_cache_size()
            logger.info(f"Database check passed. Cache size: {size}")
            return True
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            return False

    @staticmethod
    def check_feishu_connection() -> bool:
        """Check if Feishu API is accessible."""
        try:
            from feishu.client import get_feishu_client
            client = get_feishu_client()
            return client.test_connection()
        except Exception as e:
            logger.error(f"Feishu connection check failed: {e}")
            return False

    @staticmethod
    def get_system_status() -> Dict[str, Any]:
        """
        Get overall system status.

        Returns:
            Status dictionary
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "database": HealthChecker.check_database(),
            "feishu": HealthChecker.check_feishu_connection(),
            "scheduler": _get_scheduler_status(),
        }

    @staticmethod
    def get_recent_logs(lines: int = 100) -> List[str]:
        """
        Get recent log entries.

        Args:
            lines: Number of lines to return

        Returns:
            List of log lines
        """
        log_file = LOGS_DIR / "crawler.log"
        if not log_file.exists():
            return []

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            logger.error(f"Error reading log file: {e}")
            return []


def _get_scheduler_status() -> Dict[str, Any]:
    """Get scheduler status."""
    try:
        from scheduler.jobs import get_scheduler
        scheduler = get_scheduler()
        return scheduler.get_status()
    except:
        return {"running": False}


def health_check() -> Dict[str, Any]:
    """
    Perform a full health check.

    Returns:
        Health check result
    """
    return HealthChecker.get_system_status()
