"""
Logging configuration for Persistence Service
"""
import os
import logging
import logging.handlers
from .settings import settings


def setup_logging():
    """
    Setup structured logging with rotation
    """
    # Create logs directory if not exists
    log_dir = os.path.dirname(settings.logging.file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Convert string log level to logging constant
    log_level = getattr(logging, settings.logging.level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(settings.logging.format)

    # Console handler (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=settings.logging.file,
        maxBytes=settings.logging.max_bytes,
        backupCount=settings.logging.backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Log startup message
    logging.info("=" * 60)
    logging.info("Persistence Service Starting")
    logging.info(f"Log Level: {settings.logging.level}")
    logging.info(f"Log File: {settings.logging.file}")
    logging.info("=" * 60)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module

    Args:
        name: Module name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)