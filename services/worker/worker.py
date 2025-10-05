"""
SimpleCrawler MK4 - Background Worker
Processes crawl jobs from Redis queue.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import redis.asyncio as redis
import asyncpg

# Import crawler (mounted as volume)
sys.path.append('/app/crawler')
from crawler.main import CrawlConfig, WebCrawler

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://crawler:password@postgres:5432/crawler_db")
OUTPUT_DIR = Path("/app/output")
OUTPUT_DIR.mkdir(exist_ok=True)

class WorkerManager:
    """Worker process manager."""
    
    def __init__(self):
        self.redis_client = None
        self.db_pool = None
        self.running = True
    
    async def connect(self):
        """Connect to Redis and PostgreSQL."""
        self.redis_client = redis.from_url(REDIS_URL)
        await self.redis_client.ping()
        
        self.db_pool = await asyncpg.create_pool(DATABASE_URL)
        
        print("✅ Worker connected to Redis and PostgreSQL")
    
    async def disconnect(self):
        """Disconnect from services."""
        if self.redis_client:
            await self.redis_client.close()
        
        if self.db_pool:
            await self.db_pool.close()
        
        print("✅ Worker disconnected")
    
    async def update_job_status(self, job_id: str, **kwargs):
        """Update job status in database."""
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
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(query, *values)
    
    async def process_crawl_job(self, job_id: str, request_data: dict):
        """Process a single crawl job."""
        
        print(f"🔄 Processing job {job_id}")
        
        try:
            # Update job status to running
            await self.update_job_status(
                job_id,
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
                user_agent=request_data.get('user_agent', 'SimpleCrawler-Worker/2.0'),
                export_format=request_data.get('export_format', 'json'),
                output_dir=str(OUTPUT_DIR / job_id),
                verbose=False
            )
            
            print(f"🕷️  Starting crawl: {config.start_url}")
            
            # Execute crawl
            crawler = WebCrawler(config)
            summary = await crawler.crawl()
            
            # Find output files
            job_output_dir = OUTPUT_DIR / job_id
            output_files = []
            if job_output_dir.exists():
                output_files = [f.name for f in job_output_dir.iterdir() if f.is_file()]
            
            # Update job with success
            await self.update_job_status(
                job_id,
                status="completed",
                completed_at=datetime.now(timezone.utc),
                progress=100.0,
                pages_crawled=summary['stats']['pages_crawled'],
                urls_discovered=summary['stats']['urls_discovered'],
                errors=summary['stats']['errors'],
                total_time=summary['stats'].get('total_time', 0),
                output_files=output_files
            )
            
            print(f"✅ Job {job_id} completed: {summary['stats']['pages_crawled']} pages crawled")
            
        except Exception as e:
            print(f"❌ Job {job_id} failed: {e}")
            
            # Update job with failure
            await self.update_job_status(
                job_id,
                status="failed",
                completed_at=datetime.now(timezone.utc),
                progress=0.0
            )
    
    async def run(self):
        """Main worker loop."""
        print("🚀 Worker started, waiting for jobs...")
        
        while self.running:
            try:
                # Block and wait for job from queue (timeout 5 seconds)
                job_data = await self.redis_client.brpop("crawl_queue", timeout=5)
                
                if job_data:
                    queue_name, job_json = job_data
                    job_info = json.loads(job_json)
                    
                    job_id = job_info['job_id']
                    request_data = job_info['request_data']
                    
                    # Process the job
                    await self.process_crawl_job(job_id, request_data)
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                print("🛑 Worker cancelled")
                break
            
            except Exception as e:
                print(f"⚠️  Worker error: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def stop(self):
        """Stop the worker."""
        self.running = False
        print("🛑 Worker stopping...")

async def main():
    """Main worker function."""
    worker = WorkerManager()
    
    try:
        await worker.connect()
        await worker.run()
    
    except KeyboardInterrupt:
        print("\n🛑 Worker interrupted")
    
    finally:
        await worker.stop()
        await worker.disconnect()

if __name__ == "__main__":
    asyncio.run(main())