#!/usr/bin/env python3
"""
Streamlit Dashboard launcher with dynamic port assignment.

This script finds an available port and launches the Streamlit Dashboard.
"""

import sys
import subprocess
from utils.port_utils import find_free_port
from config.settings import Config
from utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Launch Streamlit Dashboard with dynamic port assignment."""
    # Determine port to use (different from UI to avoid conflicts)
    if Config.STREAMLIT_PORT == 0:
        # Dynamic port assignment, start from 8502 to avoid conflict with UI
        port = find_free_port(start_port=8502, max_port=8600)
        logger.info(f"Using dynamically assigned port: {port}")
    else:
        # Use configured port + 1 for dashboard
        port = Config.STREAMLIT_PORT + 1
        logger.info(f"Using configured port + 1: {port}")
    
    # Launch Streamlit
    cmd = [
        "streamlit",
        "run",
        "app_dashboard.py",
        f"--server.port={port}",
        f"--server.address={Config.STREAMLIT_SERVER_ADDRESS}",
        f"--server.headless={str(Config.STREAMLIT_SERVER_HEADLESS).lower()}"
    ]
    
    logger.info(f"Launching Streamlit Dashboard on port {port}")
    print(f"\n{'='*60}")
    print(f"AI Job Agent Dashboard")
    print(f"{'='*60}")
    print(f"URL: http://{Config.STREAMLIT_SERVER_ADDRESS}:{port}")
    print(f"{'='*60}\n")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to launch Streamlit Dashboard: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
