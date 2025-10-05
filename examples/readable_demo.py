#!/usr/bin/env python3
"""
Demonstrate the new readable formats with side-by-side comparison.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))
from app import CrawlConfig, WebCrawler

async def demo_format_comparison():
    """Demo all formats with the same content for comparison."""
    
    print("🎨 Format Comparison Demo")
    print("=" * 50)
    
    # Use a smaller documentation site for quick demo
    test_url = "https://rich.readthedocs.io/en/stable/"
    
    formats = [
        ('json', 'Structured data for APIs/processing'),
        ('markdown', 'Standard markdown for documentation'),
        ('readable', 'Human-friendly text for LLMs'),
        ('summary', 'Executive summary with analysis')
    ]
    
    for fmt, description in formats:
        print(f"\n🔄 Generating {fmt} format...")
        print(f"   {description}")
        
        config = CrawlConfig(
            start_url=test_url,
            max_pages=2,
            max_depth=1,
            same_domain=True,
            output_dir=f'format_demo/{fmt}',
            export_format=fmt,
            verbose=False,
            delay=0.5
        )
        
        crawler = WebCrawler(config)
        summary = await crawler.crawl()
        
        print(f"   ✅ Generated: {summary['stats']['pages_crawled']} pages")
        
        await asyncio.sleep(1)  # Be respectful
    
    return formats

def show_format_examples():
    """Show examples from each format."""
    
    print("\n📋 Format Examples")
    print("=" * 50)
    
    base_dir = Path('format_demo')
    
    examples = [
        ('json/crawl_results.json', 'JSON Format', 'json', 300),
        ('markdown/*.md', 'Markdown Format', 'text', 400),
        ('readable/crawl_content_readable.txt', 'Readable Format', 'text', 500),
        ('summary/crawl_summary.md', 'Summary Format', 'text', 400)
    ]
    
    for file_pattern, title, file_type, preview_length in examples:
        print(f"\n📄 {title}")
        print("-" * 30)
        
        if '*' in file_pattern:
            # Find files with wildcard
            pattern_parts = file_pattern.split('*')
            matching_files = list(base_dir.glob(file_pattern))
            
            if matching_files:
                file_path = matching_files[0]
            else:
                print("   ❌ No files found")
                continue
        else:
            file_path = base_dir / file_pattern
        
        if file_path.exists():
            try:
                content = file_path.read_text(encoding='utf-8')
                
                if file_type == 'json':
                    # Show formatted JSON structure
                    import json
                    try:
                        data = json.loads(content)
                        if isinstance(data, list) and len(data) > 0:
                            first_page = data[0]
                            print(f"   📊 Structure: {len(data)} pages")
                            print(f"   🏷️  Sample fields: {', '.join(list(first_page.keys())[:5])}")
                            print(f"   📝 Sample title: {first_page.get('title', 'N/A')}")
                            print(f"   📏 Content length: {len(first_page.get('content', ''))}")
                    except json.JSONDecodeError:
                        print("   ❌ Invalid JSON")
                
                else:
                    # Show text preview
                    lines = content.split('\n')[:10]  # First 10 lines
                    preview = '\n'.join(lines)
                    
                    if len(preview) > preview_length:
                        preview = preview[:preview_length] + "..."
                    
                    print(f"   Preview:")
                    for line in preview.split('\n')[:8]:  # Show up to 8 lines
                        if line.strip():
                            print(f"   │ {line[:80]}")
                
                # Show file stats
                size = file_path.stat().st_size
                print(f"   📊 File size: {size:,} bytes")
                
            except Exception as e:
                print(f"   ❌ Error reading file: {e}")
        else:
            print("   ❌ File not found")

async def main():
    """Run the demo."""
    print("🚀 SimpleCrawler MK4 - Readable Formats Demo")
    print("Comparing output formats for human and LLM readability")
    
    # Create demo directory
    Path('format_demo').mkdir(exist_ok=True)
    
    try:
        # Generate all formats
        formats = await demo_format_comparison()
        
        # Show examples
        show_format_examples()
        
        # Final recommendations
        print("\n💡 Format Recommendations")
        print("=" * 50)
        print("📊 JSON       → APIs, data processing, machine readable")
        print("📝 Markdown   → Documentation, GitHub, human readable") 
        print("📖 Readable   → LLM consumption, analysis, reports")
        print("📋 Summary    → Executive overview, quick insights")
        
        print("\n🎯 For LLM/AI Use Cases:")
        print("  • Use 'readable' for full content analysis")
        print("  • Use 'summary' for quick site overview")
        print("  • Use 'json' for structured data processing")
        
        print(f"\n📁 Demo files generated in: format_demo/")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())