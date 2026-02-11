"""
Global configuration settings for recruitment crawler.
"""
import os
from pathlib import Path
from typing import List

# Project paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CACHE_DB = DATA_DIR / "cache.db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Scheduler settings
SCHEDULER_INTERVAL_HOURS = 3  # Run every 3 hours
SCHEDULER_START_HOUR = 6  # First run at 6 AM
SCHEDULER_END_HOUR = 24  # Last run at midnight

# Web scraping settings
REQUEST_TIMEOUT = 30
REQUEST_DELAY_MIN = 1  # Minimum delay between requests (seconds)
REQUEST_DELAY_MAX = 3  # Maximum delay between requests (seconds)
MAX_RETRIES = 3
USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# Data processing settings
BATCH_SIZE = 100  # Number of records to process in each batch
DEDUPLICATION_FIELDS = ["company_name", "position", "publish_date"]

# Feishu API settings
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_APP_TOKEN = os.getenv("FEISHU_APP_TOKEN", "")  # Existing table app_token
FEISHU_TABLE_ID = os.getenv("FEISHU_TABLE_ID", "")  # Existing table table_id
FEISHU_API_BASE_URL = "https://open.feishu.cn/open-apis"

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
LOG_ROTATION = "00:00"  # Rotate logs at midnight
LOG_RETENTION = "30 days"  # Keep logs for 30 days
