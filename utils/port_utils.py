"""
Port utility module.

Provides functions for finding available ports for dynamic port assignment.
"""

import socket
from contextlib import closing
from utils.logger import get_logger

logger = get_logger(__name__)


def find_free_port(start_port=8000, max_port=9000):
    """
    Find a free port in the specified range.
    
    Args:
        start_port: Starting port to check
        max_port: Maximum port to check
        
    Returns:
        Available port number
        
    Raises:
        RuntimeError: If no free port found in range
    """
    for port in range(start_port, max_port):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            try:
                s.bind(('', port))
                logger.info(f"Found free port: {port}")
                return port
            except OSError:
                continue
    
    raise RuntimeError(f"No free port found in range {start_port}-{max_port}")


def is_port_available(port):
    """
    Check if a specific port is available.
    
    Args:
        port: Port number to check
        
    Returns:
        True if port is available, False otherwise
    """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        try:
            s.bind(('', port))
            return True
        except OSError:
            return False
