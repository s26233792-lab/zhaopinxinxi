"""
Scheduler job definitions for automated crawling.
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from crawlers.base import BaseCrawler
from processors.cleaner import DataCleaner
from processors.deduplicator import Deduplicator
from processors.normalizer import DataNormalizer
from feishu.bitable import RecruitmentTable


class CrawlerJob:
    """
    Job definition for crawling a single source.
    """

    def __init__(self, crawler: BaseCrawler, feishu_table: RecruitmentTable = None):
        """
        Initialize the crawler job.

        Args:
            crawler: Crawler instance
            feishu_table: Feishu table manager
        """
        self.crawler = crawler
        self.feishu_table = feishu_table or RecruitmentTable()

        # Initialize processors
        self.cleaner = DataCleaner()
        self.deduplicator = Deduplicator()
        self.normalizer = DataNormalizer()

    async def run(self) -> Dict[str, Any]:
        """
        Execute the crawler job.

        Returns:
            Job result statistics
        """
        result = {
            "crawler": self.crawler.name,
            "started_at": datetime.now().isoformat(),
            "raw_records": 0,
            "cleaned_records": 0,
            "unique_records": 0,
            "synced_records": 0,
            "errors": [],
        }

        try:
            logger.info(f"Starting crawler job: {self.crawler.name}")

            # Fetch raw records
            raw_records = self.crawler.run()
            result["raw_records"] = len(raw_records)

            if not raw_records:
                logger.info(f"No records fetched from {self.crawler.name}")
                return result

            # Normalize records
            normalized_records = self.normalizer.normalize_records(raw_records)
            result["cleaned_records"] = len(normalized_records)

            # Clean records
            cleaned_records = self.cleaner.clean_records(normalized_records)
            result["cleaned_records"] = len(cleaned_records)

            # Remove duplicates
            unique_records = self.deduplicator.filter_duplicates(cleaned_records)
            result["unique_records"] = len(unique_records)

            if not unique_records:
                logger.info(f"No unique records after deduplication from {self.crawler.name}")
                return result

            # Sync to Feishu
            sync_result = self.feishu_table.sync_data(unique_records, incremental=True)
            result["synced_records"] = sync_result.get("created", 0) + sync_result.get("updated", 0)

            # Add to cache
            for record in unique_records:
                self.deduplicator.add_record(record)

            logger.info(
                f"Job {self.crawler.name} completed: "
                f"{result['raw_records']} raw -> {result['unique_records']} unique -> "
                f"{result['synced_records']} synced"
            )

        except Exception as e:
            error_msg = f"Error in crawler job {self.crawler.name}: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)

        finally:
            result["completed_at"] = datetime.now().isoformat()

        return result


class SchedulerManager:
    """
    Manage scheduled crawler jobs.
    """

    def __init__(self, interval_hours: int = 3):
        """
        Initialize the scheduler manager.

        Args:
            interval_hours: Hours between job runs
        """
        self.scheduler = AsyncIOScheduler()
        self.interval_hours = interval_hours
        self.jobs: List[CrawlerJob] = []
        self.feishu_table = RecruitmentTable()

    def add_crawler(self, crawler: BaseCrawler):
        """
        Add a crawler to the schedule.

        Args:
            crawler: Crawler instance
        """
        job = CrawlerJob(crawler, self.feishu_table)
        self.jobs.append(job)
        logger.info(f"Added crawler to schedule: {crawler.name}")

    async def run_all_crawlers(self) -> List[Dict[str, Any]]:
        """
        Run all registered crawlers sequentially.

        Returns:
            List of job results
        """
        results = []

        for job in self.jobs:
            try:
                result = await job.run()
                results.append(result)
            except Exception as e:
                logger.error(f"Error running job {job.crawler.name}: {e}")
                results.append({
                    "crawler": job.crawler.name,
                    "errors": [str(e)],
                })

        return results

    def start(self):
        """Start the scheduler."""
        # Add job to run at interval
        self.scheduler.add_job(
            self.run_all_crawlers,
            trigger=IntervalTrigger(hours=self.interval_hours),
            id="crawler_job",
            name="Recruitment Crawler Job",
            replace_existing=True,
        )

        # Also run immediately on start
        self.scheduler.add_job(
            self.run_all_crawlers,
            trigger="date",
            id="crawler_initial",
            name="Initial Crawler Run",
        )

        self.scheduler.start()
        logger.info(f"Scheduler started with {self.interval_hours}h interval")

    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    def get_status(self) -> Dict[str, Any]:
        """
        Get scheduler status.

        Returns:
            Status dictionary
        """
        return {
            "running": self.scheduler.running,
            "jobs": len(self.jobs),
            "interval_hours": self.interval_hours,
            "next_run_time": str(self.scheduler.get_job("crawler_job").next_run_time)
            if self.scheduler.get_job("crawler_job")
            else None,
        }


# Singleton instance
_scheduler_instance: SchedulerManager = None


def get_scheduler() -> SchedulerManager:
    """Get or create the singleton scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SchedulerManager(interval_hours=3)
    return _scheduler_instance
