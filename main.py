#!/usr/bin/env python3
"""
Main entry point for the recruitment crawler system.
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger
from scheduler.jobs import get_scheduler, CrawlerJob
from scheduler.health_check import start_health_check_server
from crawlers.yingjiesheng import YingjieshengCrawler
from feishu.client import get_feishu_client
from feishu.existing_table import print_table_setup_instructions
from loguru import logger


# Load environment variables
load_dotenv()


def test_feishu_connection():
    """Test connection to Feishu API."""
    logger.info("Testing Feishu connection...")

    client = get_feishu_client()

    # Check credentials
    if not all([client.app_id, client.app_secret, client.app_token, client.table_id]):
        logger.error(
            "Feishu credentials not configured. "
            "Please set FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_APP_TOKEN, and FEISHU_TABLE_ID."
        )
        print_table_setup_instructions()
        return False

    if client.test_connection():
        logger.info("Feishu connection successful!")
        return True
    else:
        logger.error("Feishu connection failed!")
        return False


async def run_once():
    """Run crawlers once and exit."""
    logger.info("Starting single run...")

    # Test Feishu connection first
    if not test_feishu_connection():
        return

    # Create crawlers
    crawlers = [
        YingjieshengCrawler(),
        # Add more crawlers here
    ]

    # Run each crawler
    results = []
    for crawler in crawlers:
        try:
            job = CrawlerJob(crawler)
            result = await job.run()
            results.append(result)
        except Exception as e:
            logger.error(f"Error running crawler {crawler.name}: {e}")
            results.append({"crawler": crawler.name, "errors": [str(e)]})

    # Print summary
    logger.info("=" * 50)
    logger.info("CRAWL SUMMARY")
    logger.info("=" * 50)

    for result in results:
        crawler_name = result.get("crawler", "Unknown")
        unique = result.get("unique_records", 0)
        synced = result.get("synced_records", 0)
        errors = result.get("errors", [])

        logger.info(f"{crawler_name}: {unique} unique, {synced} synced")

        if errors:
            logger.error(f"  Errors: {', '.join(errors)}")

    logger.info("=" * 50)


async def run_scheduled():
    """Run crawlers on a schedule."""
    logger.info("Starting scheduled mode...")

    # Test Feishu connection first
    if not test_feishu_connection():
        logger.error("Cannot start scheduled mode without Feishu connection")
        return

    # Start health check server
    start_health_check_server(port=8080)

    # Get scheduler and add crawlers
    scheduler = get_scheduler()

    crawlers = [
        YingjieshengCrawler(),
        # Add more crawlers here
    ]

    for crawler in crawlers:
        scheduler.add_crawler(crawler)

    # Start scheduler
    scheduler.start()

    logger.info("Scheduler started. Press Ctrl+C to stop.")

    try:
        # Keep the program running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        scheduler.stop()


def print_usage():
    """Print usage information."""
    print("""
Usage: python main.py [command]

Commands:
  run     Run crawlers once and exit
  schedule    Run crawlers on schedule (every 3 hours)
  test    Test Feishu connection
  setup   Print Feishu setup instructions

Environment variables:
  FEISHU_APP_ID       Your Feishu app ID
  FEISHU_APP_SECRET   Your Feishu app secret
  FEISHU_APP_TOKEN    Your Feishu app token (table)
  FEISHU_TABLE_ID     Your Feishu table ID
  LOG_LEVEL           Log level (DEBUG, INFO, WARNING, ERROR)

Example:
  # Run once
  python main.py run

  # Start scheduled mode
  python main.py schedule

  # Test connection
  python main.py test
""")


def main():
    """Main entry point."""
    # Setup logger
    setup_logger()

    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1].lower()

    if command == "run":
        asyncio.run(run_once())
    elif command == "schedule":
        asyncio.run(run_scheduled())
    elif command == "test":
        test_feishu_connection()
    elif command == "setup":
        print_table_setup_instructions()
    else:
        print(f"Unknown command: {command}")
        print_usage()


if __name__ == "__main__":
    main()
