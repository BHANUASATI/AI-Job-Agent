"""
Configuration loader module.

This module provides backward compatibility functions that now use the
new Config class from config.settings.
"""

from config.settings import Config


def load_user_profile():
    """Load user profile from config file using Config class."""
    return Config.get_user_profile()


def save_user_profile(profile):
    """Save user profile to config file using Config class."""
    Config.save_user_profile(profile)
