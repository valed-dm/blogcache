"""
Logging configuration for the application.

Uses Loguru for structured logging with file rotation and contextual binding.
Reads DEBUG from env at import time to avoid circular import with config.
"""

import os
import sys

from loguru import logger


def _debug_from_env() -> bool:
    """Read DEBUG from environment to avoid importing config (circular import)."""
    return os.environ.get("DEBUG", "true").lower() in ("1", "true", "yes")


logger.remove()

logger.add(
    sys.stderr,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    level="DEBUG" if _debug_from_env() else "INFO",
    colorize=True,
)

logger.add(
    "logs/blogcache.log",
    format=(
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    ),
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    level="DEBUG",
    enqueue=True,
    backtrace=True,
    diagnose=True,
)

log = logger.bind(service="blogcache")
