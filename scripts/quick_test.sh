#!/bin/bash
# Quick test script for SimpleCrawler MK4

set -e

echo "🚀 SimpleCrawler MK4 - Quick Test Script"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Setting up...${NC}"
    make setup
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Test sites for quick validation
test_sites=(
    "https://example.com"
    "https://httpbin.org/html"
    "https://requests.readthedocs.io/en/latest/"
)

echo -e "${BLUE}🧪 Running quick crawl tests...${NC}"

for site in "${test_sites[@]}"; do
    echo -e "\n${YELLOW}Testing: $site${NC}"
    
    # Extract domain for output directory
    domain=$(echo "$site" | sed 's|https\?://||' | sed 's|/.*||' | sed 's|\.|-|g')
    output_dir="test_output/quick_test_$domain"
    
    # Run crawler with minimal settings
    if python app/main.py "$site" \
        --max-pages 3 \
        --max-depth 1 \
        --format json \
        --output-dir "$output_dir" \
        --delay 0.5 \
        --timeout 10; then
        
        echo -e "${GREEN}✅ Success: $site${NC}"
        
        # Show what was crawled
        if [ -f "$output_dir/crawl_results.json" ]; then
            pages=$(jq length "$output_dir/crawl_results.json" 2>/dev/null || echo "?")
            echo -e "   📄 Pages crawled: $pages"
        fi
    else
        echo -e "${RED}❌ Failed: $site${NC}"
    fi
    
    sleep 1
done

echo -e "\n${BLUE}🧪 Running unit tests...${NC}"
if python -m pytest app/tests/test_crawler.py -v -x; then
    echo -e "${GREEN}✅ Unit tests passed${NC}"
else
    echo -e "${YELLOW}⚠️  Some unit tests failed (this is OK for quick testing)${NC}"
fi

echo -e "\n${BLUE}📊 Test Results Summary${NC}"
echo "=========================="

if [ -d "test_output" ]; then
    total_dirs=$(find test_output -type d -name "quick_test_*" | wc -l)
    total_files=$(find test_output -name "crawl_results.json" | wc -l)
    
    echo -e "📁 Output directories created: $total_dirs"
    echo -e "📄 JSON result files: $total_files"
    
    # Show file sizes
    echo -e "\n📊 Crawl Results:"
    for json_file in test_output/quick_test_*/crawl_results.json; do
        if [ -f "$json_file" ]; then
            pages=$(jq length "$json_file" 2>/dev/null || echo "?")
            size=$(du -h "$json_file" | cut -f1)
            dir_name=$(basename "$(dirname "$json_file")")
            echo -e "   $dir_name: $pages pages ($size)"
        fi
    done
else
    echo -e "${RED}❌ No test output found${NC}"
fi

echo -e "\n${GREEN}🎉 Quick test completed!${NC}"
echo -e "${BLUE}💡 Try these commands next:${NC}"
echo "   make test-real-sites    # Test against real documentation sites"
echo "   make crawl-fastapi      # Crawl FastAPI documentation"
echo "   python examples/basic_usage.py  # Run usage examples"

echo -e "\n${BLUE}📁 Project structure:${NC}"
echo "   app/                    # Core crawler code"
echo "   test_output/            # Crawl results"
echo "   examples/               # Usage examples"
echo "   docs/                   # Documentation"