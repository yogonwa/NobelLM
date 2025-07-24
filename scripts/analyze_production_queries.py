#!/usr/bin/env python3
"""
Production Query Analysis Script for NobelLM

This script provides comprehensive analysis of production queries and RAG responses
from multiple sources:
- Fly.io application logs
- Local query logs (data/query_log.tsv)
- Cost logs (if available)
- Real-time log streaming

Usage:
    python scripts/analyze_production_queries.py --help
    python scripts/analyze_production_queries.py --recent 24h
    python scripts/analyze_production_queries.py --stream
    python scripts/analyze_production_queries.py --analyze --since 2025-07-24
"""

import argparse
import json
import logging
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
from collections import defaultdict, Counter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionQueryAnalyzer:
    """Analyze production queries and RAG responses from multiple sources."""
    
    def __init__(self, app_name: str = "nobellm-api"):
        self.app_name = app_name
        self.project_root = Path(__file__).parent.parent
        
    def get_fly_logs(self, hours: Optional[int] = None, follow: bool = False) -> List[str]:
        """Fetch logs from Fly.io application."""
        cmd = ["fly", "logs", "--app", self.app_name, "-n"]
        
        if hours:
            # Fly.io doesn't have a direct time filter, so we'll filter in Python
            logger.info(f"Fetching logs for the last {hours} hours...")
        if follow:
            cmd.append("--follow")
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
            else:
                logger.error(f"Failed to fetch Fly logs: {result.stderr}")
                return []
        except subprocess.TimeoutExpired:
            logger.error("Timeout fetching Fly logs")
            return []
        except Exception as e:
            logger.error(f"Error fetching Fly logs: {e}")
            return []
    
    def parse_fly_logs(self, log_lines: List[str], since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Parse Fly.io logs to extract query information."""
        parsed_queries = []
        
        # Regex patterns for different log types
        query_pattern = r'Processing query: \'(.*?)\'\.\.\.'
        completion_pattern = r'Query completed successfully.*?chunk_count": (\d+).*?completion_tokens": (\d+)'
        intent_pattern = r'intent": "(\w+)"'
        score_pattern = r'mean_score": "float64"'
        error_pattern = r'Query processing failed: (.*)'
        
        current_query = None
        
        for line in log_lines:
            # Skip lines without timestamp
            if not line.startswith('20'):
                continue
                
            # Parse timestamp
            try:
                timestamp_str = line[:19]  # YYYY-MM-DDTHH:MM:SS
                timestamp = datetime.fromisoformat(timestamp_str.replace('T', ' '))
                
                if since and timestamp < since:
                    continue
            except:
                continue
            
            # Extract query start
            query_match = re.search(query_pattern, line)
            if query_match:
                current_query = {
                    'timestamp': timestamp,
                    'query': query_match.group(1),
                    'source': 'fly_logs',
                    'status': 'started'
                }
                continue
            
            # Extract completion info
            if current_query and 'Query completed successfully' in line:
                completion_match = re.search(completion_pattern, line)
                if completion_match:
                    current_query.update({
                        'chunk_count': int(completion_match.group(1)),
                        'completion_tokens': int(completion_match.group(2)),
                        'status': 'completed'
                    })
                
                # Extract intent
                intent_match = re.search(intent_pattern, line)
                if intent_match:
                    current_query['intent'] = intent_match.group(1)
                
                parsed_queries.append(current_query)
                current_query = None
                continue
            
            # Extract error info
            if current_query and 'Query processing failed' in line:
                error_match = re.search(error_pattern, line)
                if error_match:
                    current_query.update({
                        'error': error_match.group(1),
                        'status': 'failed'
                    })
                parsed_queries.append(current_query)
                current_query = None
        
        return parsed_queries
    
    def parse_query_log(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Parse local query log file."""
        query_log_path = self.project_root / "data" / "query_log.tsv"
        queries = []
        
        if not query_log_path.exists():
            logger.warning(f"Query log file not found: {query_log_path}")
            return queries
        
        try:
            with open(query_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        timestamp_str, source, query = parts[:3]
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str)
                            if since and timestamp < since:
                                continue
                            
                            queries.append({
                                'timestamp': timestamp,
                                'query': query,
                                'source': source,
                                'status': 'logged'
                            })
                        except ValueError:
                            continue
        except Exception as e:
            logger.error(f"Error reading query log: {e}")
        
        return queries
    
    def analyze_queries(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze query patterns and statistics."""
        if not queries:
            return {}
        
        # Basic statistics
        total_queries = len(queries)
        completed_queries = [q for q in queries if q.get('status') == 'completed']
        failed_queries = [q for q in queries if q.get('status') == 'failed']
        
        # Query length analysis
        query_lengths = [len(q.get('query', '')) for q in queries]
        
        # Intent analysis
        intents = [q.get('intent') for q in completed_queries if q.get('intent')]
        intent_counts = Counter(intents)
        
        # Performance analysis
        chunk_counts = [q.get('chunk_count', 0) for q in completed_queries if q.get('chunk_count')]
        token_counts = [q.get('completion_tokens', 0) for q in completed_queries if q.get('completion_tokens')]
        
        # Time-based analysis
        timestamps = [q['timestamp'] for q in queries]
        if timestamps:
            time_range = max(timestamps) - min(timestamps)
            queries_per_hour = total_queries / (time_range.total_seconds() / 3600) if time_range.total_seconds() > 0 else 0
        else:
            time_range = timedelta(0)
            queries_per_hour = 0
        
        # Common query patterns
        query_words = []
        for q in queries:
            query_words.extend(q.get('query', '').lower().split())
        word_counts = Counter(query_words)
        
        return {
            'summary': {
                'total_queries': total_queries,
                'completed_queries': len(completed_queries),
                'failed_queries': len(failed_queries),
                'success_rate': len(completed_queries) / total_queries if total_queries > 0 else 0,
                'time_range': str(time_range),
                'queries_per_hour': round(queries_per_hour, 2)
            },
            'performance': {
                'avg_query_length': round(sum(query_lengths) / len(query_lengths), 1) if query_lengths else 0,
                'avg_chunks_retrieved': round(sum(chunk_counts) / len(chunk_counts), 1) if chunk_counts else 0,
                'avg_completion_tokens': round(sum(token_counts) / len(token_counts), 1) if token_counts else 0,
                'max_chunks_retrieved': max(chunk_counts) if chunk_counts else 0,
                'max_completion_tokens': max(token_counts) if token_counts else 0
            },
            'intents': dict(intent_counts),
            'common_words': dict(word_counts.most_common(20)),
            'recent_queries': [q for q in sorted(queries, key=lambda x: x['timestamp'], reverse=True)[:10]]
        }
    
    def print_analysis(self, analysis: Dict[str, Any]):
        """Print formatted analysis results."""
        if not analysis:
            print("No data to analyze.")
            return
        
        print("\n" + "="*60)
        print("NobelLM Production Query Analysis")
        print("="*60)
        
        # Summary
        summary = analysis.get('summary', {})
        print(f"\n📊 SUMMARY")
        print(f"   Total Queries: {summary.get('total_queries', 0)}")
        print(f"   Completed: {summary.get('completed_queries', 0)}")
        print(f"   Failed: {summary.get('failed_queries', 0)}")
        print(f"   Success Rate: {summary.get('success_rate', 0):.1%}")
        print(f"   Time Range: {summary.get('time_range', 'N/A')}")
        print(f"   Queries/Hour: {summary.get('queries_per_hour', 0)}")
        
        # Performance
        perf = analysis.get('performance', {})
        print(f"\n⚡ PERFORMANCE")
        print(f"   Avg Query Length: {perf.get('avg_query_length', 0)} chars")
        print(f"   Avg Chunks Retrieved: {perf.get('avg_chunks_retrieved', 0)}")
        print(f"   Avg Completion Tokens: {perf.get('avg_completion_tokens', 0)}")
        print(f"   Max Chunks: {perf.get('max_chunks_retrieved', 0)}")
        print(f"   Max Tokens: {perf.get('max_completion_tokens', 0)}")
        
        # Intents
        intents = analysis.get('intents', {})
        if intents:
            print(f"\n🎯 QUERY INTENTS")
            for intent, count in sorted(intents.items(), key=lambda x: x[1], reverse=True):
                print(f"   {intent}: {count}")
        
        # Common words
        words = analysis.get('common_words', {})
        if words:
            print(f"\n🔤 COMMON WORDS")
            for word, count in list(words.items())[:10]:
                if len(word) > 2:  # Skip short words
                    print(f"   '{word}': {count}")
        
        # Recent queries
        recent = analysis.get('recent_queries', [])
        if recent:
            print(f"\n🕒 RECENT QUERIES")
            for i, query in enumerate(recent[:5], 1):
                status_emoji = "✅" if query.get('status') == 'completed' else "❌" if query.get('status') == 'failed' else "📝"
                print(f"   {i}. {status_emoji} {query.get('query', 'N/A')[:60]}...")
                print(f"      {query.get('timestamp', 'N/A')} | {query.get('source', 'N/A')}")
    
    def stream_logs(self):
        """Stream real-time logs from Fly.io."""
        print("🔴 Streaming live logs from Fly.io... (Press Ctrl+C to stop)")
        print("-" * 60)
        
        try:
            cmd = ["fly", "logs", "--app", self.app_name, "--follow"]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            query_pattern = r'Processing query: \'(.*?)\'\.\.\.'
            completion_pattern = r'Query completed successfully.*?chunk_count": (\d+).*?completion_tokens": (\d+)'
            
            current_query = None
            
            for line in iter(process.stdout.readline, ''):
                if not line:
                    continue
                
                # Check for new query
                query_match = re.search(query_pattern, line)
                if query_match:
                    current_query = query_match.group(1)
                    print(f"\n🔍 NEW QUERY: {current_query}")
                    continue
                
                # Check for completion
                if current_query and 'Query completed successfully' in line:
                    completion_match = re.search(completion_pattern, line)
                    if completion_match:
                        chunks = completion_match.group(1)
                        tokens = completion_match.group(2)
                        print(f"✅ COMPLETED: {chunks} chunks, {tokens} tokens")
                    current_query = None
                    continue
                
                # Check for errors
                if current_query and 'Query processing failed' in line:
                    print(f"❌ FAILED: {current_query}")
                    current_query = None
                    continue
                
                # Print other relevant lines
                if any(keyword in line for keyword in ['intent', 'chunk_count', 'completion_tokens', 'error']):
                    print(f"   {line.strip()}")
                    
        except KeyboardInterrupt:
            print("\n🛑 Stopping log stream...")
            process.terminate()
        except Exception as e:
            logger.error(f"Error streaming logs: {e}")

def main():
    parser = argparse.ArgumentParser(description="Analyze NobelLM production queries")
    parser.add_argument("--recent", type=str, help="Analyze recent logs (e.g., '24h', '7d')")
    parser.add_argument("--since", type=str, help="Analyze since date (YYYY-MM-DD)")
    parser.add_argument("--stream", action="store_true", help="Stream live logs")
    parser.add_argument("--analyze", action="store_true", help="Perform detailed analysis")
    parser.add_argument("--app", type=str, default="nobellm-api", help="Fly.io app name")
    
    args = parser.parse_args()
    
    analyzer = ProductionQueryAnalyzer(args.app)
    
    if args.stream:
        analyzer.stream_logs()
        return
    
    # Determine time range
    since = None
    if args.since:
        try:
            since = datetime.fromisoformat(args.since)
        except ValueError:
            logger.error(f"Invalid date format: {args.since}. Use YYYY-MM-DD")
            return
    
    if args.recent:
        try:
            hours = int(args.recent.replace('h', ''))
            since = datetime.now() - timedelta(hours=hours)
        except ValueError:
            logger.error(f"Invalid time format: {args.recent}. Use '24h', '7d', etc.")
            return
    
    # Collect data
    print("📊 Collecting production query data...")
    
    # Get Fly.io logs
    fly_logs = analyzer.get_fly_logs()
    fly_queries = analyzer.parse_fly_logs(fly_logs, since)
    
    # Get local query logs
    local_queries = analyzer.parse_query_log(since)
    
    # Combine all queries
    all_queries = fly_queries + local_queries
    
    if not all_queries:
        print("No queries found in the specified time range.")
        return
    
    print(f"Found {len(all_queries)} queries")
    
    # Analyze
    if args.analyze or not args.stream:
        analysis = analyzer.analyze_queries(all_queries)
        analyzer.print_analysis(analysis)
    
    # Save detailed results
    if args.analyze:
        output_file = f"query_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        print(f"\n💾 Detailed analysis saved to: {output_file}")

if __name__ == "__main__":
    main() 