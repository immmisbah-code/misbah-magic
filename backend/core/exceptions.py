"""
exceptions.py — Custom application-level exceptions.

Raise these inside modules/services so routes can catch
them cleanly and return consistent API error responses.
"""


class MisbahMagicError(Exception):
    """Base exception for all app errors."""
    status_code: int = 500


class FileProcessingError(MisbahMagicError):
    """Raised when a file cannot be parsed or is malformed."""
    status_code = 422


class UnsupportedFileTypeError(MisbahMagicError):
    """Raised when an uploaded file extension is not allowed."""
    status_code = 415


class AIServiceError(MisbahMagicError):
    """Raised when the Gemini / AI service call fails."""
    status_code = 502


class ReconciliationError(MisbahMagicError):
    """Raised when the reconciliation engine hits an unexpected state."""
    status_code = 500
