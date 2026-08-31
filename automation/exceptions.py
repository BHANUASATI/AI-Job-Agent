"""
Custom exceptions for browser automation module.

Provides specific exception classes for better error handling in browser automation tasks.
"""


class AutomationException(Exception):
    """Base exception for all automation errors."""
    pass


class BrowserLaunchException(AutomationException):
    """Raised when browser fails to launch or initialize."""
    pass


class SessionExpiredException(AutomationException):
    """Raised when authentication session has expired."""
    pass


class LoginFailedException(AutomationException):
    """Raised when login process fails."""
    pass


class ProjectNotFoundException(AutomationException):
    """Raised when a project cannot be found or accessed."""
    pass


class EditorNotLoadedException(AutomationException):
    """Raised when editor fails to load or is not ready."""
    pass


class CompileFailedException(AutomationException):
    """Raised when LaTeX compilation fails."""
    pass


class DownloadFailedException(AutomationException):
    """Raised when file download fails."""
    pass


class TimeoutException(AutomationException):
    """Raised when an operation times out."""
    pass


class ElementNotFoundException(AutomationException):
    """Raised when a required UI element is not found."""
    pass


class NetworkException(AutomationException):
    """Raised when network-related errors occur."""
    pass


class ValidationException(AutomationException):
    """Raised when input validation fails."""
    pass
