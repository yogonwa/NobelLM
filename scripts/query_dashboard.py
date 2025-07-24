#!/usr/bin/env python3
"""
NobelLM Production Query Dashboard

Simple dashboard showing key metrics and recent activity.
"""

import subprocess
import re
import json
from datetime import datetime, timedelta
from collections import Counter
from typing import Dict, List, Any

def get_fly_logs(app_name: str = "nobellm-api") -> List[str]:
    """Get recent logs from Fly.io."""
    try:
        cmd = ["fly", "logs", "--app", app_name, "-n"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
    except Exception as e:
        print(f"Error fetching logs: {e}")
    return []

def parse_queries_from_logs(log_lines: List[str]) -> List[Dict[str, Any]]:
    """Parse query information from log lines."""
    queries = []
    current_query = None
    
    query_pattern = r'Processing query: \'(.*?)\'\.\.\.'
    completion_pattern = r'Query completed successfully.*?chunk_count": (\d+).*?completion_tokens": (\d+)'
    intent_pattern = r'intent": "(\w+)"'
    error_pattern = r'Query processing failed: (.*)'
    
    for line in log_lines:
        if not line.startswith('20'):
            continue
            
        # Parse timestamp
        try:
            timestamp_str = line[:19]
            timestamp = datetime.fromisoformat(timestamp_str.replace('T', ' '))
        except:
            continue
        
        # Extract query start
        query_match = re.search(query_pattern, line)
        if query_match:
            current_query = {
                'timestamp': timestamp,
                'query': query_match.group(1),
                'status': 'started'
            }
            continue
        
        # Extract completion
        if current_query and 'Query completed successfully' in line:
            completion_match = re.search(completion_pattern, line)
            intent_match = re.search(intent_pattern, line)
            
            if completion_match:
                current_query.update({
                    'chunk_count': int(completion_match.group(1)),
                    'completion_tokens': int(completion_match.group(2)),
                    'status': 'completed'
                })
            
            if intent_match:
                current_query['intent'] = intent_match.group(1)
            
            queries.append(current_query)
            current_query = None
            continue
        
        # Extract error
        if current_query and 'Query processing failed' in line:
            error_match = re.search(error_pattern, line)
            if error_match:
                current_query.update({
                    'error': error_match.group(1),
                    'status': 'failed'
                })
            queries.append(current_query)
            current_query = None
    
    return queries

def calculate_metrics(queries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate key metrics from queries."""
    if not queries:
        return {}
    
    # Filter to last 24 hours
    cutoff = datetime.now() - timedelta(hours=24)
    recent_queries = [q for q in queries if q['timestamp'] > cutoff]
    
    completed = [q for q in recent_queries if q.get('status') == 'completed']
    failed = [q for q in recent_queries if q.get('status') == 'failed']
    
    # Performance metrics
    chunk_counts = [q.get('chunk_count', 0) for q in completed if q.get('chunk_count')]
    token_counts = [q.get('completion_tokens', 0) for q in completed if q.get('completion_tokens')]
    
    # Intent analysis
    intents = [q.get('intent') for q in completed if q.get('intent')]
    intent_counts = Counter(intents)
    
    # Query patterns
    query_words = []
    for q in recent_queries:
        query_words.extend(q.get('query', '').lower().split())
    word_counts = Counter(query_words)
    
    return {
        'total_24h': len(recent_queries),
        'completed_24h': len(completed),
        'failed_24h': len(failed),
        'success_rate': len(completed) / len(recent_queries) if recent_queries else 0,
        'avg_chunks': sum(chunk_counts) / len(chunk_counts) if chunk_counts else 0,
        'avg_tokens': sum(token_counts) / len(token_counts) if token_counts else 0,
        'intents': dict(intent_counts),
        'common_words': dict(word_counts.most_common(10)),
        'recent_queries': recent_queries[-10:]  # Last 10 queries
    }

def print_dashboard(metrics: Dict[str, Any]):
    """Print formatted dashboard."""
    print("\n" + "="*60)
    print("🎯 NobelLM Production Dashboard")
    print("="*60)
    
    # 24-hour summary
    print(f"\n📊 LAST 24 HOURS")
    print(f"   Total Queries: {metrics.get('total_24h', 0)}")
    print(f"   Completed: {metrics.get('completed_24h', 0)}")
    print(f"   Failed: {metrics.get('failed_24h', 0)}")
    print(f"   Success Rate: {metrics.get('success_rate', 0):.1%}")
    
    # Performance
    print(f"\n⚡ PERFORMANCE")
    print(f"   Avg Chunks Retrieved: {metrics.get('avg_chunks', 0):.1f}")
    print(f"   Avg Completion Tokens: {metrics.get('avg_tokens', 0):.1f}")
    
    # Intent breakdown
    intents = metrics.get('intents', {})
    if intents:
        print(f"\n🎯 QUERY INTENTS")
        for intent, count in sorted(intents.items(), key=lambda x: x[1], reverse=True):
            print(f"   {intent}: {count}")
    
    # Common words
    words = metrics.get('common_words', {})
    if words:
        print(f"\n🔤 COMMON WORDS")
        for word, count in list(words.items())[:5]:
            if len(word) > 2:
                print(f"   '{word}': {count}")
    
    # Recent queries
    recent = metrics.get('recent_queries', [])
    if recent:
        print(f"\n🕒 RECENT QUERIES")
        for i, query in enumerate(recent[-5:], 1):  # Last 5
            status_emoji = "✅" if query.get('status') == 'completed' else "❌" if query.get('status') == 'failed' else "⏳"
            timestamp = query.get('timestamp', 'N/A')
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime("%H:%M")
            print(f"   {i}. {status_emoji} {query.get('query', 'N/A')[:50]}...")
            print(f"      {timestamp} | {query.get('intent', 'N/A')}")

def main():
    print("🔄 Fetching production data...")
    
    # Get logs
    log_lines = get_fly_logs()
    if not log_lines:
        print("❌ No logs found. Check if the app is running.")
        return
    
    # Parse queries
    queries = parse_queries_from_logs(log_lines)
    if not queries:
        print("❌ No queries found in logs.")
        return
    
    # Calculate metrics
    metrics = calculate_metrics(queries)
    
    # Print dashboard
    print_dashboard(metrics)
    
    # Save detailed data
    output_file = f"dashboard_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"\n💾 Detailed data saved to: {output_file}")

if __name__ == "__main__":
    main() 