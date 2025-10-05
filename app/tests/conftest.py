"""
Pytest configuration and shared fixtures for SimpleCrawler tests.
"""

import asyncio
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any
from unittest.mock import Mock, AsyncMock
from aiohttp import web
from app import CrawlConfig, WebCrawler


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_output_dir() -> Generator[Path, None, None]:
    """Create temporary output directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def basic_config(temp_output_dir: Path) -> CrawlConfig:
    """Basic crawler configuration for testing."""
    return CrawlConfig(
        start_url="http://example.com",
        max_pages=10,
        max_depth=2,
        output_dir=str(temp_output_dir),
        verbose=False,
        debug=False,
        delay=0.1,  # Fast for testing
        max_concurrent=3
    )


@pytest.fixture
def sample_html() -> str:
    """Sample HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <meta name="description" content="A test page for crawling">
        <meta name="keywords" content="test, crawler, python">
        <meta property="og:title" content="Test Page OG">
    </head>
    <body>
        <main>
            <h1>Main Content</h1>
            <p>This is a test page with some content.</p>
            <a href="/page1">Page 1</a>
            <a href="/page2">Page 2</a>
            <a href="http://external.com">External</a>
            <img src="/image1.jpg" alt="Image 1">
            <img src="http://example.com/image2.png" alt="Image 2">
        </main>
        <script>console.log('test');</script>
        <style>body { color: red; }</style>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_no_content() -> str:
    """HTML with minimal content."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Empty Page</title></head>
    <body></body>
    </html>
    """


@pytest.fixture
def robots_txt_allow_all() -> str:
    """Robots.txt that allows all."""
    return """
    User-agent: *
    Disallow:
    """


@pytest.fixture
def robots_txt_block_all() -> str:
    """Robots.txt that blocks all."""
    return """
    User-agent: *
    Disallow: /
    """


@pytest.fixture
def robots_txt_partial() -> str:
    """Robots.txt with partial blocking."""
    return """
    User-agent: *
    Disallow: /private/
    Disallow: /admin/
    Allow: /public/
    """


@pytest.fixture
async def mock_server(sample_html: str, robots_txt_allow_all: str):
    """
    Create a mock HTTP server for testing.
    
    Provides endpoints:
    - GET / - returns sample HTML
    - GET /page{n} - returns page HTML with links
    - GET /robots.txt - returns robots.txt
    - GET /error - returns 500
    - GET /timeout - delays 30 seconds
    - GET /redirect - redirects to /
    """
    async def index_handler(request):
        return web.Response(text=sample_html, content_type='text/html')
    
    async def page_handler(request):
        page_num = request.match_info.get('num', '1')
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Page {page_num}</title></head>
        <body>
            <h1>Page {page_num}</h1>
            <p>Content for page {page_num}</p>
            <a href="/page{int(page_num) + 1}">Next Page</a>
            <a href="/">Home</a>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def robots_handler(request):
        return web.Response(text=robots_txt_allow_all, content_type='text/plain')
    
    async def error_handler(request):
        return web.Response(status=500, text="Internal Server Error")
    
    async def timeout_handler(request):
        await asyncio.sleep(30)
        return web.Response(text="Delayed response")
    
    async def redirect_handler(request):
        return web.Response(status=302, headers={'Location': '/'})
    
    async def json_handler(request):
        return web.json_response({'message': 'This is JSON, not HTML'})
    
    app = web.Application()
    app.router.add_get('/', index_handler)
    app.router.add_get('/page{num}', page_handler)
    app.router.add_get('/robots.txt', robots_handler)
    app.router.add_get('/error', error_handler)
    app.router.add_get('/timeout', timeout_handler)
    app.router.add_get('/redirect', redirect_handler)
    app.router.add_get('/json', json_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8765)
    await site.start()
    
    yield 'http://localhost:8765'
    
    await runner.cleanup()


@pytest.fixture
def documentation_sites() -> Dict[str, str]:
    """
    Real documentation sites for integration testing.
    
    These are well-structured, crawler-friendly documentation sites.
    """
    return {
        'python_docs': 'https://docs.python.org/3/library/asyncio.html',
        'requests_docs': 'https://requests.readthedocs.io/en/latest/',
        'aiohttp_docs': 'https://docs.aiohttp.org/en/stable/',
        'beautifulsoup_docs': 'https://www.crummy.com/software/BeautifulSoup/bs4/doc/',
        'pytest_docs': 'https://docs.pytest.org/en/stable/',
        'rich_docs': 'https://rich.readthedocs.io/en/stable/',
        'github_docs': 'https://docs.github.com/en/get-started',
        'mdn_html': 'https://developer.mozilla.org/en-US/docs/Web/HTML',
    }


@pytest.fixture
def cli_args_matrix() -> Dict[str, list]:
    """
    Comprehensive matrix of CLI argument combinations.
    
    Returns dictionary mapping test scenario names to argument lists.
    """
    return {
        'basic': ['http://example.com'],
        'with_max_pages': ['http://example.com', '--max-pages', '50'],
        'with_depth': ['http://example.com', '--max-depth', '5'],
        'single_domain': ['http://example.com', '--single-domain'],
        'with_delay': ['http://example.com', '--delay', '2.0'],
        'high_concurrency': ['http://example.com', '--concurrency', '20'],
        'json_export': ['http://example.com', '--format', 'json'],
        'csv_export': ['http://example.com', '--format', 'csv'],
        'markdown_export': ['http://example.com', '--format', 'markdown'],
        'with_images': ['http://example.com', '--images'],
        'no_dedupe': ['http://example.com', '--no-dedupe'],
        'no_robots': ['http://example.com', '--no-robots'],
        'verbose': ['http://example.com', '--verbose'],
        'debug': ['http://example.com', '--debug'],
        'custom_output': ['http://example.com', '--output-dir', 'custom_output'],
        'max_retries': ['http://example.com', '--retries', '5'],
        
        # Combined arguments
        'full_featured': [
            'http://example.com',
            '--max-pages', '100',
            '--max-depth', '3',
            '--single-domain',
            '--delay', '1.0',
            '--concurrency', '10',
            '--format', 'json',
            '--images',
            '--verbose'
        ],
        'fast_shallow': [
            'http://example.com',
            '--max-pages', '20',
            '--max-depth', '1',
            '--delay', '0.5',
            '--concurrency', '15'
        ],
        'deep_thorough': [
            'http://example.com',
            '--max-pages', '500',
            '--max-depth', '5',
            '--delay', '2.0',
            '--concurrency', '5',
            '--no-dedupe'
        ],
        
        # Edge cases
        'minimal_depth': ['http://example.com', '--max-depth', '0'],
        'single_page': ['http://example.com', '--max-pages', '1'],
        'zero_delay': ['http://example.com', '--delay', '0'],
        'max_concurrency': ['http://example.com', '--concurrency', '50'],
    }


@pytest.fixture
def invalid_cli_args() -> Dict[str, tuple]:
    """
    Invalid CLI argument combinations and expected error messages.
    
    Returns dictionary mapping scenario to (args, expected_error_substring).
    """
    return {
        'invalid_url': (
            ['not-a-url', '--max-pages', '10'],
            'Invalid URL'
        ),
        'negative_pages': (
            ['http://example.com', '--max-pages', '-10'],
            'invalid'
        ),
        'negative_depth': (
            ['http://example.com', '--max-depth', '-5'],
            'invalid'
        ),
        'invalid_format': (
            ['http://example.com', '--format', 'xml'],
            'invalid choice'
        ),
        'negative_delay': (
            ['http://example.com', '--delay', '-1.0'],
            'invalid'
        ),
        'zero_concurrency': (
            ['http://example.com', '--concurrency', '0'],
            'invalid'
        ),
        'no_url': (
            ['--max-pages', '10'],
            'required'
        ),
    }


@pytest.fixture
def mock_crawler_results() -> list:
    """Mock crawl results for testing exporters."""
    from app import PageData
    
    return [
        PageData(
            url='http://example.com/',
            title='Example Domain',
            depth=0,
            content='This is the main page content.',
            html='<html><body>Content</body></html>',
            description='Example domain',
            keywords=['example', 'domain'],
            links=['http://example.com/page1', 'http://example.com/page2'],
            images=['http://example.com/logo.png'],
            status_code=200,
            load_time=0.5,
            word_count=10
        ),
        PageData(
            url='http://example.com/page1',
            title='Page 1',
            depth=1,
            content='Content for page 1.',
            html='<html><body>Page 1</body></html>',
            description='First page',
            keywords=['page', 'one'],
            links=['http://example.com/', 'http://example.com/page2'],
            images=[],
            status_code=200,
            load_time=0.3,
            word_count=15
        ),
    ]


@pytest.fixture
def performance_urls() -> list:
    """URLs for performance testing."""
    return [
        f'http://localhost:8765/page{i}' 
        for i in range(100)
    ]
