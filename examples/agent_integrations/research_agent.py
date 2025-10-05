#!/usr/bin/env python3
"""
Research Agent Example
======================

Demonstrates how to integrate SimpleCrawler MK4 with an AI research agent.
This agent can gather information from multiple sources and synthesize research.
"""

import asyncio
import json
from typing import List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

# Import SimpleCrawler client (assuming it's installed)
try:
    from simplecrawler_client import AsyncCrawlerClient, CrawlerClient
except ImportError:
    print("SimpleCrawler client not installed. Using mock client for demo.")
    
    # Mock client for demonstration
    class MockCrawlerClient:
        def __init__(self, base_url: str):
            self.base_url = base_url
        
        async def crawl(self, start_url: str, **kwargs):
            # Return mock job
            return type('Job', (), {
                'job_id': f"job_{hash(start_url) % 10000}",
                'status': 'pending'
            })()
        
        async def wait_for_completion(self, job_id: str):
            # Return mock results
            return type('Results', (), {
                'pages': [
                    {
                        'url': 'https://example.com/page1',
                        'title': 'Sample Documentation',
                        'content': 'This is sample content from the crawled page.',
                        'summary': 'Key points about the topic with important information.',
                        'code_examples': ['print("Hello World")'],
                        'word_count': 250
                    }
                ]
            })()
    
    AsyncCrawlerClient = MockCrawlerClient
    CrawlerClient = MockCrawlerClient


@dataclass
class ResearchTask:
    """Represents a research task with sources and parameters."""
    topic: str
    sources: List[str]
    depth: str = "comprehensive"  # shallow, moderate, comprehensive
    focus: str = "general"        # general, technical, business, academic
    max_pages_per_source: int = 20


@dataclass 
class ResearchResult:
    """Contains synthesized research results."""
    topic: str
    sources_crawled: int
    total_pages: int
    key_findings: List[str]
    technical_details: List[Dict[str, Any]]
    code_examples: List[str]
    references: List[str]
    confidence_score: float
    generated_at: datetime


class AIResearchAgent:
    """
    AI Research Agent that uses SimpleCrawler MK4 to gather and synthesize information.
    
    Features:
    - Multi-source research with parallel crawling
    - Content analysis and synthesis
    - Automatic quality scoring
    - Different research depths and focuses
    - Export to multiple formats
    """
    
    def __init__(self, crawler_url: str = "http://localhost:8000"):
        """Initialize the research agent with crawler connection."""
        self.crawler = AsyncCrawlerClient(crawler_url)
        self.research_history = []
    
    async def research_topic(self, task: ResearchTask) -> ResearchResult:
        """
        Perform comprehensive research on a topic.
        
        Args:
            task: ResearchTask with topic, sources, and parameters
            
        Returns:
            ResearchResult with synthesized findings
        """
        print(f"🔍 Starting research on: {task.topic}")
        print(f"📚 Sources to crawl: {len(task.sources)}")
        
        # Determine crawl parameters based on task depth
        crawl_params = self._get_crawl_parameters(task)
        
        # Start parallel crawls for all sources
        crawl_jobs = []
        for i, source in enumerate(task.sources):
            print(f"   🌐 Starting crawl {i+1}/{len(task.sources)}: {source}")
            
            job = await self.crawler.crawl(
                start_url=source,
                max_pages=task.max_pages_per_source,
                **crawl_params
            )
            crawl_jobs.append((source, job))
        
        # Wait for all crawls to complete and collect results
        all_pages = []
        sources_completed = 0
        
        for source, job in crawl_jobs:
            try:
                print(f"   ⏳ Waiting for completion: {source}")
                results = await self.crawler.wait_for_completion(job.job_id)
                all_pages.extend(results.pages)
                sources_completed += 1
                print(f"   ✅ Completed {source}: {len(results.pages)} pages")
            except Exception as e:
                print(f"   ❌ Failed {source}: {e}")
        
        # Synthesize research from collected data
        research_result = await self._synthesize_research(task, all_pages, sources_completed)
        
        # Store in research history
        self.research_history.append(research_result)
        
        print(f"🎉 Research completed!")
        print(f"   📊 Crawled {research_result.total_pages} pages from {sources_completed} sources")
        print(f"   🎯 Confidence: {research_result.confidence_score:.2%}")
        
        return research_result
    
    def _get_crawl_parameters(self, task: ResearchTask) -> Dict[str, Any]:
        """Get crawl parameters optimized for the research task."""
        
        # Base parameters
        params = {
            'same_domain': True,
            'delay': 0.5,
            'extract_links': True,
            'respect_robots': True
        }
        
        # Adjust based on research depth
        if task.depth == "shallow":
            params.update({
                'max_depth': 1,
                'export_format': 'summary',
                'max_concurrent': 10
            })
        elif task.depth == "moderate":
            params.update({
                'max_depth': 2,
                'export_format': 'readable',
                'max_concurrent': 5
            })
        else:  # comprehensive
            params.update({
                'max_depth': 3,
                'export_format': 'json',
                'max_concurrent': 3
            })
        
        # Adjust based on research focus
        if task.focus == "technical":
            params.update({
                'extract_code': True,
                'extract_images': False
            })
        elif task.focus == "business":
            params.update({
                'extract_code': False,
                'extract_images': True
            })
        
        return params
    
    async def _synthesize_research(
        self, 
        task: ResearchTask, 
        pages: List[Dict[str, Any]], 
        sources_count: int
    ) -> ResearchResult:
        """Synthesize research results from crawled pages."""
        
        # Extract key information
        key_findings = self._extract_key_findings(pages, task.topic)
        technical_details = self._extract_technical_details(pages)
        code_examples = self._extract_code_examples(pages)
        references = self._extract_references(pages)
        
        # Calculate confidence score based on various factors
        confidence_score = self._calculate_confidence_score(
            pages, sources_count, len(task.sources)
        )
        
        return ResearchResult(
            topic=task.topic,
            sources_crawled=sources_count,
            total_pages=len(pages),
            key_findings=key_findings,
            technical_details=technical_details,
            code_examples=code_examples,
            references=references,
            confidence_score=confidence_score,
            generated_at=datetime.now()
        )
    
    def _extract_key_findings(self, pages: List[Dict], topic: str) -> List[str]:
        """Extract key findings related to the research topic."""
        findings = []
        
        for page in pages:
            # Look for summary or key points in page content
            if 'summary' in page:
                findings.append(f"From {page.get('title', 'Unknown')}: {page['summary']}")
            elif 'content' in page and topic.lower() in page['content'].lower():
                # Extract sentences containing the topic
                sentences = page['content'].split('.')
                relevant = [s.strip() for s in sentences if topic.lower() in s.lower()]
                findings.extend(relevant[:2])  # Top 2 relevant sentences
        
        return findings[:10]  # Limit to top 10 findings
    
    def _extract_technical_details(self, pages: List[Dict]) -> List[Dict[str, Any]]:
        """Extract technical details like APIs, configurations, etc."""
        technical = []
        
        for page in pages:
            detail = {
                'source': page.get('url', 'Unknown'),
                'title': page.get('title', 'Unknown'),
                'type': 'documentation'
            }
            
            # Look for API endpoints
            content = page.get('content', '')
            if any(keyword in content.lower() for keyword in ['api', 'endpoint', 'rest', 'graphql']):
                detail['type'] = 'api_documentation'
            
            # Look for configuration
            if any(keyword in content.lower() for keyword in ['config', 'setup', 'install', 'configure']):
                detail['type'] = 'configuration'
            
            technical.append(detail)
        
        return technical
    
    def _extract_code_examples(self, pages: List[Dict]) -> List[str]:
        """Extract code examples from pages."""
        code_examples = []
        
        for page in pages:
            if 'code_examples' in page and page['code_examples']:
                code_examples.extend(page['code_examples'])
            
            # Look for code in content (simple heuristic)
            content = page.get('content', '')
            if '```' in content:
                # Extract code blocks
                blocks = content.split('```')
                for i in range(1, len(blocks), 2):  # Every other block should be code
                    code_examples.append(blocks[i].strip())
        
        return code_examples[:20]  # Limit to 20 examples
    
    def _extract_references(self, pages: List[Dict]) -> List[str]:
        """Extract reference URLs and sources."""
        references = []
        
        for page in pages:
            url = page.get('url', '')
            title = page.get('title', 'Unknown Page')
            if url:
                references.append(f"{title} - {url}")
        
        return references
    
    def _calculate_confidence_score(
        self, 
        pages: List[Dict], 
        sources_completed: int, 
        total_sources: int
    ) -> float:
        """Calculate confidence score based on research quality."""
        
        # Base score from source completion rate
        source_score = sources_completed / total_sources if total_sources > 0 else 0
        
        # Content quality score
        total_words = sum(page.get('word_count', 0) for page in pages)
        content_score = min(total_words / 10000, 1.0)  # Normalize to max 10k words
        
        # Diversity score (number of different sources)
        unique_domains = len(set(
            page.get('url', '').split('/')[2] for page in pages 
            if page.get('url')
        ))
        diversity_score = min(unique_domains / 5, 1.0)  # Normalize to max 5 domains
        
        # Weighted average
        confidence = (source_score * 0.4 + content_score * 0.4 + diversity_score * 0.2)
        
        return confidence
    
    def export_research(self, result: ResearchResult, format: str = "markdown") -> str:
        """Export research results in various formats."""
        
        if format == "markdown":
            return self._export_markdown(result)
        elif format == "json":
            return json.dumps(result.__dict__, default=str, indent=2)
        elif format == "summary":
            return self._export_summary(result)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_markdown(self, result: ResearchResult) -> str:
        """Export research as markdown report."""
        
        md = f"""# Research Report: {result.topic}

**Generated:** {result.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
**Sources Crawled:** {result.sources_crawled}
**Total Pages:** {result.total_pages}
**Confidence Score:** {result.confidence_score:.2%}

## Key Findings

"""
        
        for i, finding in enumerate(result.key_findings, 1):
            md += f"{i}. {finding}\n\n"
        
        if result.technical_details:
            md += "## Technical Details\n\n"
            for detail in result.technical_details[:5]:  # Top 5
                md += f"- **{detail['title']}** ({detail['type']})\n"
        
        if result.code_examples:
            md += "\n## Code Examples\n\n"
            for i, code in enumerate(result.code_examples[:3], 1):  # Top 3
                md += f"### Example {i}\n```\n{code}\n```\n\n"
        
        md += "\n## References\n\n"
        for ref in result.references:
            md += f"- {ref}\n"
        
        return md
    
    def _export_summary(self, result: ResearchResult) -> str:
        """Export research as executive summary."""
        
        summary = f"""EXECUTIVE SUMMARY: {result.topic}

SCOPE: Analyzed {result.total_pages} pages from {result.sources_crawled} sources
CONFIDENCE: {result.confidence_score:.1%}

TOP FINDINGS:
"""
        
        for i, finding in enumerate(result.key_findings[:5], 1):
            summary += f"{i}. {finding[:100]}...\n"
        
        if result.code_examples:
            summary += f"\nCODE EXAMPLES: {len(result.code_examples)} examples found"
        
        summary += f"\nTECHNICAL FOCUS: {len(result.technical_details)} technical resources"
        
        return summary


# Example usage and demo
async def demo_research_agent():
    """Demonstrate the research agent capabilities."""
    
    print("🤖 SimpleCrawler MK4 - AI Research Agent Demo")
    print("=" * 50)
    
    # Initialize the agent
    agent = AIResearchAgent()
    
    # Define research tasks
    research_tasks = [
        ResearchTask(
            topic="FastAPI Python Framework",
            sources=[
                "https://fastapi.tiangolo.com/",
                "https://fastapi.tiangolo.com/tutorial/",
                "https://fastapi.tiangolo.com/advanced/"
            ],
            depth="moderate",
            focus="technical",
            max_pages_per_source=15
        ),
        ResearchTask(
            topic="Docker containerization",
            sources=[
                "https://docs.docker.com/get-started/",
                "https://docs.docker.com/compose/"
            ],
            depth="comprehensive",
            focus="technical",
            max_pages_per_source=25
        )
    ]
    
    # Execute research tasks
    for task in research_tasks:
        print(f"\n🎯 Research Task: {task.topic}")
        print("-" * 40)
        
        try:
            result = await agent.research_topic(task)
            
            # Export results
            print("\n📄 Markdown Report:")
            print("=" * 20)
            markdown_report = agent.export_research(result, "markdown")
            print(markdown_report[:500] + "..." if len(markdown_report) > 500 else markdown_report)
            
            print("\n📋 Executive Summary:")
            print("=" * 20)
            summary = agent.export_research(result, "summary")
            print(summary)
            
        except Exception as e:
            print(f"❌ Research failed: {e}")
    
    print(f"\n🎉 Demo completed! Total research history: {len(agent.research_history)} tasks")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_research_agent())