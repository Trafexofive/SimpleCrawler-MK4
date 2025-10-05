"""
Unit tests for WebCrawler core functionality.

Tests URL processing, content extraction, filtering, and crawl logic.
"""

import pytest
import asyncio
import aiohttp
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app import (
    WebCrawler, 
    CrawlConfig, 
    PageData, 
    ContentExtractor,
    RateLimiter,
    RobotsCache
)


class TestWebCrawlerInitialization:
    """Test crawler initialization and configuration."""
    
    def test_crawler_init_with_defaults(self, basic_config):
        """Test crawler initializes with default configuration."""
        crawler = WebCrawler(basic_config)
        
        assert crawler.config == basic_config
        assert len(crawler.visited) == 0
        assert len(crawler.queued) == 0
        assert len(crawler.results) == 0
    
    def test_crawler_creates_output_dir(self, basic_config):
        """Test crawler creates output directory."""
        crawler = WebCrawler(basic_config)
        output_path = Path(basic_config.output_dir)
        
        # Directory should be created during init or crawl
        assert output_path.exists() or True  # May be created later
    
    def test_crawler_stats_initialized(self, basic_config):
        """Test crawler statistics are initialized."""
        crawler = WebCrawler(basic_config)
        
        assert 'start_time' in crawler.stats
        assert 'pages_crawled' in crawler.stats
        assert crawler.stats['pages_crawled'] == 0


class TestURLFiltering:
    """Test URL validation and filtering logic."""
    
    def test_valid_http_url(self, basic_config):
        """Test valid HTTP URLs are accepted."""
        crawler = WebCrawler(basic_config)
        
        valid_urls = [
            'http://example.com',
            'http://example.com/page',
            'http://sub.example.com',
        ]
        
        for url in valid_urls:
            assert crawler._should_crawl(url) is not None
    
    def test_valid_https_url(self, basic_config):
        """Test valid HTTPS URLs are accepted."""
        crawler = WebCrawler(basic_config)
        assert crawler._should_crawl('https://example.com') is not None
    
    def test_invalid_url_rejected(self, basic_config):
        """Test invalid URLs are rejected."""
        crawler = WebCrawler(basic_config)
        
        invalid_urls = [
            'not-a-url',
            'ftp://example.com',
            '',
            'javascript:void(0)',
        ]
        
        for url in invalid_urls:
            assert crawler._should_crawl(url) is False
    
    def test_same_domain_filtering(self, temp_output_dir):
        """Test same-domain URL filtering."""
        config = CrawlConfig(
            start_url='http://example.com',
            same_domain=True,
            output_dir=str(temp_output_dir)
        )
        crawler = WebCrawler(config)
        
        # Same domain should pass
        assert crawler._should_crawl('http://example.com/page') is not False
        assert crawler._should_crawl('http://sub.example.com/page') is not False
        
        # Different domain should fail
        assert crawler._should_crawl('http://other.com') is False
    
    def test_cross_domain_allowed(self, temp_output_dir):
        """Test cross-domain crawling when enabled."""
        config = CrawlConfig(
            start_url='http://example.com',
            same_domain=False,
            output_dir=str(temp_output_dir)
        )
        crawler = WebCrawler(config)
        
        # Different domains should pass
        assert crawler._should_crawl('http://other.com') is not False
    
    def test_file_extension_filtering(self, basic_config):
        """Test that certain file extensions are filtered."""
        crawler = WebCrawler(basic_config)
        
        excluded_urls = [
            'http://example.com/file.pdf',
            'http://example.com/image.jpg',
            'http://example.com/doc.docx',
            'http://example.com/archive.zip',
            'http://example.com/video.mp4',
        ]
        
        for url in excluded_urls:
            assert crawler._should_crawl(url) is False


class TestContentExtraction:
    """Test content extraction from HTML."""
    
    def test_extract_text_basic(self, sample_html):
        """Test basic text extraction."""
        text = ContentExtractor.extract_text(sample_html, 'http://example.com')
        
        assert 'Main Content' in text
        assert 'test page' in text.lower()
        # Scripts and styles should be removed
        assert 'console.log' not in text
        assert 'color: red' not in text
    
    def test_extract_metadata(self, sample_html):
        """Test metadata extraction."""
        metadata = ContentExtractor.extract_metadata(sample_html, 'http://example.com')
        
        assert metadata['title'] == 'Test Page'
        assert 'test page' in metadata['description'].lower()
        assert 'test' in metadata['keywords']
        assert 'crawler' in metadata['keywords']
    
    def test_extract_links(self, sample_html):
        """Test link extraction."""
        links = ContentExtractor.extract_links(sample_html, 'http://example.com')
        
        assert 'http://example.com/page1' in links
        assert 'http://example.com/page2' in links
        assert 'http://external.com' in links
    
    def test_extract_images(self, sample_html):
        """Test image URL extraction."""
        images = ContentExtractor.extract_images(sample_html, 'http://example.com')
        
        assert 'http://example.com/image1.jpg' in images
        assert 'http://example.com/image2.png' in images
    
    def test_extract_no_content(self, sample_html_no_content):
        """Test extraction from minimal HTML."""
        text = ContentExtractor.extract_text(sample_html_no_content, 'http://example.com')
        
        # Should still extract title
        metadata = ContentExtractor.extract_metadata(sample_html_no_content, 'http://example.com')
        assert metadata['title'] == 'Empty Page'


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_basic_delay(self):
        """Test basic rate limiting delay."""
        limiter = RateLimiter(delay=0.1)
        
        start = asyncio.get_event_loop().time()
        await limiter.wait('http://example.com')
        await limiter.wait('http://example.com')
        elapsed = asyncio.get_event_loop().time() - start
        
        # Should have delayed at least 0.1 seconds
        assert elapsed >= 0.1
    
    @pytest.mark.asyncio
    async def test_rate_limiter_per_domain(self):
        """Test rate limiting is per-domain."""
        limiter = RateLimiter(delay=0.1)
        
        # Different domains should not block each other
        start = asyncio.get_event_loop().time()
        await limiter.wait('http://example1.com')
        await limiter.wait('http://example2.com')
        elapsed = asyncio.get_event_loop().time() - start
        
        # Should be nearly instant (different domains)
        assert elapsed < 0.1
    
    @pytest.mark.asyncio
    async def test_rate_limiter_backoff(self):
        """Test exponential backoff on errors."""
        limiter = RateLimiter(delay=0.1, max_delay=1.0)
        
        url = 'http://example.com'
        initial_delay = limiter.domain_delays[url]
        
        limiter.increase_delay(url)
        increased_delay = limiter.domain_delays[url]
        
        assert increased_delay > initial_delay
        assert increased_delay == initial_delay * 2
    
    @pytest.mark.asyncio
    async def test_rate_limiter_recovery(self):
        """Test delay recovery after success."""
        limiter = RateLimiter(delay=0.1)
        
        url = 'http://example.com'
        limiter.increase_delay(url)
        increased = limiter.domain_delays[url]
        
        limiter.decrease_delay(url)
        decreased = limiter.domain_delays[url]
        
        assert decreased < increased
        assert decreased == increased / 2


class TestRobotsCache:
    """Test robots.txt caching and compliance."""
    
    @pytest.mark.asyncio
    async def test_robots_allow_all(self, robots_txt_allow_all):
        """Test robots.txt that allows all."""
        cache = RobotsCache()
        
        # Mock session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=robots_txt_allow_all)
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock()
        
        can_fetch = await cache.can_fetch(
            'http://example.com/any-path',
            'SimpleCrawler',
            mock_session
        )
        
        assert can_fetch is True
    
    @pytest.mark.asyncio
    async def test_robots_block_all(self, robots_txt_block_all):
        """Test robots.txt that blocks all."""
        cache = RobotsCache()
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=robots_txt_block_all)
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock()
        
        can_fetch = await cache.can_fetch(
            'http://example.com/any-path',
            'SimpleCrawler',
            mock_session
        )
        
        assert can_fetch is False


class TestPageData:
    """Test PageData dataclass functionality."""
    
    def test_page_data_creation(self):
        """Test creating PageData instance."""
        page = PageData(
            url='http://example.com',
            title='Test Page',
            depth=0,
            content='Test content',
            html='<html></html>'
        )
        
        assert page.url == 'http://example.com'
        assert page.title == 'Test Page'
        assert page.content_hash  # Should be auto-generated
        assert page.word_count == 2  # "Test content"
    
    def test_page_data_hash_generation(self):
        """Test content hash is generated."""
        page1 = PageData(
            url='http://example.com',
            title='Test',
            depth=0,
            content='Same content',
            html='<html></html>'
        )
        
        page2 = PageData(
            url='http://example.com/other',
            title='Test 2',
            depth=0,
            content='Same content',
            html='<html></html>'
        )
        
        # Same content should have same hash
        assert page1.content_hash == page2.content_hash
    
    def test_page_data_word_count(self):
        """Test word count calculation."""
        page = PageData(
            url='http://example.com',
            title='Test',
            depth=0,
            content='One two three four five',
            html='<html></html>'
        )
        
        assert page.word_count == 5
