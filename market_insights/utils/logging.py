"""Logging configuration for the Market Insights application.

This module provides centralized logging setup with consistent formatting
and output to both console and file.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    log_file: Path | None = None,
) -> None:
    """Configure logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format string for log messages
        log_file: Optional path to log file
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
