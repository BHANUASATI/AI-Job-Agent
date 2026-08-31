"""
Utility functions for browser automation module.

Provides retry mechanisms, logging setup, and helper functions.
"""

import asyncio
import logging
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Callable, TypeVar, Optional, Any

from automation.config import AutomationConfig
from automation.exceptions import (
    AutomationException,
    TimeoutException,
    NetworkException,
)

T = TypeVar('T')


def setup_logger(name: str = "automation") -> logging.Logger:
    """
    Set up and return a configured logger instance for automation.
    
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
    log_level = getattr(logging, AutomationConfig.AUTOMATION_LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = "automation") -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Name of the logger
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: Optional[int] = None,
    backoff_base: Optional[int] = None,
    backoff_max: Optional[int] = None,
    exceptions: tuple = (Exception,),
    logger: Optional[logging.Logger] = None,
) -> T:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts (default from config)
        backoff_base: Base for exponential backoff (default from config)
        backoff_max: Maximum backoff time in seconds (default from config)
        exceptions: Tuple of exceptions to catch and retry on
        logger: Logger instance for logging retry attempts
        
    Returns:
        Result of the function call
        
    Raises:
        The last exception if all retries are exhausted
    """
    if max_retries is None:
        max_retries = AutomationConfig.MAX_RETRIES
    if backoff_base is None:
        backoff_base = AutomationConfig.RETRY_BACKOFF_BASE
    if backoff_max is None:
        backoff_max = AutomationConfig.RETRY_BACKOFF_MAX
    
    if logger is None:
        logger = get_logger()
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            
            if attempt == max_retries:
                logger.error(f"Function failed after {max_retries} retries: {e}")
                raise
            
            # Calculate backoff time with exponential increase
            backoff_time = min(backoff_base ** attempt, backoff_max)
            
            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                f"Retrying in {backoff_time} seconds..."
            )
            
            await asyncio.sleep(backoff_time)
    
    # This should never be reached, but for type safety
    raise last_exception if last_exception else AutomationException("Retry failed")


def sync_retry_with_backoff(
    func: Callable[..., T],
    max_retries: Optional[int] = None,
    backoff_base: Optional[int] = None,
    backoff_max: Optional[int] = None,
    exceptions: tuple = (Exception,),
    logger: Optional[logging.Logger] = None,
) -> T:
    """
    Retry a synchronous function with exponential backoff.
    
    Args:
        func: Synchronous function to retry
        max_retries: Maximum number of retry attempts (default from config)
        backoff_base: Base for exponential backoff (default from config)
        backoff_max: Maximum backoff time in seconds (default from config)
        exceptions: Tuple of exceptions to catch and retry on
        logger: Logger instance for logging retry attempts
        
    Returns:
        Result of the function call
        
    Raises:
        The last exception if all retries are exhausted
    """
    if max_retries is None:
        max_retries = AutomationConfig.MAX_RETRIES
    if backoff_base is None:
        backoff_base = AutomationConfig.RETRY_BACKOFF_BASE
    if backoff_max is None:
        backoff_max = AutomationConfig.RETRY_BACKOFF_MAX
    
    if logger is None:
        logger = get_logger()
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            
            if attempt == max_retries:
                logger.error(f"Function failed after {max_retries} retries: {e}")
                raise
            
            # Calculate backoff time with exponential increase
            backoff_time = min(backoff_base ** attempt, backoff_max)
            
            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                f"Retrying in {backoff_time} seconds..."
            )
            
            time.sleep(backoff_time)
    
    # This should never be reached, but for type safety
    raise last_exception if last_exception else AutomationException("Retry failed")


def generate_timestamp() -> str:
    """
    Generate a timestamp string for file naming.
    
    Returns:
        Timestamp string in format: YYYY_MM_DD_HHMM
    """
    return datetime.now().strftime("%Y_%m_%d_%H%M")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def ensure_unique_filepath(filepath: Path) -> Path:
    """
    Ensure a filepath is unique by adding a suffix if it exists.
    
    Args:
        filepath: Desired filepath
        
    Returns:
        Unique filepath
    """
    if not filepath.exists():
        return filepath
    
    base = filepath.stem
    extension = filepath.suffix
    parent = filepath.parent
    
    counter = 1
    while True:
        new_path = parent / f"{base}_{counter}{extension}"
        if not new_path.exists():
            return new_path
        counter += 1


async def wait_for_condition(
    condition: Callable[[], bool],
    timeout: int = 30000,
    interval: int = 500,
    error_message: str = "Condition not met within timeout",
) -> bool:
    """
    Wait for a condition to become true with a timeout.
    
    Args:
        condition: Function that returns bool
        timeout: Maximum wait time in milliseconds
        interval: Check interval in milliseconds
        error_message: Error message to raise on timeout
        
    Returns:
        True if condition was met
        
    Raises:
        TimeoutException: If condition is not met within timeout
    """
    timeout_seconds = timeout / 1000
    interval_seconds = interval / 1000
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        if condition():
            return True
        await asyncio.sleep(interval_seconds)
    
    raise TimeoutException(error_message)


def parse_latex_error(error_output: str) -> dict:
    """
    Parse LaTeX compilation error output into structured format.
    
    Args:
        error_output: Raw error output from LaTeX compilation
        
    Returns:
        Dictionary with structured error information
    """
    lines = error_output.split('\n')
    errors = []
    
    for line in lines:
        if '!' in line or 'Error' in line:
            errors.append({
                'line': line.strip(),
                'type': 'error' if 'Error' in line else 'warning'
            })
    
    return {
        'has_errors': len(errors) > 0,
        'error_count': len(errors),
        'errors': errors,
        'raw_output': error_output
    }


# Create default logger
logger = setup_logger()
