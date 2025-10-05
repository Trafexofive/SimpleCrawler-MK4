#!/usr/bin/env python3
"""
Test code extraction capabilities with real documentation sites.
Focus on proper markdown code block formatting.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'app'))
from app import CrawlConfig, WebCrawler

# Documentation sites known for having lots of code examples
CODE_HEAVY_SITES = {
    # Python documentation with code examples
    'python_requests': 'https://requests.readthedocs.io/en/latest/user/quickstart/',
    'fastapi_tutorial': 'https://fastapi.tiangolo.com/tutorial/',
    'django_tutorial': 'https://docs.djangoproject.com/en/stable/intro/tutorial01/',
    'flask_quickstart': 'https://flask.palletsprojects.com/en/latest/quickstart/',
    
    # JavaScript frameworks with code examples  
    'react_tutorial': 'https://react.dev/learn/tutorial-tic-tac-toe',
    'vue_guide': 'https://vuejs.org/guide/essentials/reactivity-fundamentals.html',
    'nextjs_docs': 'https://nextjs.org/docs/app/building-your-application/routing',
    
    # API documentation with code samples
    'stripe_docs': 'https://stripe.com/docs/api/charges/create',
    'github_api': 'https://docs.github.com/en/rest/repos/repos',
    
    # Developer tools with CLI examples
    'docker_docs': 'https://docs.docker.com/get-started/',
    'git_docs': 'https://git-scm.com/docs/git-commit',
    
    # Programming language docs
    'rust_book': 'https://doc.rust-lang.org/book/ch01-02-hello-world.html',
    'go_tour': 'https://go.dev/tour/basics/1',
}

async def test_code_extraction(site_name: str, url: str, max_pages: int = 3):
    """Test code extraction for a specific site."""
    print(f"\n🔍 Testing {site_name}: {url}")
    
    config = CrawlConfig(
        start_url=url,
        max_pages=max_pages,
        max_depth=1,  # Focus on content, not deep crawling
        same_domain=True,
        output_dir=f'code_test_output/{site_name}',
        export_format='markdown',  # Test markdown code formatting
        verbose=False,
        delay=1.0,
        timeout=20
    )
    
    try:
        crawler = WebCrawler(config)
        summary = await crawler.crawl()
        
        # Check if any markdown files were created
        output_dir = Path(f'code_test_output/{site_name}')
        md_files = list(output_dir.glob('*.md'))
        
        if md_files:
            # Analyze the first markdown file for code blocks
            first_file = md_files[0]
            content = first_file.read_text(encoding='utf-8')
            
            # Count code blocks
            code_blocks = content.count('```')
            inline_code = content.count('`') - (code_blocks * 6)  # Subtract ``` markers
            
            print(f"  ✅ {site_name}: {summary['stats']['pages_crawled']} pages")
            print(f"     📄 Generated: {len(md_files)} markdown files")
            print(f"     💻 Code blocks: {code_blocks // 2} (``` pairs)")
            print(f"     📝 Inline code: {inline_code // 2} segments")
            
            # Show sample code block if found
            if '```' in content:
                lines = content.split('\n')
                in_code_block = False
                code_sample = []
                for line in lines:
                    if line.strip().startswith('```') and not in_code_block:
                        in_code_block = True
                        code_sample.append(line)
                    elif line.strip().startswith('```') and in_code_block:
                        code_sample.append(line)
                        break
                    elif in_code_block:
                        code_sample.append(line)
                
                if code_sample:
                    print(f"     🔍 Sample code block:")
                    for line in code_sample[:5]:  # Show first 5 lines
                        print(f"         {line}")
                    if len(code_sample) > 5:
                        print(f"         ... ({len(code_sample) - 5} more lines)")
            
            return {
                'success': True,
                'pages': summary['stats']['pages_crawled'],
                'files': len(md_files),
                'code_blocks': code_blocks // 2,
                'inline_code': inline_code // 2,
                'sample_file': first_file
            }
        else:
            print(f"  ❌ {site_name}: No markdown files generated")
            return {'success': False}
    
    except Exception as e:
        print(f"  ❌ {site_name}: Failed - {str(e)}")
        return {'success': False}

async def test_readable_format_with_code(site_name: str, url: str):
    """Test the readable format with code preservation."""
    print(f"\n📖 Testing readable format for {site_name}")
    
    config = CrawlConfig(
        start_url=url,
        max_pages=2,
        max_depth=1,
        same_domain=True,
        output_dir=f'code_test_output/{site_name}_readable',
        export_format='readable',
        verbose=False,
        delay=1.0
    )
    
    try:
        crawler = WebCrawler(config)
        summary = await crawler.crawl()
        
        # Check readable output
        readable_file = Path(f'code_test_output/{site_name}_readable/crawl_content_readable.txt')
        if readable_file.exists():
            content = readable_file.read_text(encoding='utf-8')
            code_blocks = content.count('```')
            
            print(f"  ✅ Readable format: {code_blocks // 2} code blocks preserved")
            
            # Show a sample
            if '```' in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if '```' in line:
                        print(f"     🔍 Code sample around line {i+1}:")
                        start = max(0, i-1)
                        end = min(len(lines), i+8)
                        for j in range(start, end):
                            prefix = "  →  " if j == i else "     "
                            print(f"{prefix}{lines[j]}")
                        break
            
            return {'success': True, 'code_blocks': code_blocks // 2}
        
    except Exception as e:
        print(f"  ❌ Readable format failed: {e}")
        return {'success': False}

async def validate_markdown_syntax(file_path: Path):
    """Validate that markdown code blocks are properly formatted."""
    if not file_path.exists():
        return False, "File not found"
    
    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        issues = []
        code_block_stack = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for code block markers
            if stripped.startswith('```'):
                if code_block_stack:
                    # Closing a code block
                    if stripped == '```':
                        code_block_stack.pop()
                    else:
                        issues.append(f"Line {i}: Closing code block with language specified")
                else:
                    # Opening a code block
                    code_block_stack.append(i)
            
            # Check for unmatched backticks
            backtick_count = line.count('`')
            if backtick_count % 2 != 0:
                # Odd number of backticks - might be an issue
                if not any(line.count(marker) for marker in ['```']):
                    issues.append(f"Line {i}: Unmatched backticks")
        
        # Check for unclosed code blocks
        if code_block_stack:
            issues.append(f"Unclosed code blocks starting at lines: {code_block_stack}")
        
        return len(issues) == 0, issues
    
    except Exception as e:
        return False, [f"Error reading file: {e}"]

async def comprehensive_code_test():
    """Run comprehensive code extraction tests."""
    print("🚀 SimpleCrawler MK4 - Code Extraction Testing")
    print("=" * 60)
    
    # Create output directory
    Path('code_test_output').mkdir(exist_ok=True)
    
    results = {}
    
    # Test a selection of code-heavy sites
    test_sites = {
        'fastapi_tutorial': 'https://fastapi.tiangolo.com/tutorial/',
        'requests_quickstart': 'https://requests.readthedocs.io/en/latest/user/quickstart/',
        'flask_quickstart': 'https://flask.palletsprojects.com/en/latest/quickstart/',
        'react_tutorial': 'https://react.dev/learn/tutorial-tic-tac-toe',
    }
    
    print(f"\n📋 Testing {len(test_sites)} documentation sites...")
    
    for site_name, url in test_sites.items():
        result = await test_code_extraction(site_name, url, max_pages=2)
        results[site_name] = result
        
        if result.get('success'):
            # Also test readable format
            await test_readable_format_with_code(site_name, url)
            
            # Validate markdown syntax
            sample_file = result.get('sample_file')
            if sample_file:
                is_valid, issues = await validate_markdown_syntax(sample_file)
                if is_valid:
                    print(f"     ✅ Markdown syntax is valid")
                else:
                    print(f"     ⚠️  Markdown issues: {len(issues)}")
                    for issue in issues[:3]:  # Show first 3 issues
                        print(f"         - {issue}")
        
        # Small delay between sites
        await asyncio.sleep(2)
    
    # Summary
    print(f"\n📊 Code Extraction Test Results")
    print("=" * 40)
    
    successful = sum(1 for r in results.values() if r.get('success'))
    total_pages = sum(r.get('pages', 0) for r in results.values())
    total_code_blocks = sum(r.get('code_blocks', 0) for r in results.values())
    
    print(f"✅ Successful sites: {successful}/{len(test_sites)}")
    print(f"📄 Total pages crawled: {total_pages}")
    print(f"💻 Total code blocks extracted: {total_code_blocks}")
    
    for site_name, result in results.items():
        if result.get('success'):
            print(f"  {site_name}: {result['code_blocks']} code blocks from {result['pages']} pages")
        else:
            print(f"  {site_name}: ❌ Failed")
    
    return results

async def demo_code_extraction():
    """Quick demo of code extraction with a single site."""
    print("\n🎯 Quick Code Extraction Demo")
    print("-" * 30)
    
    # Use FastAPI docs as they have lots of code examples
    url = 'https://fastapi.tiangolo.com/tutorial/first-steps/'
    
    config = CrawlConfig(
        start_url=url,
        max_pages=1,
        max_depth=0,
        output_dir='demo_code_extraction',
        export_format='markdown',
        verbose=True
    )
    
    crawler = WebCrawler(config)
    summary = await crawler.crawl()
    
    # Show the extracted content
    output_dir = Path('demo_code_extraction')
    md_files = list(output_dir.glob('*.md'))
    
    if md_files:
        content = md_files[0].read_text(encoding='utf-8')
        
        print(f"\n📄 Extracted content preview:")
        print("-" * 40)
        
        lines = content.split('\n')
        for i, line in enumerate(lines[:50]):  # Show first 50 lines
            if line.strip().startswith('```'):
                print(f"{Fore.CYAN}{line}{Style.RESET_ALL}")
            elif '`' in line and not line.strip().startswith('#'):
                print(f"{Fore.YELLOW}{line}{Style.RESET_ALL}")
            else:
                print(line)
        
        if len(lines) > 50:
            print(f"\n... ({len(lines) - 50} more lines)")
        
        # Count code blocks
        code_blocks = content.count('```') // 2
        inline_code = (content.count('`') - content.count('```') * 3) // 2
        
        print(f"\n📊 Code extraction results:")
        print(f"  💻 Code blocks: {code_blocks}")
        print(f"  📝 Inline code segments: {inline_code}")
    
    return summary

if __name__ == "__main__":
    import sys
    
    # Add colorama for better output (optional)
    try:
        from colorama import Fore, Style, init
        init(autoreset=True)
    except ImportError:
        # Fallback if colorama not available
        class Fore:
            CYAN = ""
            YELLOW = ""
        class Style:
            RESET_ALL = ""
    
    if len(sys.argv) > 1 and sys.argv[1] == 'demo':
        # Quick demo
        asyncio.run(demo_code_extraction())
    else:
        # Full test suite
        asyncio.run(comprehensive_code_test())