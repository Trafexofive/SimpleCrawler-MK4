#!/usr/bin/env python3
"""
Validate code extraction quality and markdown formatting.
"""

import re
from pathlib import Path

def analyze_markdown_file(file_path: Path):
    """Analyze a markdown file for code extraction quality."""
    if not file_path.exists():
        return None
    
    content = file_path.read_text(encoding='utf-8')
    
    # Count different code elements
    code_blocks = len(re.findall(r'```[\s\S]*?```', content, re.MULTILINE))
    inline_code = len(re.findall(r'`[^`\n]+`', content))
    
    # Find languages in code blocks
    languages = re.findall(r'```(\w+)', content)
    language_counts = {}
    for lang in languages:
        language_counts[lang] = language_counts.get(lang, 0) + 1
    
    # Check for common issues
    issues = []
    
    # Unclosed code blocks
    open_blocks = content.count('```')
    if open_blocks % 2 != 0:
        issues.append(f"Unclosed code blocks (found {open_blocks} ``` markers)")
    
    # Empty code blocks
    empty_blocks = len(re.findall(r'```\s*\n\s*```', content, re.MULTILINE))
    if empty_blocks > 0:
        issues.append(f"{empty_blocks} empty code blocks")
    
    # Malformed code blocks (common issue)
    malformed = len(re.findall(r'```.*```.*```', content, re.DOTALL))
    if malformed > 0:
        issues.append(f"Possible malformed code blocks: {malformed}")
    
    return {
        'file_size': len(content),
        'code_blocks': code_blocks,
        'inline_code': inline_code,
        'languages': language_counts,
        'issues': issues,
        'sample_blocks': extract_sample_blocks(content)
    }

def extract_sample_blocks(content: str, max_samples: int = 3):
    """Extract sample code blocks for display."""
    blocks = re.findall(r'```[\s\S]*?```', content, re.MULTILINE)
    
    samples = []
    for block in blocks[:max_samples]:
        lines = block.split('\n')
        if len(lines) > 10:
            # Truncate long blocks
            sample = '\n'.join(lines[:8]) + '\n... (truncated)'
        else:
            sample = block
        samples.append(sample)
    
    return samples

def main():
    """Run validation on extracted code."""
    print("🔍 Code Extraction Quality Validation")
    print("=" * 50)
    
    # Check the test output directory
    test_dir = Path('code_test_output')
    if not test_dir.exists():
        print("❌ No test output directory found")
        return
    
    # Find all markdown files
    md_files = list(test_dir.rglob('*.md'))
    
    if not md_files:
        print("❌ No markdown files found")
        return
    
    print(f"📄 Found {len(md_files)} markdown files")
    print()
    
    total_code_blocks = 0
    total_inline_code = 0
    all_languages = {}
    all_issues = []
    
    for md_file in md_files:
        site_name = md_file.parent.name
        analysis = analyze_markdown_file(md_file)
        
        if analysis:
            print(f"📋 {site_name}")
            print(f"   📄 File: {md_file.name}")
            print(f"   📊 Size: {analysis['file_size']:,} bytes")
            print(f"   💻 Code blocks: {analysis['code_blocks']}")
            print(f"   📝 Inline code: {analysis['inline_code']}")
            
            if analysis['languages']:
                print(f"   🔤 Languages: {', '.join(f'{lang}({count})' for lang, count in analysis['languages'].items())}")
            
            if analysis['issues']:
                print(f"   ⚠️  Issues: {len(analysis['issues'])}")
                for issue in analysis['issues'][:2]:  # Show first 2 issues
                    print(f"      - {issue}")
            else:
                print(f"   ✅ No issues found")
            
            # Show a sample code block
            if analysis['sample_blocks']:
                print(f"   🔍 Sample code block:")
                sample = analysis['sample_blocks'][0]
                lines = sample.split('\n')
                for line in lines[:6]:  # Show first 6 lines
                    print(f"      {line}")
                if len(lines) > 6:
                    print(f"      ... ({len(lines) - 6} more lines)")
            
            print()
            
            # Accumulate totals
            total_code_blocks += analysis['code_blocks']
            total_inline_code += analysis['inline_code']
            
            for lang, count in analysis['languages'].items():
                all_languages[lang] = all_languages.get(lang, 0) + count
            
            all_issues.extend(analysis['issues'])
    
    # Summary
    print("📊 SUMMARY")
    print("=" * 30)
    print(f"📄 Files analyzed: {len(md_files)}")
    print(f"💻 Total code blocks: {total_code_blocks}")
    print(f"📝 Total inline code: {total_inline_code}")
    print(f"🔤 Programming languages detected: {len(all_languages)}")
    
    if all_languages:
        print("   Language breakdown:")
        for lang, count in sorted(all_languages.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {lang}: {count} blocks")
    
    print(f"⚠️  Total issues: {len(all_issues)}")
    
    if len(all_issues) == 0:
        print("✅ EXCELLENT: All markdown files have valid code block formatting!")
    elif len(all_issues) < total_code_blocks * 0.1:  # Less than 10% issues
        print("✅ GOOD: Minor formatting issues, mostly valid")
    else:
        print("⚠️  NEEDS IMPROVEMENT: Significant formatting issues found")
    
    # Quality score
    if total_code_blocks > 0:
        quality_score = max(0, 100 - (len(all_issues) / total_code_blocks * 100))
        print(f"📈 Quality Score: {quality_score:.1f}%")
    
    print(f"\n🎯 Code extraction is {'WORKING WELL' if len(all_issues) < 10 else 'NEEDS FIXES'}")

if __name__ == "__main__":
    main()