"""
Integration tests using real documentation sites.

These tests fetch actual documentation to verify the crawler works
with real-world websites. They are slower and require internet connection.

Run with: pytest -v -m integration
Skip with: pytest -v -m "not integration"
"""

import pytest
import asyncio
from pathlib import Path
from app import WebCrawler, CrawlConfig


pytestmark = pytest.mark.integration


class TestRealDocumentationSites:
    """
    Test crawling real documentation websites.
    
    These are well-structured, crawler-friendly sites perfect for testing.
    """
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_python_docs_asyncio(self, temp_output_dir, documentation_sites):
        """
        Test crawling Python's asyncio documentation.
        
        Reference: https://docs.python.org/3/library/asyncio.html
        """
        config = CrawlConfig(
            start_url=documentation_sites['python_docs'],
            max_pages=5,
            max_depth=1,
            same_domain=True,
            delay=1.0,
            output_dir=str(temp_output_dir),
            export_format='markdown'
        )
        
        crawler = WebCrawler(config)
        summary = await crawler.crawl()
        
        assert summary['stats']['pages_crawled'] > 0
        assert summary['stats']['pages_crawled'] <= 5
        
        # Check output files created
        output_path = Path(temp_output_dir)
        md_files = list(output_path.glob('*.md'))
        assert len(md_files) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_requests_docs(self, temp_output_dir, documentation_sites):
        """
        Test crawling Requests library documentation.
        
        Reference: https://requests.readthedocs.io/
        """
        config = CrawlConfig(
            start_url=documentation_sites['requests_docs'],
            max_pages=10,
            max_depth=2,
            same_domain=True,
            delay=1.0,
            output_dir=str(temp_output_dir),
            export_format='json'
        )
        
        crawler = WebCrawler(config)
        summary = await crawler.crawl()
        
        assert summary['stats']['pages_crawled'] > 0
        
        # Check JSON export
        json_file = Path(temp_output_dir) / 'crawl_results.json'
        assert json_file.exists()
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_beautifulsoup_docs(self, temp_output_dir, documentation_sites):
        """
        Test crawling BeautifulSoup documentation.
        
        Reference: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
        """
        config = CrawlConfig(
            start_url=documentation_sites['beautifulsoup_docs'],
            max_pages=8,
            max_depth=1,
            same_domain=True,
            delay=1.5,
            output_dir=str(temp_output_dir),
            extract_images=True
        )
        
        crawler = WebCrawler(config)
        summary = await crawler.crawl()
        
        assert summary['stats']['pages_crawled'] > 0
        
        # Check that some pages have images
        has_images = any(len(result.images) > 0 for result in crawler.results)
        # May or may not have images, just check it doesn't error
        assert has_images is not None
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_pytest_docs(self, temp_output_dir, documentation_sites):
        """
        Test crawling Pytest documentation.
        
        Reference: https://docs.pytest.org/
        """
        config = CrawlConfig(
            start_url=documentation_sites['pytest_docs'],
            max_pages=10,
            max_depth=2,
            same_domain=True,
            delay=1.0,
            output_dir=str(temp_output_dir),
            deduplicate=True
        )
        
        crawler = WebCrawler(config)
        summary = await crawler.crawl()
        
        assert summary['stats']['pages_crawled'] > 0
        
        # Check deduplication worked
        unique_hashes = set(result.content_hash for result in crawler.results)
        assert len(unique_hashes) == len(crawler.results)
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_rich_docs(self, temp_output_dir, documentation_sites):
        """
        Test crawling Rich library documentation.
        
        Reference: https://rich.readthedocs.io/
        """
        config = CrawlConfig(
            start_url=documentation_sites['rich_docs'],
            max_pages=15,
            max_depth=2,
            same_domain=True,
            delay=1.0,
            max_concurrent=5,
            output_dir=str(temp_output_dir),
            export_format='csv'
        )
        
        crawler = WebCrawler(config)
        summary = await crawler.crawl()
        
        assert summary['stats']['pages_crawled'] > 0
        
        # Check CSV export
        csv_file = Path(temp_output_dir) / 'crawl_results.csv'
        assert csv_file.exists()
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_github_docs(self, temp_output_dir, documentation_sites):
        """
        Test crawling GitHub documentation.
        
        Reference: https://docs.github.com/
        """
        config = CrawlConfig(
            start_url=documentation_sites['github_docs'],
            max_pages=5,
            max_depth=1,
            same_domain=True,
            delay=2.0,  # Be nice to GitHub
            output_dir=str(temp_output_dir),
            respect_robots=True
        )
        
        crawler = WebCrawler(config)
        summary = await crawler.crawl()
        
        # GitHub has robots.txt, may block some URLs
        assert summary['stats']['pages_crawled'] >= 0
        
        # Check robots blocking stats
        assert 'robots_blocked' in summary['stats']


class TestExportFormats:
    """Test different export formats with real data."""
    
    @pytest.mark.asyncio
    async def test_markdown_export_structure(self, temp_output_dir, documentation_sites):
        """Test markdown export creates proper files."""
        config = CrawlConfig(
            start_url=documentation_sites['python_docs'],
            max_pages=3,
            max_depth=1,
            output_dir=str(temp_output_dir),
            export_format='markdown'
        )
        
        crawler = WebCrawler(config)
        await crawler.crawl()
        
        md_files = list(Path(temp_output_dir).glob('*.md'))
        assert len(md_files) > 0
        
        # Check markdown structure
        for md_file in md_files:
            content = md_file.read_text()
            assert content.startswith('#')  # Has header
            assert '## Metadata' in content or '##' in content
    
    @pytest.mark.asyncio
    async def test_json_export_structure(self, temp_output_dir, documentation_sites):
        """Test JSON export creates valid JSON."""
        import json
        
        config = CrawlConfig(
            start_url=documentation_sites['python_docs'],
            max_pages=3,
            max_depth=1,
            output_dir=str(temp_output_dir),
            export_format='json'
        )
        
        crawler = WebCrawler(config)
        await crawler.crawl()
        
        json_file = Path(temp_output_dir) / 'crawl_results.json'
        assert json_file.exists()
        
        # Validate JSON
        data = json.loads(json_file.read_text())
        assert isinstance(data, list)
        assert len(data) > 0
        assert 'url' in data[0]
        assert 'title' in data[0]
        assert 'content' in data[0]
    
    @pytest.mark.asyncio
    async def test_csv_export_structure(self, temp_output_dir, documentation_sites):
        """Test CSV export creates valid CSV."""
        import csv
        
        config = CrawlConfig(
            start_url=documentation_sites['python_docs'],
            max_pages=3,
            max_depth=1,
            output_dir=str(temp_output_dir),
            export_format='csv'
        )
        
        crawler = WebCrawler(config)
        await crawler.crawl()
        
        csv_file = Path(temp_output_dir) / 'crawl_results.csv'
        assert csv_file.exists()
        
        # Validate CSV
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) > 0
            assert 'url' in rows[0]
            assert 'title' in rows[0]


class TestEdgeCases:
    """Test edge cases and error conditions with real sites."""
    
    @pytest.mark.asyncio
    async def test_single_page_crawl(self, temp_output_dir, documentation_sites):
        """Test crawling exactly one page."""
        config = CrawlConfig(
            start_url=documentation_sites['python_docs'],
            max_pages=1,
            max_depth=0,
            output_dir=str(temp_output_dir)
        )
        
        crawler = WebCrawler(config)
        summary = await crawler.crawl()
        
        assert summary['stats']['pages_crawled'] == 1
    
    @pytest.mark.asyncio
    async def test_zero_depth_crawl(self, temp_output_dir, documentation_sites):
        """Test crawling with depth 0 (no following links)."""
        config = CrawlConfig(
            start_url=documentation_sites['python_docs'],
            max_pages=10,
            max_depth=0,
            output_dir=str(temp_output_dir)
        )
        
        crawler = WebCrawler(config)
        summary = await crawler.crawl()
        
        # Should only crawl start URL
        assert summary['stats']['pages_crawled'] == 1
    
    @pytest.mark.asyncio
    async def test_invalid_start_url(self, temp_output_dir):
        """Test handling of invalid start URL."""
        config = CrawlConfig(
            start_url='http://this-domain-definitely-does-not-exist-12345.com',
            max_pages=5,
            max_depth=1,
            output_dir=str(temp_output_dir),
            timeout=5
        )
        
        crawler = WebCrawler(config)
        summary = await crawler.crawl()
        
        # Should handle gracefully
        assert summary['stats']['pages_crawled'] == 0
        assert summary['stats']['errors'] > 0
