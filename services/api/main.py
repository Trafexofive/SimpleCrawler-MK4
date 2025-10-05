"""
SimpleCrawler MK4 - FastAPI Microservice
Production-ready crawler API with Redis, PostgreSQL, and async workers.
"""

import asyncio
import uuid
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, HttpUrl, validator, root_validator
import redis.asyncio as redis
import asyncpg
import uvicorn

# Import our crawler (will be mounted as volume)
import sys
sys.path.append('/app/crawler')
from crawler.main import CrawlConfig, WebCrawler

# ============================================================================
# Configuration
# ============================================================================

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://crawler:password@postgres:5432/crawler_db")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
OUTPUT_DIR = Path("/app/output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# Pydantic Models
# ============================================================================

class CrawlRequest(BaseModel):
    """Request model for crawl operations."""
    
    start_url: HttpUrl = Field(..., description="Starting URL for crawling")
    max_pages: int = Field(default=10, ge=1, le=1000, description="Maximum pages to crawl")
    max_depth: int = Field(default=3, ge=0, le=10, description="Maximum crawl depth")
    same_domain: bool = Field(default=True, description="Restrict crawling to same domain")
    delay: float = Field(default=1.0, ge=0.1, le=10.0, description="Delay between requests (seconds)")
    max_concurrent: int = Field(default=5, ge=1, le=50, description="Maximum concurrent requests")
    export_format: str = Field(default="json", pattern="^(markdown|json|readable|summary)$")
    timeout: int = Field(default=30, ge=5, le=120, description="Request timeout (seconds)")
    extract_images: bool = Field(default=False, description="Extract image URLs")
    extract_links: bool = Field(default=True, description="Extract page links")
    deduplicate: bool = Field(default=True, description="Enable content deduplication")
    respect_robots: bool = Field(default=True, description="Respect robots.txt")
    user_agent: str = Field(default="SimpleCrawler-API/2.0", max_length=200)
    
    @validator('start_url')
    def validate_url(cls, v):
        if str(v).startswith(('http://', 'https://')):
            return v
        raise ValueError('URL must start with http:// or https://')

class CrawlJob(BaseModel):
    """Crawl job model."""
    
    job_id: str
    status: str  # pending, running, completed, failed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    pages_crawled: int = 0
    urls_discovered: int = 0
    errors: int = 0
    total_time: Optional[float] = None
    output_files: List[str] = []
    request_data: Dict[str, Any]

class CrawlResponse(BaseModel):
    """Response for crawl requests."""
    
    job_id: str
    status: str
    message: str
    estimated_time: Optional[int] = None

class HealthCheck(BaseModel):
    """Health check response."""
    
    status: str = "healthy"
    version: str = "2.0.0"
    uptime: float
    active_jobs: int
    completed_jobs: int
    redis_connected: bool
    database_connected: bool

# ============================================================================
# Database and Redis Setup
# ============================================================================

class DatabaseManager:
    """Database connection manager."""
    
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        """Connect to PostgreSQL."""
        self.pool = await asyncpg.create_pool(DATABASE_URL)
        await self.init_tables()
    
    async def disconnect(self):
        """Disconnect from PostgreSQL."""
        if self.pool:
            await self.pool.close()
    
    async def init_tables(self):
        """Initialize database tables."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS crawl_jobs (
                    job_id VARCHAR(36) PRIMARY KEY,
                    status VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    started_at TIMESTAMP WITH TIME ZONE,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    progress FLOAT DEFAULT 0.0,
                    pages_crawled INTEGER DEFAULT 0,
                    urls_discovered INTEGER DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    total_time FLOAT,
                    output_files TEXT[],
                    request_data JSONB NOT NULL
                )
            """)
    
    async def create_job(self, job: CrawlJob):
        """Create a new job record."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO crawl_jobs (
                    job_id, status, created_at, request_data
                ) VALUES ($1, $2, $3, $4)
            """, job.job_id, job.status, job.created_at, json.dumps(job.request_data))
    
    async def update_job(self, job_id: str, **kwargs):
        """Update job fields."""
        set_clauses = []
        values = []
        param_count = 1
        
        for key, value in kwargs.items():
            set_clauses.append(f"{key} = ${param_count}")
            values.append(value)
            param_count += 1
        
        if not set_clauses:
            return
        
        query = f"""
            UPDATE crawl_jobs 
            SET {', '.join(set_clauses)}
            WHERE job_id = ${param_count}
        """
        values.append(job_id)
        
        async with self.pool.acquire() as conn:
            await conn.execute(query, *values)
    
    async def get_job(self, job_id: str) -> Optional[CrawlJob]:
        """Get job by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM crawl_jobs WHERE job_id = $1", job_id
            )
            
            if not row:
                return None
            
            return CrawlJob(
                job_id=row['job_id'],
                status=row['status'],
                created_at=row['created_at'],
                started_at=row['started_at'],
                completed_at=row['completed_at'],
                progress=row['progress'],
                pages_crawled=row['pages_crawled'],
                urls_discovered=row['urls_discovered'],
                errors=row['errors'],
                total_time=row['total_time'],
                output_files=row['output_files'] or [],
                request_data=row['request_data']
            )
    
    async def list_jobs(self, limit: int = 50, status_filter: Optional[str] = None):
        """List jobs with optional filtering."""
        query = "SELECT * FROM crawl_jobs"
        params = []
        
        if status_filter:
            query += " WHERE status = $1"
            params.append(status_filter)
        
        query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            jobs = []
            for row in rows:
                jobs.append(CrawlJob(
                    job_id=row['job_id'],
                    status=row['status'],
                    created_at=row['created_at'],
                    started_at=row['started_at'],
                    completed_at=row['completed_at'],
                    progress=row['progress'],
                    pages_crawled=row['pages_crawled'],
                    urls_discovered=row['urls_discovered'],
                    errors=row['errors'],
                    total_time=row['total_time'],
                    output_files=row['output_files'] or [],
                    request_data=row['request_data']
                ))
            
            return jobs

class RedisManager:
    """Redis connection manager."""
    
    def __init__(self):
        self.client = None
    
    async def connect(self):
        """Connect to Redis."""
        self.client = redis.from_url(REDIS_URL)
        await self.client.ping()
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
    
    async def queue_job(self, job_id: str, request_data: Dict[str, Any]):
        """Queue a job for processing."""
        await self.client.lpush("crawl_queue", json.dumps({
            "job_id": job_id,
            "request_data": request_data
        }))
    
    async def get_queue_length(self):
        """Get queue length."""
        return await self.client.llen("crawl_queue")

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="SimpleCrawler MK4 API",
    description="Production-ready async web crawler microservice",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global managers
db = DatabaseManager()
redis_client = RedisManager()
app_start_time = datetime.now(timezone.utc)

# ============================================================================
# Dependencies
# ============================================================================

async def get_job_by_id(job_id: str) -> CrawlJob:
    """Get job by ID dependency."""
    job = await db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    return job

# ============================================================================
# Background Tasks
# ============================================================================

async def process_crawl_job(job_id: str, request_data: Dict[str, Any]):
    """Process a crawl job (runs in worker container)."""
    try:
        # Update job status
        await db.update_job(job_id, 
            status="running", 
            started_at=datetime.now(timezone.utc)
        )
        
        # Create crawler config
        config = CrawlConfig(
            start_url=request_data['start_url'],
            max_pages=request_data.get('max_pages', 10),
            max_depth=request_data.get('max_depth', 3),
            same_domain=request_data.get('same_domain', True),
            delay=request_data.get('delay', 1.0),
            max_concurrent=request_data.get('max_concurrent', 5),
            timeout=request_data.get('timeout', 30),
            extract_images=request_data.get('extract_images', False),
            extract_links=request_data.get('extract_links', True),
            deduplicate=request_data.get('deduplicate', True),
            respect_robots=request_data.get('respect_robots', True),
            user_agent=request_data.get('user_agent', 'SimpleCrawler-API/2.0'),
            export_format=request_data.get('export_format', 'json'),
            output_dir=str(OUTPUT_DIR / job_id),
            verbose=False
        )
        
        # Execute crawl
        crawler = WebCrawler(config)
        summary = await crawler.crawl()
        
        # Find output files
        job_output_dir = OUTPUT_DIR / job_id
        output_files = []
        if job_output_dir.exists():
            output_files = [f.name for f in job_output_dir.iterdir() if f.is_file()]
        
        # Update job with results
        await db.update_job(job_id,
            status="completed",
            completed_at=datetime.now(timezone.utc),
            progress=100.0,
            pages_crawled=summary['stats']['pages_crawled'],
            urls_discovered=summary['stats']['urls_discovered'],
            errors=summary['stats']['errors'],
            total_time=summary['stats'].get('total_time', 0),
            output_files=output_files
        )
        
    except Exception as e:
        # Update job with error
        await db.update_job(job_id,
            status="failed",
            completed_at=datetime.now(timezone.utc),
            progress=0.0
        )
        print(f"Job {job_id} failed: {e}")

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API root."""
    return {
        "service": "SimpleCrawler MK4 API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    uptime = (datetime.now(timezone.utc) - app_start_time).total_seconds()
    
    # Check Redis connection
    redis_connected = True
    try:
        await redis_client.client.ping()
    except:
        redis_connected = False
    
    # Check database connection
    database_connected = True
    try:
        async with db.pool.acquire() as conn:
            await conn.execute("SELECT 1")
    except:
        database_connected = False
    
    # Get job counts
    jobs = await db.list_jobs(limit=1000)
    active_jobs = len([j for j in jobs if j.status in ['pending', 'running']])
    completed_jobs = len([j for j in jobs if j.status in ['completed', 'failed']])
    
    return HealthCheck(
        uptime=uptime,
        active_jobs=active_jobs,
        completed_jobs=completed_jobs,
        redis_connected=redis_connected,
        database_connected=database_connected
    )

@app.post("/crawl", response_model=CrawlResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_crawl(request: CrawlRequest):
    """Start a new crawl job."""
    
    job_id = str(uuid.uuid4())
    
    # Create job record
    job = CrawlJob(
        job_id=job_id,
        status="pending",
        created_at=datetime.now(timezone.utc),
        request_data=request.dict(mode='json')  # Serialize HttpUrl properly
    )
    
        await db.create_job(job)
    
    # Queue job for processing
    await redis_client.queue_job(job_id, request.dict())
    
    # Estimate completion time
    estimated_time = request.max_pages * request.delay + 30
    
    return CrawlResponse(
        job_id=job_id,
        status="accepted",
        message=f"Crawl job {job_id} queued for processing",
        estimated_time=int(estimated_time)
    )

@app.get("/jobs/{job_id}", response_model=CrawlJob)
async def get_job_status(job: CrawlJob = Depends(get_job_by_id)):
    """Get job status."""
    return job

@app.get("/jobs", response_model=List[CrawlJob])
async def list_jobs(
    status_filter: Optional[str] = Query(None, regex="^(pending|running|completed|failed)$"),
    limit: int = Query(50, ge=1, le=1000)
):
    """List crawl jobs."""
    return await db.list_jobs(limit=limit, status_filter=status_filter)

@app.get("/jobs/{job_id}/results")
async def get_crawl_results(job: CrawlJob = Depends(get_job_by_id)):
    """Get crawl results."""
    
    if job.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job {job.job_id} is not completed (status: {job.status})"
        )
    
    # Load JSON results if available
    json_file = OUTPUT_DIR / job.job_id / "crawl_results.json"
    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            pages_data = json.load(f)
    else:
        pages_data = []
    
    return {
        "job_id": job.job_id,
        "summary": {
            "pages_crawled": job.pages_crawled,
            "urls_discovered": job.urls_discovered,
            "errors": job.errors,
            "total_time": job.total_time
        },
        "pages": pages_data,
        "files": job.output_files
    }

@app.get("/download/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    """Download result files."""
    
    job = await get_job_by_id(job_id)
    
    file_path = OUTPUT_DIR / job_id / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {filename} not found"
        )
    
    # Security check
    try:
        file_path.resolve().relative_to(OUTPUT_DIR / job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its files."""
    
    job = await get_job_by_id(job_id)
    
    # Delete files
    import shutil
    job_output_dir = OUTPUT_DIR / job_id
    if job_output_dir.exists():
        shutil.rmtree(job_output_dir)
    
    # Delete from database
    async with db.pool.acquire() as conn:
        await conn.execute("DELETE FROM crawl_jobs WHERE job_id = $1", job_id)
    
    return {"message": f"Job {job_id} deleted successfully"}

@app.get("/stats")
async def get_stats():
    """Get API statistics."""
    
    jobs = await db.list_jobs(limit=1000)
    
    stats = {
        "total_jobs": len(jobs),
        "pending": len([j for j in jobs if j.status == "pending"]),
        "running": len([j for j in jobs if j.status == "running"]),
        "completed": len([j for j in jobs if j.status == "completed"]),
        "failed": len([j for j in jobs if j.status == "failed"]),
        "queue_length": await redis_client.get_queue_length(),
        "total_pages_crawled": sum(j.pages_crawled for j in jobs),
        "avg_crawl_time": sum(j.total_time or 0 for j in jobs if j.total_time) / max(1, len([j for j in jobs if j.total_time]))
    }
    
    return stats

# ============================================================================
# Application Lifecycle
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    print("🚀 SimpleCrawler MK4 API starting...")
    
    await db.connect()
    print("✅ Database connected")
    
    await redis_client.connect()
    print("✅ Redis connected")
    
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print("🎯 API ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("🛑 SimpleCrawler MK4 API shutting down...")
    
    await db.disconnect()
    await redis_client.disconnect()
    
    print("✅ Shutdown complete!")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level="info"
    )