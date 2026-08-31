"""
Configuration management for AI Job Agent.

This module handles all configuration settings using environment variables
and config files, with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class."""
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    PROJECT_ROOT = BASE_DIR
    
    # Directory paths (configurable via environment variables)
    RESUME_DIR = Path(os.getenv("RESUME_DIR", BASE_DIR / "resumes"))
    DATABASE_DIR = Path(os.getenv("DATABASE_DIR", BASE_DIR / "database"))
    VECTOR_DB_DIR = Path(os.getenv("VECTOR_DB_DIR", BASE_DIR / "vector_db"))
    CONFIG_DIR = Path(os.getenv("CONFIG_DIR", BASE_DIR / "config"))
    LOGS_DIR = Path(os.getenv("LOGS_DIR", BASE_DIR / "logs"))
    GENERATED_RESUME_DIR = Path(os.getenv("GENERATED_RESUME_DIR", BASE_DIR / "generated_resumes"))
    
    # File paths
    USER_PROFILE_PATH = CONFIG_DIR / "user_profile.json"
    GMAIL_TOKEN_PATH = BASE_DIR / "token.json"
    GMAIL_CREDENTIALS_PATH = BASE_DIR / "credentials.json"
    
    # Database configuration
    DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")  # sqlite, postgresql, mongodb
    DATABASE_PATH = DATABASE_DIR / "job_applications.db"
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")
    
    # LLM Configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")  # openrouter, openai, gemini
    LLM_MODEL = os.getenv("LLM_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")
    LLM_API_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("LLM_API_KEY")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))
    
    # Embedding Configuration
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")  # cpu, cuda
    
    # Text Splitting Configuration
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # Resume Ranking Configuration
    CHUNK_SCORE_MULTIPLIER = int(os.getenv("CHUNK_SCORE_MULTIPLIER", "10"))
    SKILL_MATCH_BONUS = int(os.getenv("SKILL_MATCH_BONUS", "15"))
    
    # Email Configuration
    EMAIL_SIGNATURE_FORMAT = os.getenv("EMAIL_SIGNATURE_FORMAT", "professional")
    EMAIL_WORD_COUNT_MIN = int(os.getenv("EMAIL_WORD_COUNT_MIN", "90"))
    EMAIL_WORD_COUNT_MAX = int(os.getenv("EMAIL_WORD_COUNT_MAX", "140"))
    
    # Gmail Configuration
    GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
    
    # Streamlit Configuration
    STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "0"))  # 0 = dynamic
    STREAMLIT_SERVER_ADDRESS = os.getenv("STREAMLIT_SERVER_ADDRESS", "localhost")
    STREAMLIT_SERVER_HEADLESS = os.getenv("STREAMLIT_SERVER_HEADLESS", "true").lower() == "true"
    
    # Application Configuration
    APP_NAME = os.getenv("APP_NAME", "AI Job Agent")
    APP_VERSION = os.getenv("APP_VERSION", "2.0.0")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_FILE = LOGS_DIR / "app.log"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "10"))
    
    # Cache Configuration
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # seconds
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist."""
        directories = [
            cls.RESUME_DIR,
            cls.DATABASE_DIR,
            cls.VECTOR_DB_DIR,
            cls.CONFIG_DIR,
            cls.LOGS_DIR,
            cls.GENERATED_RESUME_DIR,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls):
        """Validate configuration and raise errors if invalid."""
        errors = []
        
        # Check required API keys
        if cls.LLM_PROVIDER == "openrouter" and not cls.LLM_API_KEY:
            errors.append("OPENROUTER_API_KEY is required when LLM_PROVIDER is 'openrouter'")
        
        # Check paths
        if not cls.GMAIL_CREDENTIALS_PATH.exists():
            errors.append(f"Gmail credentials file not found: {cls.GMAIL_CREDENTIALS_PATH}")
        
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
        
        return True
    
    @classmethod
    def get_user_profile(cls) -> dict:
        """Load user profile from config file."""
        default_profile = {
            "name": "Your Name",
            "email": "your.email@example.com",
            "phone": "+1-234-567-8900",
            "location": "Your Location",
            "github": "https://github.com/yourusername",
            "linkedin": "https://linkedin.com/in/yourprofile",
            "portfolio": "https://yourportfolio.com"
        }
        
        if cls.USER_PROFILE_PATH.exists():
            try:
                with open(cls.USER_PROFILE_PATH, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load user profile: {e}")
                return default_profile
        
        return default_profile
    
    @classmethod
    def save_user_profile(cls, profile: dict):
        """Save user profile to config file."""
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(cls.USER_PROFILE_PATH, 'w') as f:
            json.dump(profile, f, indent=2)
    
    @classmethod
    def to_dict(cls) -> dict:
        """Convert configuration to dictionary (for debugging)."""
        return {
            key: str(getattr(cls, key))
            for key in dir(cls)
            if not key.startswith('_') and not callable(getattr(cls, key))
        }


# Initialize configuration on import
Config.ensure_directories()
