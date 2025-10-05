# SimpleCrawler MK4 🚀

A production-ready microservices web crawling platform built with FastAPI, PostgreSQL, Redis, and Docker. Transform any documentation site into structured, LLM-friendly data.

## 🏗️ Architecture

**Enterprise Microservices Platform:**
- 🚀 **FastAPI API Service** - REST API with Pydantic validation
- ⚙️ **Background Workers** - Scalable async job processing
- 🗄️ **PostgreSQL Database** - Job persistence with ACID transactions
- 🚀 **Redis Queue** - Job queue and caching layer
- 🌐 **Nginx Proxy** - Load balancing with rate limiting

## 🌟 Features

- **Production Microservices**: Docker containers, health checks, scaling
- **Type-Safe APIs**: FastAPI + Pydantic validation
- **Async Processing**: Background job queue with Redis
- **Smart Content Extraction**: Code blocks, markdown, readable formats
- **Multiple Export Formats**: JSON, Markdown, **Human-Readable**, **Executive Summary**
- **Enterprise Database**: PostgreSQL with connection pooling
- **Zero Host Pollution**: Everything runs in containers

## 🔥 Validated Against Real Sites

Successfully tested against:

### Python Ecosystem
- ✅ **Python Official Docs** (docs.python.org)
- ✅ **FastAPI** (fastapi.tiangolo.com)
- ✅ **Django** (docs.djangoproject.com)
- ✅ **Flask** (flask.palletsprojects.com)
- ✅ **Requests** (requests.readthedocs.io)
- ✅ **NumPy** (numpy.org/doc)

### JavaScript Frameworks
- ✅ **React** (react.dev)
- ✅ **Vue.js** (vuejs.org)
- ✅ **Svelte** (svelte.dev)

### Documentation & Static Sites
- ✅ **Bootstrap** (getbootstrap.com)
- ✅ **Tailwind CSS** (tailwindcss.com)
- ✅ **GitHub Docs** (docs.github.com)
- ✅ **Rich** (rich.readthedocs.io)
- ✅ **Pytest** (docs.pytest.org)

## 🚀 Quick Start

```bash
# Start the entire platform (builds everything)
make quick-start

# Check services health
make health

# Monitor all services
make logs

# Scale background workers
make scale-workers WORKERS=5

# Access API documentation
open http://localhost:8000/docs
```

### Using the API

```bash
# Start a crawl job
curl -X POST "http://localhost:8000/crawl" \
  -H "Content-Type: application/json" \
  -d '{"start_url": "https://fastapi.tiangolo.com", "max_pages": 10, "export_format": "readable"}'

# List jobs
curl "http://localhost:8000/jobs"

# Download results
curl "http://localhost:8000/download/{job_id}/{filename}"
```

## 📁 Project Structure

```
SimpleCrawler-MK4/
├── services/                    # Microservices
│   ├── api/                    # FastAPI REST API
│   │   ├── main.py            # API service
│   │   ├── Dockerfile         # API container
│   │   └── requirements.txt   # API dependencies
│   └── worker/                # Background workers
│       ├── worker.py          # Worker service
│       ├── Dockerfile         # Worker container
│       └── requirements.txt   # Worker dependencies
├── app/                       # Core crawler engine
│   ├── main.py               # Crawler implementation
│   └── tests/                # Unit tests
├── docs/                     # Documentation
├── examples/                 # Usage examples
├── docker-compose.yml        # Service orchestration
├── nginx.conf               # Reverse proxy config
└── Makefile                 # Operations toolkit
```

## 🛠 Installation

**Prerequisites:** Docker and Docker Compose

```bash
# Clone repository
git clone https://github.com/yourusername/SimpleCrawler-MK4.git
cd SimpleCrawler-MK4

# Start all services (builds containers automatically)
make quick-start

# Verify installation
make health
make status
```

**No Python setup required** - everything runs in containers!

## 💡 Usage

### Basic Crawling

```bash
# Activate virtual environment
source venv/bin/activate

# Basic crawl
python app/main.py https://example.com

# Advanced options
python app/main.py https://fastapi.tiangolo.com/ \
    --max-pages 20 \
    --max-depth 3 \
    --single-domain \
    --format json \
    --verbose
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--max-pages` | Maximum pages to crawl | 100 |
| `--max-depth` | Maximum crawl depth | 3 |
| `--single-domain` | Restrict to same domain | False |
| `--delay` | Delay between requests (seconds) | 1.0 |
| `--concurrency` | Max concurrent requests | 10 |
| `--format` | Export format (markdown/json/csv) | markdown |
| `--output-dir` | Output directory | crawled_pages |
| `--verbose` | Verbose logging | False |

## 🧪 Testing

```bash
# Run unit tests
make test-unit

# Test with real documentation sites
make test-real-sites

# Run specific tests
python -m pytest app/tests/test_crawler.py -v
```

## 📊 Performance Results

Recent test results from real documentation sites:

```
🏆 OVERALL RESULTS:
   Tests: 14/14 successful (100.0%)
   Pages crawled: 31
   Total time: 28.36s
   Average speed: 1.09 pages/second
```

### Detailed Results by Category

| Category | Sites Tested | Success Rate | Avg Speed |
|----------|-------------|-------------|-----------|
| Python Ecosystem | 6 sites | 100% | 1.1 pages/s |
| JS Frameworks | 3 sites | 100% | 1.2 pages/s |
| Documentation | 5 sites | 100% | 1.0 pages/s |

## 🔧 Development

### Available Make Commands

```bash
make help                 # Show all available commands
make setup               # Setup development environment
make test                # Run all tests
make test-real-sites     # Test against real documentation sites
make lint                # Run code linting
make format              # Format code with black
make clean               # Clean up generated files
make crawl-example       # Demo crawl of example.com
```

### Project Components

- **WebCrawler**: Main crawler class with async worker pool
- **RateLimiter**: Smart rate limiting with domain-specific delays
- **ContentExtractor**: Advanced content extraction using multiple strategies
- **RobotsCache**: Robots.txt compliance and caching
- **PageData**: Structured data model for crawled pages

## 📈 Features in Detail

### Smart Rate Limiting
- Domain-specific delays
- Exponential backoff on errors
- Automatic recovery after successful requests

### Content Extraction
- Primary: Trafilatura for article extraction
- Fallback: BeautifulSoup with smart content detection
- Metadata extraction (title, description, keywords)
- Link and image URL extraction

### Export Formats
- **Markdown**: Clean, readable format with metadata headers
- **JSON**: Structured data for programmatic use
- **CSV**: Spreadsheet-compatible format

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Format code: `make format`
6. Submit a pull request

## 📝 License

[MIT License](LICENSE)

## 🙏 Acknowledgments

Built with:
- [aiohttp](https://aiohttp.readthedocs.io/) - Async HTTP client/server
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Trafilatura](https://trafilatura.readthedocs.io/) - Content extraction
- [pytest](https://docs.pytest.org/) - Testing framework

---

**SimpleCrawler MK4** - *Fast, reliable, respectful web crawling* 🕷️