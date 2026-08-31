"""
Input validation utilities.

Provides validation functions for various inputs throughout the application.
"""

import re
from typing import List, Optional
from utils.logger import get_logger
from utils.exceptions import ValidationError

logger = get_logger(__name__)


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
        
    Raises:
        ValidationError: If email is invalid
    """
    if not email or not isinstance(email, str):
        raise ValidationError("Email must be a non-empty string")
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        raise ValidationError(f"Invalid email format: {email}")
    
    return True


def validate_job_description(jd: str) -> bool:
    """
    Validate job description content.
    
    Args:
        jd: Job description text
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If job description is invalid
    """
    if not jd or not isinstance(jd, str):
        raise ValidationError("Job description must be a non-empty string")
    
    if len(jd.strip()) < 50:
        raise ValidationError("Job description is too short (minimum 50 characters)")
    
    if len(jd) > 10000:
        raise ValidationError("Job description is too long (maximum 10000 characters)")
    
    return True


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If URL is invalid
    """
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string")
    
    # Basic URL regex pattern
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    
    if not re.match(pattern, url):
        raise ValidationError(f"Invalid URL format: {url}")
    
    return True


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If phone number is invalid
    """
    if not phone or not isinstance(phone, str):
        raise ValidationError("Phone number must be a non-empty string")
    
    # Allow various phone number formats
    pattern = r'^[\d\s\-\+\(\)\.]+$'
    
    if not re.match(pattern, phone):
        raise ValidationError(f"Invalid phone number format: {phone}")
    
    # Check minimum length (after removing non-digits)
    digits = re.sub(r'[^\d]', '', phone)
    if len(digits) < 10:
        raise ValidationError("Phone number must have at least 10 digits")
    
    return True


def validate_skills(skills: List[str]) -> bool:
    """
    Validate skills list.
    
    Args:
        skills: List of skills to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If skills are invalid
    """
    if not isinstance(skills, list):
        raise ValidationError("Skills must be a list")
    
    if not skills:
        raise ValidationError("Skills list cannot be empty")
    
    for skill in skills:
        if not isinstance(skill, str):
            raise ValidationError("Each skill must be a string")
        if len(skill.strip()) < 2:
            raise ValidationError("Each skill must be at least 2 characters long")
    
    return True


def validate_file_path(path: str, must_exist: bool = False) -> bool:
    """
    Validate file path.
    
    Args:
        path: File path to validate
        must_exist: Whether the file must exist
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If path is invalid
    """
    if not path or not isinstance(path, str):
        raise ValidationError("File path must be a non-empty string")
    
    from pathlib import Path
    path_obj = Path(path)
    
    if must_exist and not path_obj.exists():
        raise ValidationError(f"File does not exist: {path}")
    
    # Check for valid characters
    invalid_chars = '<>:"|?*'
    if any(char in path for char in invalid_chars):
        raise ValidationError(f"Path contains invalid characters: {path}")
    
    return True


def validate_user_profile(profile: dict) -> bool:
    """
    Validate user profile data.
    
    Args:
        profile: User profile dictionary
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If profile is invalid
    """
    required_fields = ["name", "email", "phone"]
    
    if not isinstance(profile, dict):
        raise ValidationError("User profile must be a dictionary")
    
    for field in required_fields:
        if field not in profile:
            raise ValidationError(f"Missing required field: {field}")
    
    # Validate specific fields
    validate_email(profile["email"])
    validate_phone_number(profile["phone"])
    
    if not profile["name"] or len(profile["name"].strip()) < 2:
        raise ValidationError("Name must be at least 2 characters long")
    
    return True


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input by removing potentially harmful content.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove null bytes and other control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
        logger.warning(f"Input truncated to {max_length} characters")
    
    return text.strip()
