"""
Logging utility module.

Provides structured logging configuration for the application.
"""

import logging
import sys
from pathlib import Path
from config.settings import Config


def setup_logger(name: str = "ai-job-agent") -> logging.Logger:
    """
    Set up and return a configured logger instance.
    
    Args:
        name: Name of the logger
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Set log level from config
    log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatters
    formatter = logging.Formatter(Config.LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(Config.LOG_FILE)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "ai-job-agent") -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Name of the logger
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Create default logger
logger = setup_logger()
