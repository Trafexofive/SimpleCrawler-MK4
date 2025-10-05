#!/usr/bin/env python3
"""
Test the new readable formats for SimpleCrawler MK4.
Demonstrates human and LLM-friendly output formats.
"""

import asyncio
import sys
from pathlib import Path

# Add app to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'app'))

from app import CrawlConfig, WebCrawler

async def test_readable_format():
    """Test the readable text format."""
    print("📖 Testing Readable Format")
    
    config = CrawlConfig(
        start_url='https://fastapi.tiangolo.com/',
        max_pages=5,
        max_depth=2,
        same_domain=True,
        output_dir='readable_output/fastapi_readable',
        export_format='readable',  # New format!
        verbose=True,
        delay=1.0
    )
    
    crawler = WebCrawler(config)
    summary = await crawler.crawl()
    
    print(f"✅ Readable format: {summary['stats']['pages_crawled']} pages")
    return summary

async def test_summary_format():
    """Test the executive summary format."""
    print("📋 Testing Summary Format")
    
    config = CrawlConfig(
        start_url='https://requests.readthedocs.io/en/latest/',
        max_pages=8,
        max_depth=2,
        same_domain=True,
        output_dir='readable_output/requests_summary',
        export_format='summary',  # New format!
        verbose=True,
        delay=1.0
    )
    
    crawler = WebCrawler(config)
    summary = await crawler.crawl()
    
    print(f"✅ Summary format: {summary['stats']['pages_crawled']} pages")
    return summary

async def test_enhanced_markdown():
    """Test enhanced markdown with better formatting."""
    print("📝 Testing Enhanced Markdown")
    
    config = CrawlConfig(
        start_url='https://rich.readthedocs.io/en/stable/',
        max_pages=4,
        max_depth=1,
        same_domain=True,
        output_dir='readable_output/rich_markdown',
        export_format='markdown',
        verbose=True,
        delay=1.0
    )
    
    crawler = WebCrawler(config)
    summary = await crawler.crawl()
    
    print(f"✅ Enhanced markdown: {summary['stats']['pages_crawled']} pages")
    return summary

async def demo_all_formats():
    """Demonstrate all output formats with same content."""
    print("🎨 All Formats Demo - Same Site, Different Outputs")
    
    base_url = 'https://docs.python.org/3/library/asyncio.html'
    
    formats = ['markdown', 'json', 'readable', 'summary']
    
    results = {}
    
    for fmt in formats:
        print(f"\n🔄 Testing {fmt} format...")
        
        config = CrawlConfig(
            start_url=base_url,
            max_pages=3,
            max_depth=1,
            same_domain=True,
            output_dir=f'readable_output/python_docs_{fmt}',
            export_format=fmt,
            verbose=False,  # Quiet for demo
            delay=0.8
        )
        
        crawler = WebCrawler(config)
        summary = await crawler.crawl()
        results[fmt] = summary
        
        print(f"   ✅ {fmt}: {summary['stats']['pages_crawled']} pages in {summary['stats']['total_time']:.2f}s")
        
        # Small delay between formats
        await asyncio.sleep(1)
    
    return results

def show_file_previews():
    """Show previews of generated files."""
    print("\n📄 File Previews:")
    print("=" * 60)
    
    # Find generated files
    output_dir = Path('readable_output')
    
    if not output_dir.exists():
        print("❌ No output directory found")
        return
    
    file_types = [
        ('crawl_content_readable.txt', 'Readable Format'),
        ('crawl_summary.md', 'Executive Summary'),
        ('*.md', 'Markdown Files'),
        ('crawl_results.json', 'JSON Data')
    ]
    
    for pattern, description in file_types:
        print(f"\n📁 {description}:")
        print("-" * 30)
        
        if pattern == '*.md':
            # Find markdown files
            md_files = list(output_dir.rglob('*.md'))
            for md_file in md_files[:3]:  # Show first 3
                print(f"   📄 {md_file.relative_to(output_dir)}")
                if md_file.stat().st_size < 5000:  # Show preview of small files
                    try:
                        content = md_file.read_text(encoding='utf-8')[:200]
                        print(f"      Preview: {content[:100]}...")
                    except Exception as e:
                        print(f"      Error reading: {e}")
        else:
            # Find specific files
            matching_files = list(output_dir.rglob(pattern))
            for file_path in matching_files[:2]:  # Show first 2
                print(f"   📄 {file_path.relative_to(output_dir)}")
                size = file_path.stat().st_size
                print(f"      Size: {size:,} bytes")
                
                # Show preview for text files
                if pattern.endswith('.txt') or pattern.endswith('.md'):
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        lines = content.split('\n')[:5]  # First 5 lines
                        preview = '\n'.join(lines)
                        print(f"      Preview:\n{preview}...")
                    except Exception as e:
                        print(f"      Error reading: {e}")

async def main():
    """Run all readable format tests."""
    print("🚀 SimpleCrawler MK4 - Readable Format Testing")
    print("Testing human and LLM-friendly output formats")
    print("=" * 60)
    
    # Create output directory
    Path('readable_output').mkdir(exist_ok=True)
    
    try:
        # Test individual formats
        await test_readable_format()
        await asyncio.sleep(2)
        
        await test_summary_format()
        await asyncio.sleep(2)
        
        await test_enhanced_markdown()
        await asyncio.sleep(2)
        
        # Demo all formats with same content
        results = await demo_all_formats()
        
        # Show file previews
        show_file_previews()
        
        # Final summary
        print("\n🎉 Readable Format Testing Complete!")
        print("=" * 60)
        print("New formats available:")
        print("  📖 readable  - Human-friendly text format")
        print("  📋 summary   - Executive summary with analysis")
        print("  📝 markdown  - Enhanced markdown (existing)")
        print("  📊 json      - Structured data (existing)")
        
        print(f"\n📁 All outputs saved to: readable_output/")
        
        # Show format comparison
        if results:
            print(f"\n📊 Format Performance Comparison:")
            for fmt, result in results.items():
                stats = result['stats']
                print(f"  {fmt:>10}: {stats['pages_crawled']} pages in {stats['total_time']:.2f}s")
    
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())