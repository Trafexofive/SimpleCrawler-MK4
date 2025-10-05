#!/usr/bin/env python3
"""
Basic usage examples for SimpleCrawler MK4.
"""

import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

from app import CrawlConfig, WebCrawler

async def basic_crawl_example():
    """Basic crawling example."""
    print("🕷️ Basic Crawl Example")
    
    config = CrawlConfig(
        start_url='https://example.com',
        max_pages=5,
        max_depth=2,
        output_dir='examples/output/basic',
        verbose=True
    )
    
    crawler = WebCrawler(config)
    summary = await crawler.crawl()
    
    print(f"✅ Crawled {summary['stats']['pages_crawled']} pages")
    return summary

async def documentation_crawl_example():
    """Documentation site crawling example."""
    print("📚 Documentation Crawl Example")
    
    config = CrawlConfig(
        start_url='https://requests.readthedocs.io/en/latest/',
        max_pages=10,
        max_depth=2,
        same_domain=True,
        output_dir='examples/output/docs',
        export_format='json',
        verbose=True,
        delay=1.5,  # Be respectful
        extract_images=False  # Focus on text content
    )
    
    crawler = WebCrawler(config)
    summary = await crawler.crawl()
    
    print(f"✅ Crawled {summary['stats']['pages_crawled']} documentation pages")
    return summary

async def fast_shallow_crawl():
    """Fast shallow crawl for site overview."""
    print("⚡ Fast Shallow Crawl Example")
    
    config = CrawlConfig(
        start_url='https://fastapi.tiangolo.com/',
        max_pages=20,
        max_depth=1,  # Only first level
        same_domain=True,
        output_dir='examples/output/shallow',
        export_format='markdown',
        delay=0.5,  # Faster crawling
        max_concurrent=15,  # More concurrency
        verbose=True
    )
    
    crawler = WebCrawler(config)
    summary = await crawler.crawl()
    
    print(f"✅ Fast crawl completed: {summary['stats']['pages_crawled']} pages")
    return summary

async def comprehensive_crawl():
    """Comprehensive crawl with all features."""
    print("🔍 Comprehensive Crawl Example")
    
    config = CrawlConfig(
        start_url='https://rich.readthedocs.io/en/stable/',
        max_pages=30,
        max_depth=3,
        same_domain=True,
        output_dir='examples/output/comprehensive',
        export_format='json',
        extract_images=True,
        extract_links=True,
        deduplicate=True,
        verbose=True,
        delay=1.0,
        max_concurrent=8,
        timeout=20
    )
    
    crawler = WebCrawler(config)
    summary = await crawler.crawl()
    
    print(f"✅ Comprehensive crawl: {summary['stats']['pages_crawled']} pages")
    print(f"   Found {len(crawler.results[0].images) if crawler.results else 0} images in first page")
    return summary

async def main():
    """Run all examples."""
    print("🚀 SimpleCrawler MK4 - Usage Examples\n")
    
    # Create output directories
    Path('examples/output').mkdir(parents=True, exist_ok=True)
    
    examples = [
        ("Basic Crawl", basic_crawl_example),
        ("Documentation Site", documentation_crawl_example), 
        ("Fast Shallow", fast_shallow_crawl),
        ("Comprehensive", comprehensive_crawl)
    ]
    
    results = {}
    
    for name, example_func in examples:
        try:
            print(f"\n{'='*50}")
            result = await example_func()
            results[name] = result
            print(f"✅ {name} completed successfully")
            
            # Wait between examples to be respectful
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            results[name] = None
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 Examples Summary")
    print(f"{'='*50}")
    
    total_pages = 0
    successful = 0
    
    for name, result in results.items():
        if result:
            successful += 1
            pages = result['stats']['pages_crawled']
            total_pages += pages
            time_taken = result['stats']['total_time']
            print(f"✅ {name:<20} | {pages:>3} pages | {time_taken:>6.2f}s")
        else:
            print(f"❌ {name:<20} | FAILED")
    
    print(f"\n🏆 Results: {successful}/{len(examples)} examples successful")
    print(f"📄 Total pages crawled: {total_pages}")
    print(f"💾 Output saved to examples/output/")

if __name__ == "__main__":
    asyncio.run(main())