"""
SimpleCrawler Client Exceptions
===============================

Exception classes for SimpleCrawler client library.
"""


class SimpleCrawlerError(Exception):
    """Base exception for SimpleCrawler client errors."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.error_code:
            return f"{self.error_code}: {self.message}"
        return self.message


class APIError(SimpleCrawlerError):
    """General API error."""
    pass


class AuthenticationError(SimpleCrawlerError):
    """Authentication failed."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_FAILED")


class RateLimitError(SimpleCrawlerError):
    """Rate limit exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(message, "RATE_LIMIT_EXCEEDED")
        self.retry_after = retry_after


class JobNotFoundError(SimpleCrawlerError):
    """Job not found."""
    
    def __init__(self, job_id: str):
        super().__init__(f"Job not found: {job_id}", "JOB_NOT_FOUND")
        self.job_id = job_id


class ValidationError(SimpleCrawlerError):
    """Request validation failed."""
    
    def __init__(self, message: str = "Request validation failed", field_errors: dict = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field_errors = field_errors or {}


class NetworkError(SimpleCrawlerError):
    """Network-related error."""
    
    def __init__(self, message: str = "Network error occurred"):
        super().__init__(message, "NETWORK_ERROR")


class TimeoutError(SimpleCrawlerError):
    """Request timeout."""
    
    def __init__(self, message: str = "Request timed out"):
        super().__init__(message, "TIMEOUT_ERROR")


class ServerError(SimpleCrawlerError):
    """Server-side error (5xx status codes)."""
    
    def __init__(self, message: str = "Server error", status_code: int = None):
        super().__init__(message, "SERVER_ERROR")
        self.status_code = status_code


class ClientError(SimpleCrawlerError):
    """Client-side error (4xx status codes)."""
    
    def __init__(self, message: str = "Client error", status_code: int = None):
        super().__init__(message, "CLIENT_ERROR")
        self.status_code = status_code