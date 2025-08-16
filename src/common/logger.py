"""Logging configuration for Phosphorus."""

import sys

from loguru import logger

from .config import settings


def setup_logging() -> None:
    """Configure loguru logger with custom format."""
    # Remove default handler
    logger.remove()

    # Custom format: [MM-DD HH:mm:ss] [LEVEL] message
    log_format = (
        "<green>[{time:MM-DD HH:mm:ss}]</green> "
        "<level>[{level}]</level> "
        "<white>{message}</white>"
    )

    # Add console handler
    logger.add(
        sys.stderr,
        format=log_format,
        level=settings.log_level,
        colorize=True,
    )

    # Add file handler if specified
    if settings.log_file:
        logger.add(
            settings.log_file,
            format=log_format,
            level=settings.log_level,
            rotation="10 MB",
            retention="7 days",
            colorize=False,
        )


def get_logger():
    """Get configured logger instance."""
    return logger
