"""
Logging configuration for OneDrive Custom Backup Tool
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime


def setup_logging(verbose: bool = False, log_file: str = None) -> logging.Logger:
    """
    Setup logging configuration

    Args:
        verbose: Enable verbose logging
        log_file: Custom log file path

    Returns:
        Configured logger instance
    """
    # Create logs directory
    logs_dir = Path.cwd() / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Default log file
    if not log_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"onedrive_backup_{timestamp}.log"

    # Set log level
    log_level = logging.DEBUG if verbose else logging.INFO

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )

    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'  # Handle Unicode characters properly
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)

    # Set console encoding to handle Unicode characters
    try:
        console_handler.stream.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        # Fallback for older Python versions
        pass

    logger.addHandler(console_handler)

    # Log startup message
    logger.info("OneDrive Custom Backup Tool - Logging initialized")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Log level: {logging.getLevelName(log_level)}")

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance for specific module

    Args:
        name: Module name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
