# SimpleCrawler MK4 - Client Libraries

Professional client libraries for SimpleCrawler MK4 microservices platform in multiple languages.

## 🚀 Available Clients

### 🐍 Python Client Library (`clients/python/`)
- **Sync and Async** client implementations
- **Type-safe** with Pydantic models
- **Comprehensive error handling** with custom exceptions
- **CLI interface** for command-line usage
- **Retry logic** with exponential backoff
- **Connection pooling** for performance

```python
from simplecrawler_client import CrawlerClient

# Synchronous usage
client = CrawlerClient("http://localhost:8000")
job = client.crawl("https://example.com", max_pages=10)
results = client.wait_for_completion(job.job_id)

# Async usage
async with AsyncCrawlerClient("http://localhost:8000") as client:
    job = await client.crawl("https://example.com")
    results = await job.wait_for_completion()
```

### ⚡ C++ Client Library (`clients/cpp/`)
- **Modern C++17** implementation
- **CMake build system** with proper packaging
- **HTTP client** with libcurl
- **JSON support** with nlohmann/json
- **Cross-platform** compatibility
- **Unit tests** with Google Test

```cpp
#include <simplecrawler/client.hpp>

SimpleCrawler::Client client("http://localhost:8000");
auto job = client.crawl("https://example.com", 10);
auto results = client.waitForCompletion(job.jobId);
```

### 🖥️ TUI (Terminal User Interface) (`clients/tui/`)
- **Rich Python-based** terminal interface
- **Real-time job monitoring** with live updates
- **Interactive configuration** for crawl parameters
- **Results browsing** and visualization
- **Progress indicators** and statistics

```bash
# Launch TUI
simplecrawler-tui

# Or via Python
python -m simplecrawler_tui
```

## 📦 Installation

### Python Client
```bash
# From PyPI (when published)
pip install simplecrawler-client

# Development installation
cd clients/python
pip install -e .

# With optional dependencies
pip install simplecrawler-client[cli,async,dev]
```

### C++ Client
```bash
# Build from source
cd clients/cpp
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install

# Using vcpkg
vcpkg install simplecrawler-client

# Using Conan
conan install simplecrawler-client/2.0.0@
```

### TUI Client
```bash
# From PyPI (when published)
pip install simplecrawler-tui

# Development installation
cd clients/tui
pip install -e .
```

## 🏗️ Architecture

### Client Architecture
```
┌─────────────────────────────────────────────────┐
│                Client Libraries                 │
├─────────────────┬─────────────────┬─────────────┤
│   Python Client │   C++ Client    │ TUI Client  │
│                 │                 │             │
│ • Sync/Async    │ • Modern C++17  │ • Rich UI   │
│ • Type Safety   │ • CMake Build   │ • Real-time │
│ • CLI Tools     │ • Cross-platform│ • Interactive│
└─────────────────┴─────────────────┴─────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   SimpleCrawler API     │
              │   (FastAPI + Pydantic) │
              └─────────────────────────┘
```

### Common Features
All client libraries provide:

- ✅ **Complete API Coverage** - All endpoints supported
- ✅ **Authentication** - API key and JWT support
- ✅ **Error Handling** - Comprehensive exception hierarchy
- ✅ **Retry Logic** - Automatic retry with backoff
- ✅ **Rate Limiting** - Built-in rate limit handling
- ✅ **Validation** - Request/response validation
- ✅ **Logging** - Configurable logging levels
- ✅ **Testing** - Unit and integration tests

## 🎯 Usage Examples

### Basic Crawling
```python
# Python
client = CrawlerClient("http://localhost:8000")
job = client.crawl("https://fastapi.tiangolo.com", max_pages=20)
print(f"Job ID: {job.job_id}, Status: {job.status}")
```

```cpp
// C++
SimpleCrawler::Client client("http://localhost:8000");
auto job = client.crawl("https://fastapi.tiangolo.com", 20);
std::cout << "Job ID: " << job.jobId << ", Status: " << job.status << std::endl;
```

### Advanced Configuration
```python
# Python - Advanced crawl configuration
job = client.crawl(
    start_url="https://docs.python.org/3/",
    max_pages=50,
    max_depth=3,
    export_format="readable",
    same_domain=True,
    delay=0.5,
    extract_images=True
)
```

### Real-time Monitoring
```python
# Python - Monitor job progress
job = client.crawl("https://example.com", max_pages=100)

while not job.is_completed:
    time.sleep(2)
    job = client.get_job(job.job_id)
    print(f"Progress: {job.progress}% - {job.pages_crawled} pages")

results = client.get_results(job.job_id)
print(f"Completed! Crawled {len(results.pages)} pages")
```

### Batch Operations
```python
# Python - Batch job management
jobs = []
urls = ["https://site1.com", "https://site2.com", "https://site3.com"]

# Start multiple jobs
for url in urls:
    job = client.crawl(url, max_pages=10)
    jobs.append(job)

# Wait for all to complete
for job in jobs:
    result = client.wait_for_completion(job.job_id)
    print(f"Job {job.job_id}: {len(result.pages)} pages crawled")
```

## 🔧 Development

### Building from Source

#### Python Client
```bash
cd clients/python
python -m pip install -e .[dev]
pytest tests/
black src/
isort src/
```

#### C++ Client
```bash
cd clients/cpp
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTS=ON ..
make -j$(nproc)
ctest --output-on-failure
```

#### TUI Client
```bash
cd clients/tui
python -m pip install -e .[dev]
pytest tests/
python -m simplecrawler_tui --help
```

### Testing
Each client includes comprehensive tests:

- **Unit tests** for individual components
- **Integration tests** against live API
- **Mock tests** for offline development
- **Performance tests** for benchmarking

```bash
# Python
pytest clients/python/tests/ -v --cov

# C++
cd clients/cpp/build && ctest --verbose

# TUI
pytest clients/tui/tests/ -v
```

## 📚 Documentation

### API Documentation
- **Python**: Auto-generated from docstrings
- **C++**: Doxygen documentation
- **TUI**: Interactive help system

### Examples
Each client includes comprehensive examples:
- Basic usage patterns
- Advanced configuration
- Error handling
- Performance optimization
- Integration patterns

### Integration Guides
- Framework integration (Django, Flask, Express)
- CI/CD pipeline usage
- Docker container integration
- Kubernetes deployment

## 🤝 Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

### Client-Specific Guidelines
- **Python**: Follow PEP 8, use Black formatter
- **C++**: Follow Google C++ Style Guide
- **TUI**: Follow Rich/Textual best practices

## 📄 License

MIT License - see [LICENSE](../LICENSE) for details.