"""
Configuration management for browser automation module.

This module handles all automation-specific configuration settings using environment variables
and config files, with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class AutomationConfig:
    """Configuration class for browser automation."""
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    
    # Directory paths (configurable via environment variables)
    AUTOMATION_DIR = BASE_DIR / "automation"
    SESSION_DIR = Path(os.getenv("AUTOMATION_SESSION_DIR", BASE_DIR / "automation" / "sessions"))
    DOWNLOAD_DIR = Path(os.getenv("AUTOMATION_DOWNLOAD_DIR", BASE_DIR / "automation" / "downloads"))
    RESUME_VERSIONS_DIR = Path(os.getenv("RESUME_VERSIONS_DIR", BASE_DIR / "resume_versions"))
    
    # Browser Configuration
    BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
    BROWSER_TYPE = os.getenv("BROWSER_TYPE", "chromium")  # chromium, firefox, webkit
    BROWSER_SLOW_MO = int(os.getenv("BROWSER_SLOW_MO", "0"))  # milliseconds
    BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "30000"))  # milliseconds
    
    # Visual Execution Mode Configuration
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    VISUAL_MODE = os.getenv("VISUAL_MODE", "false").lower() == "true"
    
    # Visual Mode Settings (only used when VISUAL_MODE or DEBUG_MODE is True)
    VISUAL_HEADLESS = False  # Always visible in visual mode
    VISUAL_SLOW_MO = int(os.getenv("VISUAL_SLOW_MO", "500"))  # milliseconds between actions
    VISUAL_TYPING_DELAY = int(os.getenv("VISUAL_TYPING_DELAY", "50"))  # milliseconds per character
    VISUAL_PAUSE_AFTER_ACTION = int(os.getenv("VISUAL_PAUSE_AFTER_ACTION", "300"))  # milliseconds
    VISUAL_VIEWPORT_WIDTH = int(os.getenv("VISUAL_VIEWPORT_WIDTH", "1920"))
    VISUAL_VIEWPORT_HEIGHT = int(os.getenv("VISUAL_VIEWPORT_HEIGHT", "1080"))
    VISUAL_KEEP_BROWSER_OPEN = os.getenv("VISUAL_KEEP_BROWSER_OPEN", "true").lower() == "true"
    VISUAL_BROWSER_CLOSE_DELAY = int(os.getenv("VISUAL_BROWSER_CLOSE_DELAY", "30"))  # seconds
    
    # Screenshot Configuration
    SCREENSHOT_ENABLED = os.getenv("SCREENSHOT_ENABLED", "true").lower() == "true"
    SCREENSHOT_DIR = BASE_DIR / "logs" / "screenshots"
    SCREENSHOT_ON_MILESTONE = os.getenv("SCREENSHOT_ON_MILESTONE", "true").lower() == "true"
    SCREENSHOT_ON_ERROR = os.getenv("SCREENSHOT_ON_ERROR", "true").lower() == "true"
    
    # Video Recording Configuration
    VIDEO_ENABLED = os.getenv("VIDEO_ENABLED", "true").lower() == "true"
    VIDEO_DIR = BASE_DIR / "logs" / "videos"
    VIDEO_SIZE_STR = os.getenv("VIDEO_SIZE", "1920x1080")
    
    @classmethod
    def get_video_size(cls) -> dict:
        """Parse video size string into dictionary format for Playwright."""
        try:
            width, height = cls.VIDEO_SIZE_STR.split('x')
            return {"width": int(width), "height": int(height)}
        except:
            return {"width": 1920, "height": 1080}
    
    # Session Configuration
    SESSION_PERSIST_ENABLED = os.getenv("SESSION_PERSIST_ENABLED", "true").lower() == "true"
    SESSION_EXPIRY_HOURS = int(os.getenv("SESSION_EXPIRY_HOURS", "24"))
    
    # Retry Configuration
    MAX_RETRIES = int(os.getenv("AUTOMATION_MAX_RETRIES", "3"))
    RETRY_BACKOFF_BASE = int(os.getenv("AUTOMATION_RETRY_BACKOFF_BASE", "2"))  # exponential backoff base
    RETRY_BACKOFF_MAX = int(os.getenv("AUTOMATION_RETRY_BACKOFF_MAX", "10"))  # maximum backoff in seconds
    
    # Overleaf Configuration
    OVERLEAF_URL = os.getenv("OVERLEAF_URL", "https://www.overleaf.com")
    OVERLEAF_EMAIL = os.getenv("OVERLEAF_EMAIL")
    OVERLEAF_PASSWORD = os.getenv("OVERLEAF_PASSWORD")
    OVERLEAF_DEFAULT_PROJECT = os.getenv("OVERLEAF_DEFAULT_PROJECT", "Master Resume")
    
    # Editor Configuration
    EDITOR_LOAD_TIMEOUT = int(os.getenv("EDITOR_LOAD_TIMEOUT", "30000"))  # milliseconds
    AUTOSAVE_WAIT_TIMEOUT = int(os.getenv("AUTOSAVE_WAIT_TIMEOUT", "10000"))  # milliseconds
    COMPILE_TIMEOUT = int(os.getenv("COMPILE_TIMEOUT", "60000"))  # milliseconds
    DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", "30000"))  # milliseconds
    
    # Logging Configuration
    AUTOMATION_LOG_LEVEL = os.getenv("AUTOMATION_LOG_LEVEL", "INFO")
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist."""
        directories = [
            cls.SESSION_DIR,
            cls.DOWNLOAD_DIR,
            cls.RESUME_VERSIONS_DIR,
            cls.SCREENSHOT_DIR,
            cls.VIDEO_DIR,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls):
        """Validate configuration and raise errors if invalid."""
        errors = []
        
        # Check required credentials
        if not cls.OVERLEAF_EMAIL:
            errors.append("OVERLEAF_EMAIL is required for Overleaf automation")
        
        if not cls.OVERLEAF_PASSWORD:
            errors.append("OVERLEAF_PASSWORD is required for Overleaf automation")
        
        # Validate browser type
        valid_browsers = ["chromium", "firefox", "webkit"]
        if cls.BROWSER_TYPE not in valid_browsers:
            errors.append(f"BROWSER_TYPE must be one of {valid_browsers}, got: {cls.BROWSER_TYPE}")
        
        # Validate timeouts
        if cls.BROWSER_TIMEOUT <= 0:
            errors.append("BROWSER_TIMEOUT must be positive")
        
        if cls.MAX_RETRIES < 0:
            errors.append("MAX_RETRIES must be non-negative")
        
        if errors:
            raise ValueError("Automation configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
        
        return True
    
    @classmethod
    def get_session_path(cls, session_name: str = "default") -> Path:
        """
        Get the path for a session file.
        
        Args:
            session_name: Name of the session
            
        Returns:
            Path to the session file
        """
        return cls.SESSION_DIR / f"{session_name}.json"
    
    @classmethod
    def get_download_path(cls, filename: str) -> Path:
        """
        Get the full path for a downloaded file.
        
        Args:
            filename: Name of the downloaded file
            
        Returns:
            Path to the downloaded file
        """
        return cls.DOWNLOAD_DIR / filename
    
    @classmethod
    def get_resume_version_path(cls, base_name: str, timestamp: str) -> Path:
        """
        Get the path for a resume version.
        
        Args:
            base_name: Base name for the resume
            timestamp: Timestamp string
            
        Returns:
            Path to the resume version file
        """
        filename = f"{base_name}_{timestamp}.pdf"
        return cls.RESUME_VERSIONS_DIR / filename
    
    @classmethod
    def to_dict(cls) -> dict:
        """Convert configuration to dictionary (for debugging)."""
        return {
            key: str(getattr(cls, key))
            for key in dir(cls)
            if not key.startswith('_') and not callable(getattr(cls, key))
        }


# Initialize configuration on import
AutomationConfig.ensure_directories()
