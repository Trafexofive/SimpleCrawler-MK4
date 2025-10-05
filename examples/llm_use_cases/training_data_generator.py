#!/usr/bin/env python3
"""
LLM Training Data Generator
===========================

Use SimpleCrawler MK4 to generate high-quality training data for LLMs.
Optimized for clean text extraction, proper formatting, and structured datasets.
"""

import asyncio
import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

# Mock crawler client for demo
class MockCrawlerClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    async def crawl(self, start_url: str, **kwargs):
        return type('Job', (), {'job_id': f"job_{hash(start_url) % 10000}"})()
    
    async def wait_for_completion(self, job_id: str):
        return type('Results', (), {
            'pages': [
                {
                    'url': 'https://docs.python.org/3/tutorial/introduction.html',
                    'title': 'An Informal Introduction to Python',
                    'content': '''# An Informal Introduction to Python

In the following examples, input and output are distinguished by the presence or absence of prompts (>>> and ...): to repeat the example, you must type everything after the prompt, when the prompt appears; lines that do not begin with a prompt are output from the interpreter.

## Using Python as a Calculator

Let's try some simple Python commands. Start the Python interpreter and wait for the primary prompt, >>>.

```python
>>> 2 + 2
4
>>> 50 - 5*6
20
>>> (50 - 5*6) / 4
5.0
```

The integer numbers (e.g. 2, 4, 20) have type int, the ones with a fractional part (e.g. 5.0, 1.6) have type float.''',
                    'word_count': 150,
                    'reading_time': 2.5,
                    'quality_score': 0.95,
                    'code_blocks': [
                        {
                            'language': 'python',
                            'code': '>>> 2 + 2\n4\n>>> 50 - 5*6\n20'
                        }
                    ]
                },
                {
                    'url': 'https://docs.python.org/3/tutorial/controlflow.html',
                    'title': 'More Control Flow Tools',
                    'content': '''# More Control Flow Tools

Besides the while statement just introduced, Python knows the usual control flow statements known from other languages, with some twists.

## if Statements

Perhaps the most well-known statement type is the if statement. For example:

```python
>>> x = int(input("Please enter an integer: "))
Please enter an integer: 42
>>> if x < 0:
...     x = 0
...     print('Negative changed to zero')
... elif x == 0:
...     print('Zero')
... elif x == 1:
...     print('Single')
... else:
...     print('More')
...
More
```''',
                    'word_count': 120,
                    'reading_time': 2.0,
                    'quality_score': 0.92
                }
            ]
        })()

try:
    from simplecrawler_client import AsyncCrawlerClient
except ImportError:
    AsyncCrawlerClient = MockCrawlerClient


@dataclass
class TrainingExample:
    """Represents a single training example for LLMs."""
    text: str
    source: str
    title: str
    word_count: int
    quality_score: float
    category: str
    metadata: Dict[str, Any]
    hash: str = ""
    
    def __post_init__(self):
        """Generate content hash for deduplication."""
        if not self.hash:
            self.hash = hashlib.md5(self.text.encode()).hexdigest()


@dataclass
class TrainingDataset:
    """Collection of training examples with metadata."""
    name: str
    description: str
    examples: List[TrainingExample]
    total_words: int
    quality_threshold: float
    created_at: datetime
    stats: Dict[str, Any]


class LLMTrainingDataGenerator:
    """
    Generate high-quality training data for LLMs using SimpleCrawler MK4.
    
    Features:
    - Clean text extraction optimized for LLM training
    - Quality filtering and scoring
    - Deduplication and normalization
    - Multiple output formats (JSONL, Parquet, HF Datasets)
    - Domain-specific dataset creation
    """
    
    def __init__(self, crawler_url: str = "http://localhost:8000"):
        """Initialize the training data generator."""
        self.crawler = AsyncCrawlerClient(crawler_url)
        self.datasets = []
    
    async def create_training_dataset(
        self,
        dataset_name: str,
        sources: List[Dict[str, Any]],
        quality_threshold: float = 0.7,
        max_words_per_example: int = 2000,
        min_words_per_example: int = 50,
        categories: List[str] = None
    ) -> TrainingDataset:
        """
        Create a training dataset from multiple sources.
        
        Args:
            dataset_name: Name of the dataset
            sources: List of source configurations with URLs and parameters
            quality_threshold: Minimum quality score (0.0 to 1.0)
            max_words_per_example: Maximum words per training example
            min_words_per_example: Minimum words per training example
            categories: Categories to filter content
        
        Returns:
            TrainingDataset with processed examples
        """
        
        print(f"🏗️  Creating training dataset: {dataset_name}")
        print(f"📚 Processing {len(sources)} source collections")
        
        all_examples = []
        
        # Process each source collection
        for i, source_config in enumerate(sources):
            print(f"\n📖 Processing source {i+1}/{len(sources)}: {source_config.get('name', 'Unknown')}")
            
            # Start crawl with training-optimized parameters
            crawl_params = self._get_training_crawl_params(source_config)
            
            job = await self.crawler.crawl(
                start_url=source_config['url'],
                **crawl_params
            )
            
            print(f"   🔄 Crawling started (Job: {job.job_id})")
            results = await self.crawler.wait_for_completion(job.job_id)
            
            # Process pages into training examples
            examples = self._process_pages_for_training(
                results.pages,
                source_config,
                quality_threshold,
                max_words_per_example,
                min_words_per_example
            )
            
            all_examples.extend(examples)
            print(f"   ✅ Generated {len(examples)} training examples")
        
        # Deduplicate examples
        unique_examples = self._deduplicate_examples(all_examples)
        print(f"🔍 Deduplication: {len(all_examples)} → {len(unique_examples)} examples")
        
        # Create dataset
        dataset = TrainingDataset(
            name=dataset_name,
            description=f"Training dataset created from {len(sources)} sources",
            examples=unique_examples,
            total_words=sum(ex.word_count for ex in unique_examples),
            quality_threshold=quality_threshold,
            created_at=datetime.now(),
            stats=self._calculate_dataset_stats(unique_examples)
        )
        
        self.datasets.append(dataset)
        
        print(f"🎉 Dataset created!")
        print(f"   📊 {len(dataset.examples)} examples")
        print(f"   📝 {dataset.total_words:,} total words")
        print(f"   ⭐ Average quality: {dataset.stats['avg_quality']:.2%}")
        
        return dataset
    
    def _get_training_crawl_params(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get crawl parameters optimized for LLM training data."""
        
        # Base parameters for clean text extraction
        params = {
            'export_format': 'readable',  # Clean, formatted text
            'max_depth': source_config.get('max_depth', 3),
            'max_pages': source_config.get('max_pages', 100),
            'same_domain': source_config.get('same_domain', True),
            'delay': 1.0,  # Respectful crawling
            'extract_images': False,  # Text-only for LLM training
            'extract_links': False,   # Focus on content, not navigation
            'clean_content': True,    # Remove ads, navigation, etc.
            'remove_duplicates': True,
            'min_word_count': 50,     # Skip very short pages
            'max_concurrent': 3       # Conservative for quality
        }
        
        # Domain-specific adjustments
        domain_type = source_config.get('domain_type', 'general')
        
        if domain_type == 'documentation':
            params.update({
                'extract_code': True,
                'preserve_formatting': True,
                'extract_headings': True
            })
        elif domain_type == 'educational':
            params.update({
                'extract_examples': True,
                'preserve_structure': True
            })
        elif domain_type == 'news':
            params.update({
                'extract_dates': True,
                'extract_authors': True
            })
        
        return params
    
    def _process_pages_for_training(
        self,
        pages: List[Dict[str, Any]],
        source_config: Dict[str, Any],
        quality_threshold: float,
        max_words: int,
        min_words: int
    ) -> List[TrainingExample]:
        """Process crawled pages into training examples."""
        
        examples = []
        category = source_config.get('category', 'general')
        
        for page in pages:
            content = page.get('content', '')
            word_count = page.get('word_count', 0)
            quality_score = page.get('quality_score', 0.5)
            
            # Filter by quality and length
            if quality_score < quality_threshold:
                continue
                
            if word_count < min_words or word_count > max_words:
                continue
            
            # Clean and normalize content
            cleaned_content = self._clean_content_for_training(content)
            
            if not cleaned_content or len(cleaned_content.split()) < min_words:
                continue
            
            # Create training example
            example = TrainingExample(
                text=cleaned_content,
                source=page.get('url', ''),
                title=page.get('title', ''),
                word_count=len(cleaned_content.split()),
                quality_score=quality_score,
                category=category,
                metadata={
                    'source_domain': source_config.get('name', ''),
                    'crawled_at': datetime.now().isoformat(),
                    'reading_time': page.get('reading_time', 0),
                    'has_code': 'code_blocks' in page and len(page['code_blocks']) > 0
                }
            )
            
            examples.append(example)
        
        return examples
    
    def _clean_content_for_training(self, content: str) -> str:
        """Clean content for LLM training."""
        
        # Remove excessive whitespace
        lines = [line.strip() for line in content.split('\n')]
        lines = [line for line in lines if line]  # Remove empty lines
        
        # Join with proper spacing
        cleaned = '\n'.join(lines)
        
        # Remove duplicate consecutive lines
        prev_line = ""
        result_lines = []
        for line in cleaned.split('\n'):
            if line != prev_line:
                result_lines.append(line)
                prev_line = line
        
        return '\n'.join(result_lines)
    
    def _deduplicate_examples(self, examples: List[TrainingExample]) -> List[TrainingExample]:
        """Remove duplicate examples based on content hash."""
        
        seen_hashes = set()
        unique_examples = []
        
        for example in examples:
            if example.hash not in seen_hashes:
                seen_hashes.add(example.hash)
                unique_examples.append(example)
        
        return unique_examples
    
    def _calculate_dataset_stats(self, examples: List[TrainingExample]) -> Dict[str, Any]:
        """Calculate statistics for the dataset."""
        
        if not examples:
            return {}
        
        word_counts = [ex.word_count for ex in examples]
        quality_scores = [ex.quality_score for ex in examples]
        
        # Category distribution
        categories = {}
        for ex in examples:
            categories[ex.category] = categories.get(ex.category, 0) + 1
        
        return {
            'total_examples': len(examples),
            'avg_words_per_example': sum(word_counts) / len(word_counts),
            'min_words': min(word_counts),
            'max_words': max(word_counts),
            'avg_quality': sum(quality_scores) / len(quality_scores),
            'min_quality': min(quality_scores),
            'max_quality': max(quality_scores),
            'categories': categories,
            'total_unique_sources': len(set(ex.source for ex in examples))
        }
    
    def export_dataset(
        self,
        dataset: TrainingDataset,
        output_dir: str,
        formats: List[str] = None
    ) -> Dict[str, str]:
        """
        Export dataset in various formats.
        
        Args:
            dataset: TrainingDataset to export
            output_dir: Output directory
            formats: List of formats ('jsonl', 'json', 'txt', 'parquet')
        
        Returns:
            Dictionary mapping format to output file path
        """
        
        if formats is None:
            formats = ['jsonl', 'json']
        
        os.makedirs(output_dir, exist_ok=True)
        output_files = {}
        
        base_filename = f"{dataset.name.replace(' ', '_').lower()}"
        
        for fmt in formats:
            if fmt == 'jsonl':
                filepath = os.path.join(output_dir, f"{base_filename}.jsonl")
                self._export_jsonl(dataset, filepath)
                output_files['jsonl'] = filepath
            
            elif fmt == 'json':
                filepath = os.path.join(output_dir, f"{base_filename}.json")
                self._export_json(dataset, filepath)
                output_files['json'] = filepath
            
            elif fmt == 'txt':
                filepath = os.path.join(output_dir, f"{base_filename}.txt")
                self._export_txt(dataset, filepath)
                output_files['txt'] = filepath
            
            elif fmt == 'parquet':
                try:
                    import pandas as pd
                    filepath = os.path.join(output_dir, f"{base_filename}.parquet")
                    self._export_parquet(dataset, filepath)
                    output_files['parquet'] = filepath
                except ImportError:
                    print("⚠️  Pandas not available, skipping Parquet export")
        
        # Export metadata
        metadata_path = os.path.join(output_dir, f"{base_filename}_metadata.json")
        self._export_metadata(dataset, metadata_path)
        output_files['metadata'] = metadata_path
        
        return output_files
    
    def _export_jsonl(self, dataset: TrainingDataset, filepath: str):
        """Export dataset as JSONL (JSON Lines) format."""
        with open(filepath, 'w', encoding='utf-8') as f:
            for example in dataset.examples:
                json.dump(asdict(example), f, ensure_ascii=False)
                f.write('\n')
    
    def _export_json(self, dataset: TrainingDataset, filepath: str):
        """Export dataset as JSON format."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(dataset), f, indent=2, ensure_ascii=False, default=str)
    
    def _export_txt(self, dataset: TrainingDataset, filepath: str):
        """Export dataset as plain text (concatenated examples)."""
        with open(filepath, 'w', encoding='utf-8') as f:
            for i, example in enumerate(dataset.examples):
                f.write(f"# Example {i+1}: {example.title}\n")
                f.write(f"# Source: {example.source}\n")
                f.write(f"# Category: {example.category}\n\n")
                f.write(example.text)
                f.write("\n\n" + "="*80 + "\n\n")
    
    def _export_parquet(self, dataset: TrainingDataset, filepath: str):
        """Export dataset as Parquet format."""
        import pandas as pd
        
        data = []
        for example in dataset.examples:
            row = asdict(example)
            row['metadata'] = json.dumps(row['metadata'])
            data.append(row)
        
        df = pd.DataFrame(data)
        df.to_parquet(filepath, index=False)
    
    def _export_metadata(self, dataset: TrainingDataset, filepath: str):
        """Export dataset metadata."""
        metadata = {
            'name': dataset.name,
            'description': dataset.description,
            'created_at': dataset.created_at.isoformat(),
            'total_examples': len(dataset.examples),
            'total_words': dataset.total_words,
            'quality_threshold': dataset.quality_threshold,
            'stats': dataset.stats
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)


# Demo and example usage
async def demo_training_data_generator():
    """Demonstrate the training data generator."""
    
    print("🤖 SimpleCrawler MK4 - LLM Training Data Generator Demo")
    print("=" * 60)
    
    generator = LLMTrainingDataGenerator()
    
    # Define source collections for different types of training data
    python_docs_sources = [
        {
            'name': 'Python Official Tutorial',
            'url': 'https://docs.python.org/3/tutorial/',
            'category': 'programming_tutorial',
            'domain_type': 'documentation',
            'max_pages': 50,
            'max_depth': 3
        },
        {
            'name': 'Python Standard Library',
            'url': 'https://docs.python.org/3/library/',
            'category': 'programming_reference',
            'domain_type': 'documentation', 
            'max_pages': 100,
            'max_depth': 2
        }
    ]
    
    web_dev_sources = [
        {
            'name': 'FastAPI Documentation',
            'url': 'https://fastapi.tiangolo.com/',
            'category': 'web_framework',
            'domain_type': 'documentation',
            'max_pages': 75,
            'max_depth': 3
        },
        {
            'name': 'Django Documentation',
            'url': 'https://docs.djangoproject.com/en/stable/',
            'category': 'web_framework',
            'domain_type': 'documentation',
            'max_pages': 100,
            'max_depth': 2
        }
    ]
    
    # Create training datasets
    datasets_to_create = [
        ("Python Programming Dataset", python_docs_sources),
        ("Web Development Dataset", web_dev_sources)
    ]
    
    for dataset_name, sources in datasets_to_create:
        print(f"\n🎯 Creating: {dataset_name}")
        print("-" * 50)
        
        try:
            dataset = await generator.create_training_dataset(
                dataset_name=dataset_name,
                sources=sources,
                quality_threshold=0.75,
                max_words_per_example=1500,
                min_words_per_example=100
            )
            
            # Export dataset
            output_dir = f"./training_datasets/{dataset_name.replace(' ', '_').lower()}"
            export_files = generator.export_dataset(
                dataset,
                output_dir,
                formats=['jsonl', 'json', 'txt']
            )
            
            print(f"\n💾 Dataset exported:")
            for fmt, filepath in export_files.items():
                print(f"   {fmt.upper()}: {filepath}")
            
        except Exception as e:
            print(f"❌ Failed to create dataset: {e}")
    
    print(f"\n🎉 Demo completed!")
    print(f"   📦 Created {len(generator.datasets)} training datasets")
    
    # Show summary statistics
    if generator.datasets:
        total_examples = sum(len(ds.examples) for ds in generator.datasets)
        total_words = sum(ds.total_words for ds in generator.datasets)
        
        print(f"   📊 Total examples: {total_examples:,}")
        print(f"   📝 Total words: {total_words:,}")
        print(f"   💾 Average words per example: {total_words/total_examples:.0f}")


if __name__ == "__main__":
    asyncio.run(demo_training_data_generator())