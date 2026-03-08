"""
Logging configuration for the application.

Uses Loguru for structured logging with file rotation and contextual binding.
"""

import sys

from loguru import logger

from .config import settings


logger.remove()

logger.add(
    sys.stderr,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    level="DEBUG" if settings.debug else "INFO",
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
