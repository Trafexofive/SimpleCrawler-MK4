#!/usr/bin/env python3
"""
Test script for crawling real documentation sites.
Tests various types of sites: JS frameworks, Python libs, GitHub pages, etc.
"""

import asyncio
import sys
from pathlib import Path

# Add app to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'app'))

from app import CrawlConfig, WebCrawler

# Test URLs - various documentation sites
TEST_SITES = {
    # Python Documentation
    'python_asyncio': 'https://docs.python.org/3/library/asyncio.html',
    'requests_docs': 'https://requests.readthedocs.io/en/latest/',
    'django_docs': 'https://docs.djangoproject.com/en/stable/',
    'flask_docs': 'https://flask.palletsprojects.com/en/latest/',
    
    # JavaScript Frameworks
    'react_docs': 'https://react.dev/learn',
    'vue_docs': 'https://vuejs.org/guide/',
    'nextjs_docs': 'https://nextjs.org/docs',
    'svelte_docs': 'https://svelte.dev/docs',
    
    # GitHub Pages / Static Sites
    'bootstrap_docs': 'https://getbootstrap.com/docs/',
    'tailwind_docs': 'https://tailwindcss.com/docs',
    'github_docs': 'https://docs.github.com/en',
    'netlify_docs': 'https://docs.netlify.com/',
    
    # Developer Tools
    'vscode_docs': 'https://code.visualstudio.com/docs',
    'webpack_docs': 'https://webpack.js.org/concepts/',
    'docker_docs': 'https://docs.docker.com/get-started/',
    'kubernetes_docs': 'https://kubernetes.io/docs/concepts/',
    
    # Popular Libraries
    'numpy_docs': 'https://numpy.org/doc/stable/',
    'pandas_docs': 'https://pandas.pydata.org/docs/',
    'matplotlib_docs': 'https://matplotlib.org/stable/contents.html',
    'fastapi_docs': 'https://fastapi.tiangolo.com/',
    
    # Cloud Providers
    'aws_docs': 'https://docs.aws.amazon.com/getting-started/',
    'gcp_docs': 'https://cloud.google.com/docs',
    'azure_docs': 'https://docs.microsoft.com/en-us/azure/',
    
    # Databases
    'postgres_docs': 'https://www.postgresql.org/docs/current/',
    'mongodb_docs': 'https://docs.mongodb.com/',
    'redis_docs': 'https://redis.io/docs/'
}

async def test_single_site(name: str, url: str, max_pages: int = 5, max_depth: int = 2):
    """Test crawling a single site."""
    print(f"\n🔍 Testing {name}: {url}")
    
    config = CrawlConfig(
        start_url=url,
        max_pages=max_pages,
        max_depth=max_depth,
        same_domain=True,
        output_dir=f'test_output/{name}',
        verbose=True,
        delay=1.0,  # Be respectful
        max_concurrent=3,  # Conservative
        export_format='json',
        extract_images=False,  # Speed up testing
        deduplicate=True,
        timeout=15  # Shorter timeout for testing
    )
    
    try:
        crawler = WebCrawler(config)
        summary = await crawler.crawl()
        
        print(f"✅ {name}: Crawled {summary['stats']['pages_crawled']} pages in {summary['stats']['total_time']:.2f}s")
        print(f"   Found {summary['stats']['urls_discovered']} URLs, {summary['stats']['errors']} errors")
        
        return True, summary
        
    except Exception as e:
        print(f"❌ {name}: Failed - {str(e)}")
        return False, None

async def test_lightweight_sites():
    """Test a selection of lightweight, fast sites first."""
    lightweight_sites = {
        'fastapi_docs': 'https://fastapi.tiangolo.com/',
        'flask_docs': 'https://flask.palletsprojects.com/en/latest/',
        'requests_docs': 'https://requests.readthedocs.io/en/latest/',
        'rich_docs': 'https://rich.readthedocs.io/en/stable/',
        'pytest_docs': 'https://docs.pytest.org/en/stable/'
    }
    
    print("🚀 Testing lightweight documentation sites...")
    
    results = {}
    for name, url in lightweight_sites.items():
        success, summary = await test_single_site(name, url, max_pages=3, max_depth=1)
        results[name] = {'success': success, 'summary': summary}
        
        # Small delay between sites
        await asyncio.sleep(2)
    
    return results

async def test_framework_sites():
    """Test JavaScript framework documentation."""
    framework_sites = {
        'react_docs': 'https://react.dev/learn',
        'vue_docs': 'https://vuejs.org/guide/',
        'svelte_docs': 'https://svelte.dev/docs'
    }
    
    print("⚡ Testing JavaScript framework sites...")
    
    results = {}
    for name, url in framework_sites.items():
        success, summary = await test_single_site(name, url, max_pages=5, max_depth=2)
        results[name] = {'success': success, 'summary': summary}
        
        await asyncio.sleep(2)
    
    return results

async def test_github_pages():
    """Test GitHub Pages and static sites."""
    github_sites = {
        'bootstrap_docs': 'https://getbootstrap.com/docs/',
        'tailwind_docs': 'https://tailwindcss.com/docs',
        'github_docs': 'https://docs.github.com/en'
    }
    
    print("📚 Testing GitHub Pages and static sites...")
    
    results = {}
    for name, url in github_sites.items():
        success, summary = await test_single_site(name, url, max_pages=4, max_depth=1)
        results[name] = {'success': success, 'summary': summary}
        
        await asyncio.sleep(2)
    
    return results

async def test_python_ecosystem():
    """Test Python ecosystem documentation."""
    python_sites = {
        'python_asyncio': 'https://docs.python.org/3/library/asyncio.html',
        'django_docs': 'https://docs.djangoproject.com/en/stable/',
        'numpy_docs': 'https://numpy.org/doc/stable/',
    }
    
    print("🐍 Testing Python ecosystem sites...")
    
    results = {}
    for name, url in python_sites.items():
        success, summary = await test_single_site(name, url, max_pages=6, max_depth=2)
        results[name] = {'success': success, 'summary': summary}
        
        await asyncio.sleep(2)
    
    return results

def print_summary(all_results):
    """Print a comprehensive summary of all tests."""
    print("\n" + "="*80)
    print("🎯 CRAWLING TEST SUMMARY")
    print("="*80)
    
    total_tests = 0
    successful_tests = 0
    total_pages = 0
    total_time = 0
    
    for category, results in all_results.items():
        print(f"\n📂 {category.upper().replace('_', ' ')}")
        print("-" * 50)
        
        for name, result in results.items():
            total_tests += 1
            if result['success']:
                successful_tests += 1
                summary = result['summary']
                stats = summary['stats']
                pages = stats['pages_crawled']
                time_taken = stats['total_time']
                total_pages += pages
                total_time += time_taken
                
                print(f"  ✅ {name:<20} | {pages:>3} pages | {time_taken:>6.2f}s | {stats['errors']} errors")
            else:
                print(f"  ❌ {name:<20} | FAILED")
    
    print("\n" + "="*80)
    print(f"🏆 OVERALL RESULTS:")
    print(f"   Tests: {successful_tests}/{total_tests} successful ({successful_tests/total_tests*100:.1f}%)")
    print(f"   Pages crawled: {total_pages}")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average speed: {total_pages/total_time if total_time > 0 else 0:.2f} pages/second")
    print("="*80)

async def main():
    """Run all crawling tests."""
    print("🚀 SimpleCrawler Real-World Testing Suite")
    print("Testing various documentation sites to validate crawler functionality\n")
    
    # Create output directory
    Path('test_output').mkdir(exist_ok=True)
    
    all_results = {}
    
    try:
        # Test different categories of sites
        all_results['lightweight'] = await test_lightweight_sites()
        all_results['frameworks'] = await test_framework_sites()  
        all_results['github_pages'] = await test_github_pages()
        all_results['python_ecosystem'] = await test_python_ecosystem()
        
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    
    finally:
        print_summary(all_results)
    
    return all_results

if __name__ == "__main__":
    asyncio.run(main())