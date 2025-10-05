"""
SimpleCrawler Client Library
============================

Professional Python client for SimpleCrawler MK4 microservices platform.

Basic Usage:
    >>> from simplecrawler_client import CrawlerClient
    >>> client = CrawlerClient("http://localhost:8000")
    >>> job = client.crawl("https://example.com", max_pages=10)
    >>> print(job.status)

Async Usage:
    >>> from simplecrawler_client import AsyncCrawlerClient
    >>> async with AsyncCrawlerClient("http://localhost:8000") as client:
    ...     job = await client.crawl("https://example.com")
    ...     results = await job.wait_for_completion()
"""

from .client import CrawlerClient
from .async_client import AsyncCrawlerClient
from .models import CrawlJob, CrawlRequest, CrawlResult
from .exceptions import (
    SimpleCrawlerError,
    APIError,
    AuthenticationError,
    RateLimitError,
    JobNotFoundError,
    ValidationError,
)

__version__ = "2.0.0"
__author__ = "SimpleCrawler Team"
__email__ = "team@simplecrawler.dev"
__license__ = "MIT"

__all__ = [
    # Main clients
    "CrawlerClient",
    "AsyncCrawlerClient",
    
    # Data models
    "CrawlJob",
    "CrawlRequest", 
    "CrawlResult",
    
    # Exceptions
    "SimpleCrawlerError",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "JobNotFoundError",
    "ValidationError",
    
    # Metadata
    "__version__",
    "__author__",
    "__email__",
    "__license__",
]