"""
Logger configuration module.
"""
import sys
from pathlib import Path
from loguru import logger

from config.settings import LOGS_DIR, LOG_LEVEL, LOG_FORMAT, LOG_ROTATION, LOG_RETENTION


def setup_logger(
    log_level: str = None,
    log_file: str = None,
    rotation: str = None,
    retention: str = None,
):
    """
    Configure the logger.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file
        rotation: Log rotation setting
        retention: Log retention setting
    """
    # Remove default handler
    logger.remove()

    # Add stdout handler
    logger.add(
        sys.stdout,
        format=LOG_FORMAT,
        level=log_level or LOG_LEVEL,
        colorize=True,
    )

    # Add file handler
    log_path = Path(log_file) if log_file else LOGS_DIR / "crawler.log"
    logger.add(
        log_path,
        format=LOG_FORMAT,
        level=log_level or LOG_LEVEL,
        rotation=rotation or LOG_ROTATION,
        retention=retention or LOG_RETENTION,
        encoding="utf-8",
    )

    logger.info("Logger configured")


def get_logger():
    """Get the configured logger instance."""
    return logger
