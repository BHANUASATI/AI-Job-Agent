"""
Custom exceptions for AI Job Agent.

Provides specific exception classes for better error handling.
"""


class JobAgentException(Exception):
    """Base exception for all Job Agent errors."""
    pass


class ConfigurationError(JobAgentException):
    """Raised when configuration is invalid or missing."""
    pass


class ResumeLoadError(JobAgentException):
    """Raised when resume loading fails."""
    pass


class ResumeRetrievalError(JobAgentException):
    """Raised when resume retrieval fails."""
    pass


class VectorStoreError(JobAgentException):
    """Raised when vector store operations fail."""
    pass


class JDAnalysisError(JobAgentException):
    """Raised when job description analysis fails."""
    pass


class EmailGenerationError(JobAgentException):
    """Raised when email generation fails."""
    pass


class GmailServiceError(JobAgentException):
    """Raised when Gmail service operations fail."""
    pass


class DatabaseError(JobAgentException):
    """Raised when database operations fail."""
    pass


class ValidationError(JobAgentException):
    """Raised when input validation fails."""
    pass


class LLMError(JobAgentException):
    """Raised when LLM operations fail."""
    pass


class JDParserError(JobAgentException):
    """Raised when job description parsing fails."""
    pass
