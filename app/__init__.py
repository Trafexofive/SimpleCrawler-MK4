"""
SimpleCrawler v2.0 - Modern async web crawling framework.
"""

from .main import (
    CrawlConfig,
    PageData,
    WebCrawler,
    ContentExtractor,
    RateLimiter,
    RobotsCache
)

__version__ = "2.0.0"
__author__ = "SimpleCrawler Team"

__all__ = [
    "CrawlConfig",
    "PageData", 
    "WebCrawler",
    "ContentExtractor",
    "RateLimiter",
    "RobotsCache"
]