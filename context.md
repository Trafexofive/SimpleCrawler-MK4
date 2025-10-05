# SimpleCrawler MK4 - LLM/Agent Context

## 🎯 Project Overview

**SimpleCrawler MK4** is a production-ready microservices web crawling platform designed specifically for LLM and AI agent integration. It transforms any documentation site, GitHub pages, or web content into structured, LLM-friendly data formats.

## 🏗️ Architecture

### Microservices Platform
```
🌐 Nginx (Reverse Proxy + Load Balancer)
     ↓
🚀 FastAPI API Service (REST API + Pydantic Validation)
     ↓
⚙️  Background Workers (2x Scalable Job Processors) 
     ↓
🗄️  PostgreSQL (Job Persistence + ACID Transactions)
🚀 Redis (Job Queue + Caching)
📁 Shared Volumes (Output File Storage)
```

### Service Components
- **API Service** (`services/api/`): FastAPI + Pydantic for type-safe REST API
- **Worker Service** (`services/worker/`): Background job processing
- **Database Layer**: PostgreSQL 15 with connection pooling
- **Queue Layer**: Redis 7 for job queuing and caching
- **Reverse Proxy**: Nginx with rate limiting and security

## 🎨 LLM-Optimized Output Formats

### 1. **Human-Readable Format** 📖
**Perfect for**: LLM context windows, training data, human review
```markdown
# Page Title
Clear, formatted content with proper headings and structure.

## Key Points
- Bullet points for easy parsing
- Code blocks with syntax highlighting
- Structured information hierarchy
```

### 2. **Executive Summary Format** 📋
**Perfect for**: Agent decision-making, quick overviews, content triage
```markdown
# Executive Summary

**Page**: https://example.com/docs
**Topic**: API Documentation
**Complexity**: Intermediate
**Key Concepts**: REST API, Authentication, Rate Limiting

## Main Points
1. Authentication via API keys
2. Rate limits: 1000 requests/hour
3. JSON response format

## Code Examples Found
- Python client example
- cURL commands
- Response schemas
```

### 3. **Structured JSON Format** 🗂️
**Perfect for**: Agent processing, data pipelines, structured analysis
```json
{
  "url": "https://example.com/docs",
  "title": "API Documentation",
  "metadata": {
    "word_count": 1250,
    "code_blocks": 8,
    "links": 15,
    "reading_time": "5 minutes"
  },
  "content": {
    "sections": [
      {
        "heading": "Authentication",
        "content": "Use API keys for authentication...",
        "code_examples": ["curl -H 'Authorization: Bearer token'"]
      }
    ]
  }
}
```

### 4. **Code-Focused Extraction** 💻
**Perfect for**: Code analysis, documentation generation, programming assistance
```markdown
# Code Examples from https://example.com

## Python Client Usage
```python
import requests

client = APIClient("https://api.example.com")
response = client.get("/users")
```

## Authentication Example  
```javascript
const token = "your-api-key";
const headers = { "Authorization": `Bearer ${token}` };
```

## Response Schema
```json
{
  "users": [
    {"id": 1, "name": "John Doe"}
  ]
}
```
```

## 🤖 Agent Integration Examples

### 1. **Research Agent Integration**
```python
import asyncio
import aiohttp
from typing import List, Dict, Any

class ResearchAgent:
    def __init__(self, crawler_base_url: str = "http://localhost:8000"):
        self.base_url = crawler_base_url
    
    async def research_topic(self, topic: str, sources: List[str]) -> Dict[str, Any]:
        """Crawl multiple sources for comprehensive research"""
        async with aiohttp.ClientSession() as session:
            jobs = []
            
            # Start crawls for all sources
            for source in sources:
                job_data = {
                    "start_url": source,
                    "max_pages": 20,
                    "export_format": "summary",  # Executive summary format
                    "same_domain": True
                }
                
                async with session.post(f"{self.base_url}/crawl", json=job_data) as resp:
                    job = await resp.json()
                    jobs.append(job['job_id'])
            
            # Wait for completion and collect results
            research_data = []
            for job_id in jobs:
                results = await self._wait_for_completion(session, job_id)
                research_data.append(results)
            
            return self._synthesize_research(research_data)
    
    async def _wait_for_completion(self, session, job_id: str):
        """Wait for job completion and return results"""
        while True:
            async with session.get(f"{self.base_url}/jobs/{job_id}") as resp:
                job_status = await resp.json()
                
                if job_status['status'] == 'completed':
                    async with session.get(f"{self.base_url}/jobs/{job_id}/results") as results_resp:
                        return await results_resp.json()
                elif job_status['status'] == 'failed':
                    raise Exception(f"Crawl job {job_id} failed")
                
                await asyncio.sleep(2)  # Check every 2 seconds
```

### 2. **Documentation Agent**
```python
class DocumentationAgent:
    def __init__(self, crawler_base_url: str = "http://localhost:8000"):
        self.base_url = crawler_base_url
    
    async def analyze_api_docs(self, api_docs_url: str) -> Dict[str, Any]:
        """Extract structured API information"""
        async with aiohttp.ClientSession() as session:
            job_data = {
                "start_url": api_docs_url,
                "max_pages": 50,
                "export_format": "json",  # Structured format
                "extract_images": False,
                "extract_links": True,
                "max_depth": 3
            }
            
            # Start crawl
            async with session.post(f"{self.base_url}/crawl", json=job_data) as resp:
                job = await resp.json()
                job_id = job['job_id']
            
            # Wait for completion
            results = await self._wait_for_completion(session, job_id)
            
            # Extract API patterns from results
            api_info = self._extract_api_patterns(results)
            return self._generate_client_code(api_info)
    
    def _extract_api_patterns(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract API endpoints, examples, and schemas from crawl results"""
        api_patterns = {
            "endpoints": [],
            "examples": [],
            "schemas": []
        }
        
        for page in results.get('pages', []):
            content = page.get('content', '')
            
            # Extract API endpoints (simple pattern matching)
            import re
            
            # Find HTTP method patterns
            endpoint_patterns = re.findall(
                r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-\{\}:]+)',
                content, re.IGNORECASE
            )
            
            for method, path in endpoint_patterns:
                api_patterns['endpoints'].append({
                    'method': method.upper(),
                    'path': path,
                    'source_url': page.get('url')
                })
            
            # Find code examples
            code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', content, re.DOTALL)
            for lang, code in code_blocks:
                if lang in ['python', 'javascript', 'curl', 'json']:
                    api_patterns['examples'].append({
                        'language': lang,
                        'code': code.strip(),
                        'source_url': page.get('url')
                    })
        
        return api_patterns
```

### 3. **Learning Agent** 
```python
class LearningAgent:
    def __init__(self, crawler_base_url: str = "http://localhost:8000"):
        self.base_url = crawler_base_url
    
    async def create_study_materials(self, learning_topic: str) -> Dict[str, Any]:
        """Crawl educational content and create study materials"""
        async with aiohttp.ClientSession() as session:
            # Define learning sources
            tutorial_sources = [
                f"https://docs.python.org/3/tutorial/",
                f"https://realpython.com/",
                f"https://www.tutorialspoint.com/python/"
            ]
            
            reference_sources = [
                f"https://docs.python.org/3/reference/",
                f"https://docs.python.org/3/library/"
            ]
            
            # Crawl tutorial sites
            tutorial_jobs = []
            for source in tutorial_sources:
                job_data = {
                    "start_url": source,
                    "max_pages": 30,
                    "export_format": "readable",  # Human-readable for study
                    "same_domain": True
                }
                
                async with session.post(f"{self.base_url}/crawl", json=job_data) as resp:
                    job = await resp.json()
                    tutorial_jobs.append(job['job_id'])
            
            # Crawl reference docs
            reference_jobs = []
            for source in reference_sources:
                job_data = {
                    "start_url": source,
                    "max_pages": 100,
                    "export_format": "summary",   # Executive summaries
                    "same_domain": True
                }
                
                async with session.post(f"{self.base_url}/crawl", json=job_data) as resp:
                    job = await resp.json()
                    reference_jobs.append(job['job_id'])
            
            # Wait for all jobs to complete
            tutorials = []
            for job_id in tutorial_jobs:
                result = await self._wait_for_completion(session, job_id)
                tutorials.append(result)
            
            references = []
            for job_id in reference_jobs:
                result = await self._wait_for_completion(session, job_id)
                references.append(result)
            
            return self._create_structured_curriculum(tutorials, references)
```

## 📊 API Endpoints for Agent Integration

### Core Crawling Endpoints
```http
POST /crawl
{
  "start_url": "https://docs.python.org/3/",
  "max_pages": 50,
  "export_format": "summary",
  "extract_images": false,
  "extract_links": true,
  "same_domain": true,
  "max_depth": 3,
  "delay": 1.0
}
```

### Job Management
```http
GET /jobs/{job_id}           # Get job status
GET /jobs/{job_id}/results   # Get crawl results  
GET /download/{job_id}/{file} # Download result files
DELETE /jobs/{job_id}        # Clean up job
GET /jobs                    # List all jobs
GET /health                  # Service health check
GET /stats                   # API statistics
```

## 🔧 Configuration for LLM Use Cases

### Research Agent Configuration
```python
research_config = {
    "max_pages": 100,
    "max_depth": 4,
    "export_format": "summary",
    "extract_images": False,
    "extract_links": True,
    "same_domain": False,  # Follow external references
    "delay": 0.5,          # Respectful crawling
    "max_concurrent": 10
}
```

### Code Analysis Configuration  
```python
code_config = {
    "max_pages": 200,
    "export_format": "json",
    "extract_images": False,
    "extract_links": True,
    "same_domain": True,
    "delay": 1.0,
    "max_concurrent": 5
}
```

### Training Data Configuration
```python
training_config = {
    "max_pages": 1000,
    "export_format": "readable",
    "extract_images": False,
    "extract_links": False,
    "same_domain": True,
    "delay": 2.0,  # Be extra respectful for large crawls
    "max_concurrent": 3
}
```

## 🚀 Quick Start for Agents

### 1. **Docker Deployment**
```bash
# Clone and start the platform
git clone https://github.com/yourusername/SimpleCrawler-MK4.git
cd SimpleCrawler-MK4
make quick-start

# Verify services
make health
```

### 2. **Python Agent Integration**
```python
import asyncio
import aiohttp

async def simple_crawl_example():
    """Basic crawling example for agents"""
    
    async with aiohttp.ClientSession() as session:
        # Start a crawl job
        job_data = {
            "start_url": "https://fastapi.tiangolo.com/tutorial/first-steps/",
            "max_pages": 10,
            "export_format": "summary"
        }
        
        async with session.post("http://localhost:8000/crawl", json=job_data) as resp:
            job = await resp.json()
            job_id = job['job_id']
            print(f"Job started: {job_id}")
        
        # Wait for completion
        while True:
            async with session.get(f"http://localhost:8000/jobs/{job_id}") as resp:
                status = await resp.json()
                print(f"Status: {status['status']}, Progress: {status['progress']}%")
                
                if status['status'] == 'completed':
                    # Get results
                    async with session.get(f"http://localhost:8000/jobs/{job_id}/results") as resp:
                        results = await resp.json()
                        print(f"Crawled {len(results['pages'])} pages")
                        return results
                elif status['status'] == 'failed':
                    print("Job failed")
                    break
                
                await asyncio.sleep(2)

# Run the example
asyncio.run(simple_crawl_example())
```

### 3. **API Health Check**
```bash
curl http://localhost:8000/health
# Returns: {"status": "healthy", "version": "2.0.0", ...}
```

## 🎯 Use Cases for LLM/Agent Systems

### **Content Research & Analysis**
- **Multi-source research**: Crawl documentation, tutorials, forums
- **Competitive analysis**: Compare multiple product docs
- **Technology research**: Gather information on frameworks/tools

### **Code Documentation & Learning**
- **API documentation extraction**: Parse OpenAPI specs, code examples
- **Tutorial aggregation**: Collect coding tutorials and examples  
- **Code pattern analysis**: Extract common patterns and practices

### **Training Data Generation**
- **Clean text extraction**: High-quality text for LLM training
- **Structured datasets**: JSON format for fine-tuning
- **Domain-specific corpora**: Focused crawling for specialized domains

### **Real-time Information Gathering**
- **News and updates**: Monitor release notes, changelogs
- **Community insights**: Forums, discussions, Q&A sites
- **Trend analysis**: Emerging technologies and practices

## 🔍 Content Quality Features

### **LLM-Optimized Processing**
- ✅ **Clean text extraction**: Removes navigation, ads, footers
- ✅ **Proper formatting**: Preserves headings, lists, code blocks
- ✅ **Code syntax highlighting**: Language detection and formatting
- ✅ **Metadata extraction**: Titles, descriptions, keywords
- ✅ **Duplicate detection**: Avoids redundant content
- ✅ **Content scoring**: Quality metrics for filtering

### **Agent-Friendly Outputs**
- ✅ **Structured JSON**: Easy parsing for automated systems
- ✅ **Executive summaries**: Key points extraction
- ✅ **Token-optimized**: Efficient use of context windows
- ✅ **Batch processing**: Handle multiple URLs efficiently
- ✅ **Progress tracking**: Real-time status for long operations

## 🛠️ Development Environment

### **Local Development**
```bash
# Development mode with hot reload
make dev

# Monitor logs
make logs

# Scale workers for heavy crawling
make scale-workers WORKERS=10
```

### **Testing with Real Sites**
```bash
# Test against documentation sites
make test-crawl

# Check service status
make status

# View API statistics
make stats
```

## 📈 Performance & Scaling

### **Throughput Metrics**
- **API Response**: < 100ms for job submission
- **Crawl Speed**: 10-50 pages/minute (depending on sites)
- **Concurrent Jobs**: 100+ simultaneous crawls
- **Worker Scaling**: Horizontal scaling up to 50+ workers

### **Resource Requirements**
- **Minimum**: 4GB RAM, 2 CPU cores
- **Recommended**: 8GB RAM, 4 CPU cores  
- **Heavy Load**: 16GB+ RAM, 8+ CPU cores
- **Storage**: 10GB+ for crawl results

## 🔒 Security & Rate Limiting

### **Built-in Protections**
- ✅ **Rate limiting**: Respectful crawling with configurable delays
- ✅ **Input validation**: Pydantic schema validation
- ✅ **URL filtering**: Malicious URL detection
- ✅ **Robots.txt**: Respectful crawling compliance
- ✅ **Timeout limits**: Prevents hanging requests
- ✅ **Resource limits**: Memory and CPU protection

## 🌟 Why Perfect for LLM/Agent Systems

### **1. Plug & Play Integration**
- Simple REST API that any agent can consume
- Standard HTTP/JSON interface
- Docker deployment for any environment

### **2. LLM-Optimized Outputs** 
- Multiple formats designed for different LLM use cases
- Clean, structured content that agents can easily process
- Executive summaries for quick decision-making

### **3. Scalable Architecture**
- Handle multiple agent requests simultaneously
- Background processing for long-running crawls
- Horizontal scaling for high-throughput scenarios

### **4. Production Ready**
- Comprehensive error handling
- Monitoring and health checks
- Persistent storage for reliability

## 🔄 Integration Patterns

### **Streaming Integration**
```python
async def stream_crawl_results(crawler_url: str, urls: list):
    """Stream results to agent as they become available"""
    async with aiohttp.ClientSession() as session:
        for url in urls:
            job_data = {"start_url": url, "max_pages": 10, "export_format": "summary"}
            async with session.post(f"{crawler_url}/crawl", json=job_data) as resp:
                job = await resp.json()
                
                # Stream results as they come in
                async for result in monitor_job_progress(session, crawler_url, job['job_id']):
                    yield result

async def monitor_job_progress(session, crawler_url: str, job_id: str):
    """Monitor job progress and yield results incrementally"""
    while True:
        async with session.get(f"{crawler_url}/jobs/{job_id}") as resp:
            status = await resp.json()
            
            if status['status'] == 'completed':
                async with session.get(f"{crawler_url}/jobs/{job_id}/results") as resp:
                    results = await resp.json()
                    yield results
                break
            elif status['status'] == 'failed':
                yield {"error": "Job failed"}
                break
        
        await asyncio.sleep(1)
```

### **Batch Processing**
```python
async def batch_research(crawler_url: str, topics: list):
    """Process multiple research topics in parallel"""
    async with aiohttp.ClientSession() as session:
        batch_jobs = []
        
        for topic in topics:
            urls = await get_urls_for_topic(topic)  # Your implementation
            for url in urls:
                job_data = {"start_url": url, "max_pages": 20, "export_format": "summary"}
                async with session.post(f"{crawler_url}/crawl", json=job_data) as resp:
                    job = await resp.json()
                    batch_jobs.append(job['job_id'])
        
        # Wait for all jobs to complete
        results = []
        for job_id in batch_jobs:
            result = await wait_for_job_completion(session, crawler_url, job_id)
            results.append(result)
        
        return synthesize_batch_results(results)
```

## 📚 Documentation Structure

### **API Documentation**
- **OpenAPI Spec**: `http://localhost:8000/docs` - Interactive API documentation
- **Redoc**: `http://localhost:8000/redoc` - Clean API reference
- **Health Check**: `http://localhost:8000/health` - Service status

### **Example Usage**
```python
# Simple crawl for documentation
async def crawl_documentation(doc_url: str):
    async with aiohttp.ClientSession() as session:
        job_data = {
            "start_url": doc_url,
            "max_pages": 50,
            "export_format": "readable",
            "same_domain": True,
            "max_depth": 3
        }
        
        async with session.post("http://localhost:8000/crawl", json=job_data) as resp:
            job = await resp.json()
            return job['job_id']

# Check job status
async def check_job(job_id: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://localhost:8000/jobs/{job_id}") as resp:
            return await resp.json()

# Get results
async def get_results(job_id: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://localhost:8000/jobs/{job_id}/results") as resp:
            return await resp.json()
```

---

**SimpleCrawler MK4 transforms the web into structured, LLM-friendly data that agents can immediately use for research, analysis, learning, and decision-making.**

🚀 **Ready to integrate with your AI agents and LLM systems!**