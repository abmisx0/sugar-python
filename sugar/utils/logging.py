"""Logging configuration for Sugar Python library."""

import logging
import sys
from typing import TextIO


def setup_logging(
    level: int = logging.INFO,
    format_string: str | None = None,
    stream: TextIO | None = None,
) -> logging.Logger:
    """
    Set up logging for the Sugar library.

    Args:
        level: Logging level (default: INFO).
        format_string: Custom format string (optional).
        stream: Output stream (default: stderr).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("sugar")

    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(logging.Formatter(format_string))

    logger.addHandler(handler)
    logger.setLevel(level)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        name: Module name (typically __name__).

    Returns:
        Logger instance.
    """
    return logging.getLogger(f"sugar.{name}")
