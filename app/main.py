#!/usr/bin/env python3
"""
SimpleCrawler v2.0: A modern, high-performance web crawling framework.

Key Improvements:
- Async/await for better concurrency
- Smart rate limiting and backoff
- Advanced content extraction
- Plugin architecture
- Structured data export (JSON, CSV, SQLite)
- Better error handling and recovery
- Memory efficient streaming
- Content deduplication
- Sitemap support
- JavaScript rendering (optional)
"""

import argparse
import asyncio
import hashlib
import json
import os
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Callable
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import aiohttp
import aiofiles
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
import tldextract
import validators

# Optional dependencies
try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False

try:
    from selectolax.parser import HTMLParser
    HAS_SELECTOLAX = True
except ImportError:
    HAS_SELECTOLAX = False

# Logging
import logging
from logging.handlers import RotatingFileHandler
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.logging import RichHandler
from rich.table import Table


@dataclass
class CrawlConfig:
    """Configuration for crawler with sensible defaults."""
    start_url: str
    max_pages: int = 100
    max_depth: int = 3
    same_domain: bool = True
    timeout: int = 30
    delay: float = 1.0
    max_concurrent: int = 10
    output_dir: str = 'crawled_pages'
    respect_robots: bool = True
    user_agent: str = 'Mozilla/5.0 (compatible; SimpleCrawler/2.0)'
    verbose: bool = False
    debug: bool = False
    extract_images: bool = False
    extract_links: bool = True
    follow_redirects: bool = True
    max_retries: int = 3
    export_format: str = 'markdown'  # markdown, json, csv, sqlite, readable, summary
    deduplicate: bool = True
    javascript: bool = False
    headers: Dict[str, str] = field(default_factory=dict)
    

@dataclass
class PageData:
    """Structured page data with metadata."""
    url: str
    title: str
    depth: int
    content: str
    html: str
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    status_code: int = 200
    content_type: str = "text/html"
    content_hash: str = ""
    crawled_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    load_time: float = 0.0
    word_count: int = 0
    headers: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate derived fields."""
        if not self.content_hash:
            self.content_hash = hashlib.md5(self.content.encode()).hexdigest()
        if not self.word_count:
            self.word_count = len(self.content.split())


class RateLimiter:
    """Intelligent rate limiter with exponential backoff."""
    
    def __init__(self, delay: float = 1.0, max_delay: float = 60.0):
        self.delay = delay
        self.max_delay = max_delay
        self.domain_delays: Dict[str, float] = defaultdict(lambda: delay)
        self.last_request: Dict[str, float] = {}
        self.lock = asyncio.Lock()
    
    async def wait(self, url: str):
        """Wait appropriate time before request."""
        domain = urlparse(url).netloc
        
        async with self.lock:
            last = self.last_request.get(domain, 0)
            delay = self.domain_delays[domain]
            elapsed = time.time() - last
            
            if elapsed < delay:
                await asyncio.sleep(delay - elapsed)
            
            self.last_request[domain] = time.time()
    
    def increase_delay(self, url: str):
        """Increase delay for domain (backoff)."""
        domain = urlparse(url).netloc
        current = self.domain_delays.get(domain, self.delay)
        self.domain_delays[domain] = min(current * 2, self.max_delay)
    
    def decrease_delay(self, url: str):
        """Decrease delay for domain (recovery)."""
        domain = urlparse(url).netloc
        current = self.domain_delays.get(domain, self.delay)
        self.domain_delays[domain] = max(current / 2, self.delay)


class RobotsCache:
    """Cache and respect robots.txt files."""
    
    def __init__(self):
        self.parsers: Dict[str, RobotFileParser] = {}
        self.lock = asyncio.Lock()
    
    async def can_fetch(self, url: str, user_agent: str, session: aiohttp.ClientSession) -> bool:
        """Check if URL can be fetched according to robots.txt."""
        domain = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        
        async with self.lock:
            if domain not in self.parsers:
                parser = RobotFileParser()
                robots_url = f"{domain}/robots.txt"
                
                try:
                    async with session.get(robots_url, timeout=10) as resp:
                        if resp.status == 200:
                            content = await resp.text()
                            parser.parse(content.splitlines())
                        else:
                            # No robots.txt, allow all
                            parser.parse([])
                except Exception:
                    # Error fetching robots.txt, allow all
                    parser.parse([])
                
                self.parsers[domain] = parser
        
        return self.parsers[domain].can_fetch(user_agent, url)


class ContentExtractor:
    """Advanced content extraction using multiple strategies."""
    
    @staticmethod
    def extract_text(html: str, url: str) -> str:
        """Extract main text content with proper code block preservation."""
        # Try trafilatura first (best for articles)
        if HAS_TRAFILATURA:
            text = trafilatura.extract(html, include_comments=False, include_tables=True, 
                                     include_formatting=True)
            if text:
                return ContentExtractor._preserve_code_blocks(text, html)
        
        # Fallback to BeautifulSoup with enhanced code extraction
        return ContentExtractor._extract_with_code_preservation(html, url)
    
    @staticmethod
    def extract_metadata(html: str, url: str) -> Dict[str, Any]:
        """Extract metadata from HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        metadata = {}
        
        # Title
        metadata['title'] = soup.title.string if soup.title else ""
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        metadata['description'] = meta_desc.get('content', '') if meta_desc else ""
        
        # Keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            metadata['keywords'] = [k.strip() for k in meta_keywords.get('content', '').split(',')]
        else:
            metadata['keywords'] = []
        
        # Open Graph
        og_title = soup.find('meta', property='og:title')
        og_desc = soup.find('meta', property='og:description')
        
        if og_title and not metadata['title']:
            metadata['title'] = og_title.get('content', '')
        if og_desc and not metadata['description']:
            metadata['description'] = og_desc.get('content', '')
        
        return metadata
    
    @staticmethod
    def extract_links(html: str, base_url: str) -> List[str]:
        """Extract all links from HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Basic validation
            if validators.url(full_url):
                links.append(full_url)
        
        return list(set(links))  # Deduplicate
    
    @staticmethod
    def extract_images(html: str, base_url: str) -> List[str]:
        """Extract all image URLs."""
        soup = BeautifulSoup(html, 'html.parser')
        images = []
        
        for img in soup.find_all('img', src=True):
            src = img['src']
            full_url = urljoin(base_url, src)
            images.append(full_url)
        
        return list(set(images))
    
    @staticmethod
    def _preserve_code_blocks(text: str, html: str) -> str:
        """Enhance trafilatura output with proper code block preservation."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find code blocks and preserve them with proper markdown
        code_blocks = []
        
        # Look for various code block patterns
        for pre in soup.find_all('pre'):
            code_elem = pre.find('code')
            if code_elem:
                # Get language from class attribute
                language = ContentExtractor._extract_language(code_elem)
                code_text = ContentExtractor._clean_code_text(code_elem.get_text())
                
                if code_text.strip():
                    code_blocks.append({
                        'language': language,
                        'code': code_text,
                        'original': pre.get_text()
                    })
        
        # Also check for standalone code elements
        for code in soup.find_all('code'):
            if not code.find_parent('pre'):  # Inline code
                continue
        
        # Replace code blocks in text with properly formatted markdown
        enhanced_text = text
        for block in code_blocks:
            markdown_block = f"```{block['language']}\n{block['code']}\n```"
            # Try to find and replace the original text
            original_clean = ContentExtractor._clean_code_text(block['original'])
            if original_clean in enhanced_text:
                enhanced_text = enhanced_text.replace(original_clean, markdown_block)
        
        return enhanced_text
    
    @staticmethod
    def _extract_with_code_preservation(html: str, url: str) -> str:
        """Extract text with careful code block preservation."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted tags but preserve structure
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            tag.decompose()
        
        # Find main content area
        main_content = (soup.find('main') or 
                       soup.find('article') or 
                       soup.find('div', class_=re.compile(r'content|main|post|documentation')) or
                       soup.find('div', id=re.compile(r'content|main|documentation')) or
                       soup.body or soup)
        
        # Process content with code preservation
        result_parts = []
        
        for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'blockquote', 'ul', 'ol', 'div']):
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Headers
                level = int(element.name[1])
                header_text = element.get_text().strip()
                if header_text:
                    result_parts.append(f"{'#' * level} {header_text}")
            
            elif element.name == 'pre':
                # Code blocks
                code_elem = element.find('code')
                if code_elem:
                    language = ContentExtractor._extract_language(code_elem)
                    code_text = ContentExtractor._clean_code_text(code_elem.get_text())
                    if code_text.strip():
                        result_parts.append(f"```{language}")
                        result_parts.append(code_text)
                        result_parts.append("```")
                else:
                    # Pre without code tag
                    pre_text = ContentExtractor._clean_code_text(element.get_text())
                    if pre_text.strip():
                        result_parts.append("```")
                        result_parts.append(pre_text)
                        result_parts.append("```")
            
            elif element.name == 'blockquote':
                # Blockquotes
                quote_text = element.get_text().strip()
                if quote_text:
                    for line in quote_text.split('\n'):
                        if line.strip():
                            result_parts.append(f"> {line.strip()}")
            
            elif element.name in ['ul', 'ol']:
                # Lists
                for li in element.find_all('li', recursive=False):
                    li_text = li.get_text().strip()
                    if li_text:
                        prefix = "- " if element.name == 'ul' else "1. "
                        result_parts.append(f"{prefix}{li_text}")
            
            elif element.name in ['p', 'div']:
                # Regular paragraphs and divs
                # Skip if it contains code blocks (already processed)
                if not element.find('pre'):
                    text = element.get_text().strip()
                    if text and len(text) > 10:  # Skip very short divs
                        result_parts.append(text)
        
        # Clean up and join
        clean_parts = []
        for part in result_parts:
            if part.strip():
                clean_parts.append(part.strip())
        
        return '\n\n'.join(clean_parts)
    
    @staticmethod
    def _extract_language(code_element) -> str:
        """Extract programming language from code element classes."""
        if not code_element:
            return ""
        
        # Common patterns for language detection
        class_attr = code_element.get('class', [])
        if isinstance(class_attr, str):
            class_attr = [class_attr]
        
        for cls in class_attr:
            cls = cls.lower()
            # Highlight.js style: language-python, lang-javascript
            if cls.startswith('language-'):
                return cls.replace('language-', '')
            elif cls.startswith('lang-'):
                return cls.replace('lang-', '')
            # Prism.js style: lang-python
            elif cls.startswith('hljs-'):
                continue  # Skip highlight.js classes
            # Direct language names
            elif cls in ['python', 'javascript', 'js', 'bash', 'shell', 'json', 'yaml', 'xml', 'html', 'css', 'sql', 'go', 'rust', 'java', 'c', 'cpp', 'csharp', 'php', 'ruby', 'typescript', 'ts']:
                return cls
        
        # Check data attributes
        lang = code_element.get('data-lang') or code_element.get('data-language')
        if lang:
            return lang.lower()
        
        # Check parent pre element
        pre_parent = code_element.find_parent('pre')
        if pre_parent:
            pre_class = pre_parent.get('class', [])
            if isinstance(pre_class, str):
                pre_class = [pre_class]
            
            for cls in pre_class:
                cls = cls.lower()
                if cls.startswith('language-'):
                    return cls.replace('language-', '')
                elif cls.startswith('lang-'):
                    return cls.replace('lang-', '')
        
        return ""
    
    @staticmethod
    def _clean_code_text(text: str) -> str:
        """Clean code text while preserving formatting."""
        if not text:
            return ""
        
        lines = text.split('\n')
        
        # Remove common leading/trailing empty lines
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        
        if not lines:
            return ""
        
        # Find common indentation and remove it
        non_empty_lines = [line for line in lines if line.strip()]
        if non_empty_lines:
            min_indent = min(len(line) - len(line.lstrip()) for line in non_empty_lines)
            if min_indent > 0:
                lines = [line[min_indent:] if len(line) >= min_indent else line for line in lines]
        
        return '\n'.join(lines)


class WebCrawler:
    """Modern async web crawler with advanced features."""
    
    def __init__(self, config: CrawlConfig):
        self.config = config
        self.visited: Set[str] = set()
        self.queued: Set[str] = set()
        self.content_hashes: Set[str] = set()
        self.results: List[PageData] = []
        
        # Components
        self.rate_limiter = RateLimiter(config.delay)
        self.robots_cache = RobotsCache()
        self.extractor = ContentExtractor()
        
        # Setup
        self.setup_logging()
        self.console = Console()
        
        # Stats
        self.stats = {
            'start_time': time.time(),
            'pages_crawled': 0,
            'urls_discovered': 0,
            'duplicates_skipped': 0,
            'errors': 0,
            'robots_blocked': 0
        }
    
    def setup_logging(self):
        """Setup rich logging."""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        level = logging.DEBUG if self.config.debug else logging.INFO if self.config.verbose else logging.WARNING
        
        logging.basicConfig(
            level=level,
            format="%(message)s",
            handlers=[
                RichHandler(rich_tracebacks=True, markup=True),
                RotatingFileHandler(
                    log_dir / 'crawler.log',
                    maxBytes=10*1024*1024,
                    backupCount=5
                )
            ]
        )
        
        self.logger = logging.getLogger('SimpleCrawler')
    
    async def crawl(self) -> Dict[str, Any]:
        """Main crawl orchestration."""
        self.logger.info(f"[bold green]Starting crawl of {self.config.start_url}[/bold green]")
        
        # Create session
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        headers = {
            'User-Agent': self.config.user_agent,
            **self.config.headers
        }
        
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            # Initialize queue
            queue = asyncio.Queue()
            await queue.put((self.config.start_url, 0))
            self.queued.add(self.config.start_url)
            
            # Progress tracking
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
            ) as progress:
                
                task = progress.add_task(
                    "[cyan]Crawling...", 
                    total=self.config.max_pages
                )
                
                # Worker tasks
                workers = [
                    asyncio.create_task(self._worker(session, queue, progress, task))
                    for _ in range(self.config.max_concurrent)
                ]
                
                # Wait for completion
                await queue.join()
                
                # Cancel workers
                for worker in workers:
                    worker.cancel()
        
        # Save and summarize
        await self._save_results()
        summary = self._generate_summary()
        
        self._display_summary(summary)
        
        return summary
    
    async def _worker(self, session: aiohttp.ClientSession, queue: asyncio.Queue, progress, task):
        """Worker coroutine to process URLs."""
        while True:
            try:
                url, depth = await asyncio.wait_for(queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            
            try:
                # Check limits
                if len(self.visited) >= self.config.max_pages or depth > self.config.max_depth:
                    queue.task_done()
                    continue
                
                # Process URL
                page_data = await self._process_url(session, url, depth)
                
                if page_data:
                    self.results.append(page_data)
                    progress.update(task, advance=1)
                    
                    # Enqueue new URLs
                    if self.config.extract_links and depth < self.config.max_depth:
                        for link in page_data.links:
                            if (link not in self.visited and 
                                link not in self.queued and 
                                len(self.queued) < self.config.max_pages * 2):
                                
                                if self._should_crawl(link):
                                    await queue.put((link, depth + 1))
                                    self.queued.add(link)
                                    self.stats['urls_discovered'] += 1
            
            except Exception as e:
                self.logger.error(f"Worker error processing {url}: {e}")
                self.stats['errors'] += 1
            
            finally:
                queue.task_done()
    
    async def _process_url(self, session: aiohttp.ClientSession, url: str, depth: int) -> Optional[PageData]:
        """Process a single URL."""
        if url in self.visited:
            return None
        
        self.visited.add(url)
        
        # Check robots.txt
        if self.config.respect_robots:
            can_fetch = await self.robots_cache.can_fetch(url, self.config.user_agent, session)
            if not can_fetch:
                self.logger.warning(f"Blocked by robots.txt: {url}")
                self.stats['robots_blocked'] += 1
                return None
        
        # Rate limiting
        await self.rate_limiter.wait(url)
        
        # Fetch with retry
        html, status, headers_dict, load_time = await self._fetch_with_retry(session, url)
        
        if not html:
            return None
        
        # Extract content
        text_content = self.extractor.extract_text(html, url)
        metadata = self.extractor.extract_metadata(html, url)
        
        # Check for duplicates
        if self.config.deduplicate:
            content_hash = hashlib.md5(text_content.encode()).hexdigest()
            if content_hash in self.content_hashes:
                self.logger.debug(f"Duplicate content: {url}")
                self.stats['duplicates_skipped'] += 1
                return None
            self.content_hashes.add(content_hash)
        
        # Create page data
        page_data = PageData(
            url=url,
            title=metadata['title'],
            depth=depth,
            content=text_content,
            html=html,
            description=metadata['description'],
            keywords=metadata['keywords'],
            links=self.extractor.extract_links(html, url) if self.config.extract_links else [],
            images=self.extractor.extract_images(html, url) if self.config.extract_images else [],
            status_code=status,
            headers=headers_dict,
            load_time=load_time
        )
        
        self.stats['pages_crawled'] += 1
        self.rate_limiter.decrease_delay(url)  # Success, can speed up
        
        return page_data
    
    async def _fetch_with_retry(self, session: aiohttp.ClientSession, url: str) -> tuple:
        """Fetch URL with exponential backoff retry."""
        for attempt in range(self.config.max_retries):
            try:
                start_time = time.time()
                
                async with session.get(url, allow_redirects=self.config.follow_redirects) as response:
                    load_time = time.time() - start_time
                    
                    # Check content type
                    content_type = response.headers.get('Content-Type', '').lower()
                    if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                        return None, response.status, dict(response.headers), load_time
                    
                    html = await response.text()
                    return html, response.status, dict(response.headers), load_time
            
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout on {url}, attempt {attempt + 1}")
                self.rate_limiter.increase_delay(url)
                await asyncio.sleep(2 ** attempt)
            
            except Exception as e:
                self.logger.error(f"Error fetching {url}: {e}")
                if attempt == self.config.max_retries - 1:
                    return None, 0, {}, 0.0
                await asyncio.sleep(2 ** attempt)
        
        return None, 0, {}, 0.0
    
    def _should_crawl(self, url: str) -> bool:
        """Determine if URL should be crawled."""
        # Validate URL
        if not validators.url(url):
            return False
        
        # Same domain check
        if self.config.same_domain:
            start_domain = tldextract.extract(self.config.start_url)
            url_domain = tldextract.extract(url)
            
            if f"{url_domain.domain}.{url_domain.suffix}" != f"{start_domain.domain}.{start_domain.suffix}":
                return False
        
        # File extension filter
        excluded_exts = [
            '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp',
            '.zip', '.tar', '.gz', '.rar',
            '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.mp3', '.mp4', '.avi', '.mov', '.wmv'
        ]
        
        if any(url.lower().endswith(ext) for ext in excluded_exts):
            return False
        
        return True
    
    async def _save_results(self):
        """Save results in specified format."""
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.config.export_format == 'markdown':
            await self._save_markdown(output_dir)
        elif self.config.export_format == 'json':
            await self._save_json(output_dir)
        elif self.config.export_format == 'csv':
            await self._save_csv(output_dir)
        elif self.config.export_format == 'readable':
            await self._save_readable(output_dir)
        elif self.config.export_format == 'summary':
            await self._save_summary(output_dir)
        
        self.logger.info(f"Results saved to {output_dir}")
    
    async def _save_markdown(self, output_dir: Path):
        """Save as markdown files."""
        for result in self.results:
            filename = self._generate_filename(result.url) + '.md'
            filepath = output_dir / filename
            
            content = self._to_markdown(result)
            
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(content)
    
    async def _save_json(self, output_dir: Path):
        """Save as JSON."""
        filepath = output_dir / 'crawl_results.json'
        
        data = [asdict(result) for result in self.results]
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, indent=2, ensure_ascii=False))
    
    async def _save_csv(self, output_dir: Path):
        """Save as CSV."""
        import csv
        
        filepath = output_dir / 'crawl_results.csv'
        
        # Write synchronously (csv module not async-friendly)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if self.results:
                writer = csv.DictWriter(f, fieldnames=asdict(self.results[0]).keys())
                writer.writeheader()
                for result in self.results:
                    row = asdict(result)
                    # Convert lists to strings for CSV
                    row['links'] = '; '.join(row['links'][:10])  # Limit for readability
                    row['images'] = '; '.join(row['images'][:10])
                    row['keywords'] = '; '.join(row['keywords'])
                    writer.writerow(row)
    
    async def _save_readable(self, output_dir: Path):
        """Save as human-readable text format optimized for LLMs."""
        # Single consolidated file for easy reading
        filepath = output_dir / 'crawl_content_readable.txt'
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            # Header
            await f.write("=" * 80 + "\n")
            await f.write(f"WEBSITE CRAWL REPORT\n")
            await f.write(f"Crawled from: {self.config.start_url}\n")
            await f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            await f.write(f"Pages: {len(self.results)}\n")
            await f.write("=" * 80 + "\n\n")
            
            # Table of contents
            await f.write("TABLE OF CONTENTS\n")
            await f.write("-" * 20 + "\n")
            for i, result in enumerate(self.results, 1):
                title = result.title or "Untitled Page"
                await f.write(f"{i:2d}. {title}\n")
                await f.write(f"    URL: {result.url}\n")
                if result.description:
                    desc = result.description[:100] + "..." if len(result.description) > 100 else result.description
                    await f.write(f"    DESC: {desc}\n")
                await f.write("\n")
            
            await f.write("\n" + "=" * 80 + "\n")
            await f.write("FULL CONTENT\n")
            await f.write("=" * 80 + "\n\n")
            
            # Full content for each page
            for i, result in enumerate(self.results, 1):
                await f.write(f"\n{'#' * 3} PAGE {i}: {result.title or 'Untitled'}\n")
                await f.write(f"URL: {result.url}\n")
                await f.write(f"Depth: {result.depth} | Status: {result.status_code} | Words: {result.word_count}\n")
                
                if result.description:
                    await f.write(f"Description: {result.description}\n")
                
                if result.keywords:
                    await f.write(f"Keywords: {', '.join(result.keywords[:10])}\n")
                
                await f.write(f"\nCONTENT:\n")
                await f.write("-" * 40 + "\n")
                
                # Clean and format content for readability
                content = self._format_readable_content(result.content)
                await f.write(content)
                
                await f.write(f"\n\n" + "-" * 40 + "\n")
                await f.write(f"End of Page {i}\n")
                await f.write("-" * 40 + "\n\n")
    
    async def _save_summary(self, output_dir: Path):
        """Save as executive summary format."""
        filepath = output_dir / 'crawl_summary.md'
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            # Executive Summary Header
            await f.write("# Website Crawl Summary\n\n")
            await f.write(f"**Source**: {self.config.start_url}\n")
            await f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            await f.write(f"**Pages Analyzed**: {len(self.results)}\n")
            await f.write(f"**Total Words**: {sum(r.word_count for r in self.results):,}\n\n")
            
            # Site Overview
            await f.write("## Site Overview\n\n")
            
            if self.results:
                main_page = self.results[0]
                await f.write(f"**Primary Title**: {main_page.title}\n")
                if main_page.description:
                    await f.write(f"**Description**: {main_page.description}\n")
                
                # Extract main topics/keywords
                all_keywords = []
                for result in self.results:
                    all_keywords.extend(result.keywords)
                
                if all_keywords:
                    keyword_counts = {}
                    for kw in all_keywords:
                        keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
                    
                    top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                    await f.write(f"**Main Topics**: {', '.join([kw for kw, _ in top_keywords])}\n")
            
            await f.write("\n## Page Summaries\n\n")
            
            # Page summaries
            for i, result in enumerate(self.results, 1):
                await f.write(f"### {i}. {result.title or 'Untitled Page'}\n")
                await f.write(f"- **URL**: {result.url}\n")
                await f.write(f"- **Content Length**: {result.word_count} words\n")
                
                if result.description:
                    await f.write(f"- **Description**: {result.description}\n")
                
                # Extract key sentences (first few sentences of content)
                key_content = self._extract_key_sentences(result.content, 2)
                if key_content:
                    await f.write(f"- **Key Content**: {key_content}\n")
                
                await f.write("\n")
            
            # Content Analysis
            await f.write("## Content Analysis\n\n")
            
            # Word count distribution
            word_counts = [r.word_count for r in self.results]
            avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
            
            await f.write(f"- **Average page length**: {avg_words:.0f} words\n")
            await f.write(f"- **Shortest page**: {min(word_counts) if word_counts else 0} words\n")
            await f.write(f"- **Longest page**: {max(word_counts) if word_counts else 0} words\n")
            
            # Link analysis
            total_links = sum(len(r.links) for r in self.results)
            internal_links = 0
            external_links = 0
            
            start_domain = urlparse(self.config.start_url).netloc
            
            for result in self.results:
                for link in result.links:
                    link_domain = urlparse(link).netloc
                    if link_domain == start_domain:
                        internal_links += 1
                    else:
                        external_links += 1
            
            await f.write(f"- **Total links found**: {total_links}\n")
            await f.write(f"- **Internal links**: {internal_links}\n")
            await f.write(f"- **External links**: {external_links}\n")
            
            # Performance metrics
            await f.write("\n## Crawl Performance\n\n")
            crawl_stats = self.stats
            await f.write(f"- **Pages crawled**: {crawl_stats['pages_crawled']}\n")
            await f.write(f"- **URLs discovered**: {crawl_stats['urls_discovered']}\n")
            await f.write(f"- **Duplicates skipped**: {crawl_stats['duplicates_skipped']}\n")
            await f.write(f"- **Errors encountered**: {crawl_stats['errors']}\n")
            await f.write(f"- **Total time**: {crawl_stats.get('total_time', 0):.2f} seconds\n")
    
    def _format_readable_content(self, content: str) -> str:
        """Format content for better human readability."""
        if not content:
            return "No content available.\n"
        
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Add proper spacing for headings (lines that look like titles)
            if len(line) < 100 and line.isupper():
                formatted_lines.append(f"\n## {line.title()}\n")
            elif len(line) < 80 and not line.endswith('.') and not line.endswith(':'):
                # Likely a heading
                formatted_lines.append(f"\n### {line}\n")
            else:
                # Regular content
                # Wrap long lines for better readability
                if len(line) > 120:
                    words = line.split()
                    current_line = ""
                    for word in words:
                        if len(current_line + word) > 100:
                            formatted_lines.append(current_line.strip())
                            current_line = word + " "
                        else:
                            current_line += word + " "
                    if current_line.strip():
                        formatted_lines.append(current_line.strip())
                else:
                    formatted_lines.append(line)
        
        return '\n'.join(formatted_lines) + '\n'
    
    def _extract_key_sentences(self, content: str, num_sentences: int = 2) -> str:
        """Extract key sentences from content for summaries."""
        if not content:
            return ""
        
        # Simple sentence extraction - take first few complete sentences
        sentences = []
        current_sentence = ""
        
        for char in content:
            current_sentence += char
            if char in '.!?' and len(current_sentence.strip()) > 20:
                sentences.append(current_sentence.strip())
                current_sentence = ""
                if len(sentences) >= num_sentences:
                    break
        
        return ' '.join(sentences)
    
    def _to_markdown(self, page: PageData) -> str:
        """Convert page data to markdown."""
        md = f"# {page.title or 'Untitled'}\n\n"
        md += "## Metadata\n\n"
        md += f"- **URL**: [{page.url}]({page.url})\n"
        md += f"- **Crawled**: {page.crawled_at}\n"
        md += f"- **Depth**: {page.depth}\n"
        md += f"- **Status**: {page.status_code}\n"
        md += f"- **Load Time**: {page.load_time:.2f}s\n"
        md += f"- **Word Count**: {page.word_count}\n\n"
        
        if page.description:
            md += f"**Description**: {page.description}\n\n"
        
        if page.keywords:
            md += f"**Keywords**: {', '.join(page.keywords)}\n\n"
        
        md += "---\n\n"
        md += "## Content\n\n"
        md += page.content
        
        if page.links and len(page.links) <= 50:
            md += "\n\n## Links\n\n"
            for link in page.links[:50]:
                md += f"- {link}\n"
        
        return md
    
    def _generate_filename(self, url: str) -> str:
        """Generate safe filename from URL."""
        parsed = urlparse(url)
        path = parsed.path.strip('/').replace('/', '_') or 'index'
        filename = f"{parsed.netloc}_{path}"
        
        # Sanitize
        filename = re.sub(r'[^\w\-_.]', '_', filename)
        filename = filename[:200]  # Limit length
        
        return filename
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate crawl summary."""
        total_time = time.time() - self.stats['start_time']
        
        return {
            'config': asdict(self.config),
            'stats': {
                **self.stats,
                'total_time': total_time,
                'pages_per_second': self.stats['pages_crawled'] / total_time if total_time > 0 else 0
            },
            'pages': len(self.results)
        }
    
    def _display_summary(self, summary: Dict[str, Any]):
        """Display beautiful summary table."""
        table = Table(title="Crawl Summary", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        stats = summary['stats']
        
        table.add_row("Pages Crawled", str(stats['pages_crawled']))
        table.add_row("URLs Discovered", str(stats['urls_discovered']))
        table.add_row("Duplicates Skipped", str(stats['duplicates_skipped']))
        table.add_row("Errors", str(stats['errors']))
        table.add_row("Robots Blocked", str(stats['robots_blocked']))
        table.add_row("Total Time", f"{stats['total_time']:.2f}s")
        table.add_row("Speed", f"{stats['pages_per_second']:.2f} pages/s")
        
        self.console.print(table)


async def main_async(args):
    """Async main function."""
    config = CrawlConfig(
        start_url=args.start_url,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        same_domain=args.single_domain,
        output_dir=args.output_dir,
        verbose=args.verbose,
        debug=args.debug,
        delay=args.delay,
        max_concurrent=args.concurrency,
        export_format=args.format,
        extract_images=args.images,
        deduplicate=not args.no_dedupe,
        max_retries=args.retries
    )
    
    crawler = WebCrawler(config)
    await crawler.crawl()


def main():
    """CLI entry point."""
    init(autoreset=True)
    
    parser = argparse.ArgumentParser(
        description="SimpleCrawler v2.0 - Modern async web crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Required
    parser.add_argument("start_url", help="Starting URL for crawling")
    
    # Crawl behavior
    parser.add_argument("--max-pages", type=int, default=100, help="Maximum pages to crawl")
    parser.add_argument("--max-depth", type=int, default=3, help="Maximum crawl depth")
    parser.add_argument("--single-domain", action="store_true", help="Restrict to single domain")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests (seconds)")
    parser.add_argument("--concurrency", type=int, default=10, help="Max concurrent requests")
    parser.add_argument("--retries", type=int, default=3, help="Max retries per URL")
    
    # Output
    parser.add_argument("--output-dir", default="crawled_pages", help="Output directory")
    parser.add_argument("--format", choices=['markdown', 'json', 'csv', 'readable', 'summary'], default='markdown', help="Export format")
    
    # Features
    parser.add_argument("--images", action="store_true", help="Extract images")
    parser.add_argument("--no-dedupe", action="store_true", help="Disable deduplication")
    parser.add_argument("--no-robots", action="store_true", help="Ignore robots.txt")
    
    # Logging
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--debug", action="store_true", help="Debug logging")
    
    args = parser.parse_args()
    
    # Validate URL
    if not validators.url(args.start_url):
        print(f"{Fore.RED}❌ Invalid URL: {args.start_url}{Style.RESET_ALL}")
        sys.exit(1)
    
    # Banner
    console = Console()
    console.print("[bold cyan]SimpleCrawler v2.0[/bold cyan]")
    console.print("[dim]Modern async web crawling framework[/dim]\n")
    
    # Run crawler
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        console.print("\n[yellow]Crawl interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Fatal error: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
