#!/usr/bin/env python3
"""
Comprehensive Audit Log Analysis for NobelLM

This script analyzes audit logs to provide detailed insights into:
- User query patterns and intents
- Keyword expansion effectiveness
- Retrieval performance and chunk quality
- Prompt construction and LLM interactions
- Cost analysis and performance metrics
- Error patterns and debugging information

Usage:
    python scripts/analyze_audit_logs.py --help
    python scripts/analyze_audit_logs.py --recent 24h
    python scripts/analyze_audit_logs.py --query "specific query text"
    python scripts/analyze_audit_logs.py --export --since 2025-07-24
"""

import argparse
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import Counter, defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AuditLogAnalyzer:
    """Analyze NobelLM audit logs for comprehensive insights."""
    
    def __init__(self, log_dir: str = "logs/audit"):
        self.log_dir = Path(log_dir)
        self.audit_logs = []
    
    def load_audit_logs(self, since: Optional[datetime] = None, hours: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load audit logs from JSONL files."""
        if hours:
            since = datetime.utcnow() - timedelta(hours=hours)
        
        audit_logs = []
        
        # Read all audit files
        for log_file in self.log_dir.glob("audit_log_*.jsonl"):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            audit_data = json.loads(line.strip())
                            
                            # Filter by time if specified
                            if since:
                                audit_time = datetime.fromisoformat(audit_data["timestamp"].replace("Z", "+00:00"))
                                if audit_time < since:
                                    continue
                            
                            audit_logs.append(audit_data)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.error(f"Error reading audit file {log_file}: {e}")
        
        self.audit_logs = audit_logs
        logger.info(f"Loaded {len(audit_logs)} audit log entries")
        return audit_logs
    
    def filter_by_query(self, query_text: str) -> List[Dict[str, Any]]:
        """Filter audit logs by specific query text."""
        filtered = []
        query_lower = query_text.lower()
        
        for audit in self.audit_logs:
            if query_lower in audit.get("user_query", "").lower():
                filtered.append(audit)
        
        return filtered
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get comprehensive summary statistics."""
        if not self.audit_logs:
            return {"error": "No audit logs found"}
        
        total_queries = len(self.audit_logs)
        successful_queries = len([a for a in self.audit_logs if not a.get("error_occurred", False)])
        failed_queries = total_queries - successful_queries
        
        # Intent distribution
        intents = [a.get("intent") for a in self.audit_logs if a.get("intent")]
        intent_counts = Counter(intents)
        
        # Performance metrics
        processing_times = [a.get("total_processing_time_ms") for a in self.audit_logs if a.get("total_processing_time_ms")]
        retrieval_times = [a.get("retrieval_time_ms") for a in self.audit_logs if a.get("retrieval_time_ms")]
        llm_times = [a.get("llm_time_ms") for a in self.audit_logs if a.get("llm_time_ms")]
        
        # Cost analysis
        total_cost = sum([a.get("estimated_cost_usd", 0) for a in self.audit_logs])
        total_tokens = sum([a.get("total_tokens", 0) for a in self.audit_logs])
        
        # Chunk analysis
        chunk_counts = [a.get("chunk_count", 0) for a in self.audit_logs if a.get("chunk_count")]
        
        # Keyword expansion analysis
        expanded_queries = [a for a in self.audit_logs if a.get("expanded_terms")]
        
        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "failed_queries": failed_queries,
            "success_rate": successful_queries / total_queries if total_queries > 0 else 0,
            "intent_distribution": dict(intent_counts),
            "performance": {
                "avg_processing_time_ms": sum(processing_times) / len(processing_times) if processing_times else 0,
                "avg_retrieval_time_ms": sum(retrieval_times) / len(retrieval_times) if retrieval_times else 0,
                "avg_llm_time_ms": sum(llm_times) / len(llm_times) if llm_times else 0,
                "min_processing_time_ms": min(processing_times) if processing_times else 0,
                "max_processing_time_ms": max(processing_times) if processing_times else 0,
            },
            "cost_analysis": {
                "total_cost_usd": total_cost,
                "avg_cost_per_query": total_cost / total_queries if total_queries > 0 else 0,
                "total_tokens": total_tokens,
                "avg_tokens_per_query": total_tokens / total_queries if total_queries > 0 else 0,
            },
            "retrieval_analysis": {
                "avg_chunks_retrieved": sum(chunk_counts) / len(chunk_counts) if chunk_counts else 0,
                "queries_with_expansion": len(expanded_queries),
                "expansion_rate": len(expanded_queries) / total_queries if total_queries > 0 else 0,
            }
        }
    
    def analyze_keyword_expansion(self) -> Dict[str, Any]:
        """Analyze keyword expansion effectiveness."""
        expanded_queries = [a for a in self.audit_logs if a.get("expanded_terms")]
        
        if not expanded_queries:
            return {"message": "No keyword expansion data found"}
        
        # Analyze expansion patterns
        all_expanded_terms = []
        term_frequencies = Counter()
        
        for audit in expanded_queries:
            terms = audit.get("expanded_terms", [])
            all_expanded_terms.extend(terms)
            term_frequencies.update(terms)
        
        # Analyze expansion effectiveness
        expansion_effectiveness = []
        for audit in expanded_queries:
            if audit.get("chunk_count") and audit.get("retrieval_scores"):
                avg_score = sum(audit["retrieval_scores"]) / len(audit["retrieval_scores"])
                expansion_effectiveness.append({
                    "query": audit.get("user_query"),
                    "expanded_terms": audit.get("expanded_terms"),
                    "chunk_count": audit.get("chunk_count"),
                    "avg_retrieval_score": avg_score,
                    "processing_time_ms": audit.get("total_processing_time_ms")
                })
        
        return {
            "total_expanded_queries": len(expanded_queries),
            "total_expanded_terms": len(all_expanded_terms),
            "avg_terms_per_expansion": len(all_expanded_terms) / len(expanded_queries) if expanded_queries else 0,
            "most_common_expanded_terms": dict(term_frequencies.most_common(20)),
            "expansion_effectiveness": expansion_effectiveness
        }
    
    def analyze_prompt_construction(self) -> Dict[str, Any]:
        """Analyze prompt construction patterns."""
        prompts = [a for a in self.audit_logs if a.get("final_prompt")]
        
        if not prompts:
            return {"message": "No prompt data found"}
        
        prompt_lengths = [a.get("prompt_length", 0) for a in prompts]
        context_lengths = [a.get("context_length", 0) for a in prompts if a.get("context_length")]
        
        # Analyze prompt templates
        templates = [a.get("prompt_template") for a in prompts if a.get("prompt_template")]
        template_counts = Counter(templates)
        
        return {
            "total_prompts": len(prompts),
            "avg_prompt_length": sum(prompt_lengths) / len(prompt_lengths) if prompt_lengths else 0,
            "avg_context_length": sum(context_lengths) / len(context_lengths) if context_lengths else 0,
            "min_prompt_length": min(prompt_lengths) if prompt_lengths else 0,
            "max_prompt_length": max(prompt_lengths) if prompt_lengths else 0,
            "template_usage": dict(template_counts)
        }
    
    def analyze_llm_interactions(self) -> Dict[str, Any]:
        """Analyze LLM interaction patterns."""
        llm_interactions = [a for a in self.audit_logs if a.get("llm_response")]
        
        if not llm_interactions:
            return {"message": "No LLM interaction data found"}
        
        # Token analysis
        prompt_tokens = [a.get("prompt_tokens", 0) for a in llm_interactions]
        completion_tokens = [a.get("completion_tokens", 0) for a in llm_interactions]
        total_tokens = [a.get("total_tokens", 0) for a in llm_interactions]
        
        # Cost analysis
        costs = [a.get("estimated_cost_usd", 0) for a in llm_interactions]
        
        # Response analysis
        response_lengths = [len(a.get("llm_response", "")) for a in llm_interactions]
        
        return {
            "total_llm_interactions": len(llm_interactions),
            "token_analysis": {
                "avg_prompt_tokens": sum(prompt_tokens) / len(prompt_tokens) if prompt_tokens else 0,
                "avg_completion_tokens": sum(completion_tokens) / len(completion_tokens) if completion_tokens else 0,
                "avg_total_tokens": sum(total_tokens) / len(total_tokens) if total_tokens else 0,
                "max_prompt_tokens": max(prompt_tokens) if prompt_tokens else 0,
                "max_completion_tokens": max(completion_tokens) if completion_tokens else 0,
            },
            "cost_analysis": {
                "total_cost_usd": sum(costs),
                "avg_cost_per_interaction": sum(costs) / len(costs) if costs else 0,
                "max_cost_per_interaction": max(costs) if costs else 0,
            },
            "response_analysis": {
                "avg_response_length": sum(response_lengths) / len(response_lengths) if response_lengths else 0,
                "min_response_length": min(response_lengths) if response_lengths else 0,
                "max_response_length": max(response_lengths) if response_lengths else 0,
            }
        }
    
    def analyze_errors(self) -> Dict[str, Any]:
        """Analyze error patterns."""
        errors = [a for a in self.audit_logs if a.get("error_occurred", False)]
        
        if not errors:
            return {"message": "No errors found in audit logs"}
        
        error_types = [a.get("error_type") for a in errors if a.get("error_type")]
        error_counts = Counter(error_types)
        
        # Error details
        error_details = []
        for audit in errors:
            error_details.append({
                "query": audit.get("user_query"),
                "error_type": audit.get("error_type"),
                "error_message": audit.get("error_message"),
                "timestamp": audit.get("timestamp")
            })
        
        return {
            "total_errors": len(errors),
            "error_rate": len(errors) / len(self.audit_logs) if self.audit_logs else 0,
            "error_type_distribution": dict(error_counts),
            "error_details": error_details
        }
    
    def get_query_details(self, query_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific query."""
        for audit in self.audit_logs:
            if audit.get("query_id") == query_id:
                return audit
        return None
    
    def export_to_csv(self, output_file: str = "audit_analysis.csv"):
        """Export audit data to CSV for further analysis."""
        if not self.audit_logs:
            logger.warning("No audit logs to export")
            return
        
        # Create DataFrame
        df_data = []
        for audit in self.audit_logs:
            row = {
                "query_id": audit.get("query_id"),
                "timestamp": audit.get("timestamp"),
                "user_query": audit.get("user_query"),
                "intent": audit.get("intent"),
                "confidence": audit.get("confidence"),
                "chunk_count": audit.get("chunk_count"),
                "prompt_length": audit.get("prompt_length"),
                "total_tokens": audit.get("total_tokens"),
                "estimated_cost_usd": audit.get("estimated_cost_usd"),
                "total_processing_time_ms": audit.get("total_processing_time_ms"),
                "error_occurred": audit.get("error_occurred", False),
                "error_type": audit.get("error_type"),
                "answer_length": audit.get("answer_length"),
            }
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        df.to_csv(output_file, index=False)
        logger.info(f"Exported {len(df_data)} audit records to {output_file}")
    
    def print_comprehensive_analysis(self):
        """Print comprehensive analysis of audit logs."""
        print("\n" + "="*80)
        print("🎯 NobelLM Comprehensive Audit Analysis")
        print("="*80)
        
        # Summary statistics
        summary = self.get_summary_statistics()
        if "error" in summary:
            print(f"❌ {summary['error']}")
            return
        
        print(f"\n📊 SUMMARY STATISTICS")
        print(f"   Total Queries: {summary['total_queries']}")
        print(f"   Successful: {summary['successful_queries']}")
        print(f"   Failed: {summary['failed_queries']}")
        print(f"   Success Rate: {summary['success_rate']:.1%}")
        
        # Intent distribution
        print(f"\n🎯 INTENT DISTRIBUTION")
        for intent, count in sorted(summary['intent_distribution'].items(), key=lambda x: x[1], reverse=True):
            print(f"   {intent}: {count}")
        
        # Performance metrics
        perf = summary['performance']
        print(f"\n⚡ PERFORMANCE METRICS")
        print(f"   Avg Processing Time: {perf['avg_processing_time_ms']:.1f}ms")
        print(f"   Avg Retrieval Time: {perf['avg_retrieval_time_ms']:.1f}ms")
        print(f"   Avg LLM Time: {perf['avg_llm_time_ms']:.1f}ms")
        print(f"   Min Processing Time: {perf['min_processing_time_ms']:.1f}ms")
        print(f"   Max Processing Time: {perf['max_processing_time_ms']:.1f}ms")
        
        # Cost analysis
        cost = summary['cost_analysis']
        print(f"\n💰 COST ANALYSIS")
        print(f"   Total Cost: ${cost['total_cost_usd']:.4f}")
        print(f"   Avg Cost per Query: ${cost['avg_cost_per_query']:.4f}")
        print(f"   Total Tokens: {cost['total_tokens']:,}")
        print(f"   Avg Tokens per Query: {cost['avg_tokens_per_query']:.1f}")
        
        # Retrieval analysis
        retrieval = summary['retrieval_analysis']
        print(f"\n🔍 RETRIEVAL ANALYSIS")
        print(f"   Avg Chunks Retrieved: {retrieval['avg_chunks_retrieved']:.1f}")
        print(f"   Queries with Expansion: {retrieval['queries_with_expansion']}")
        print(f"   Expansion Rate: {retrieval['expansion_rate']:.1%}")
        
        # Keyword expansion analysis
        print(f"\n🔤 KEYWORD EXPANSION ANALYSIS")
        expansion = self.analyze_keyword_expansion()
        if "message" not in expansion:
            print(f"   Total Expanded Queries: {expansion['total_expanded_queries']}")
            print(f"   Total Expanded Terms: {expansion['total_expanded_terms']}")
            print(f"   Avg Terms per Expansion: {expansion['avg_terms_per_expansion']:.1f}")
            print(f"   Most Common Terms:")
            for term, count in list(expansion['most_common_expanded_terms'].items())[:10]:
                print(f"     '{term}': {count}")
        
        # Prompt analysis
        print(f"\n📝 PROMPT ANALYSIS")
        prompt_analysis = self.analyze_prompt_construction()
        if "message" not in prompt_analysis:
            print(f"   Total Prompts: {prompt_analysis['total_prompts']}")
            print(f"   Avg Prompt Length: {prompt_analysis['avg_prompt_length']:.0f} chars")
            print(f"   Avg Context Length: {prompt_analysis['avg_context_length']:.0f} chars")
            print(f"   Template Usage:")
            for template, count in prompt_analysis['template_usage'].items():
                print(f"     {template}: {count}")
        
        # LLM analysis
        print(f"\n🤖 LLM INTERACTION ANALYSIS")
        llm_analysis = self.analyze_llm_interactions()
        if "message" not in llm_analysis:
            print(f"   Total LLM Interactions: {llm_analysis['total_llm_interactions']}")
            print(f"   Avg Prompt Tokens: {llm_analysis['token_analysis']['avg_prompt_tokens']:.1f}")
            print(f"   Avg Completion Tokens: {llm_analysis['token_analysis']['avg_completion_tokens']:.1f}")
            print(f"   Avg Response Length: {llm_analysis['response_analysis']['avg_response_length']:.0f} chars")
        
        # Error analysis
        print(f"\n❌ ERROR ANALYSIS")
        error_analysis = self.analyze_errors()
        if "message" not in error_analysis:
            print(f"   Total Errors: {error_analysis['total_errors']}")
            print(f"   Error Rate: {error_analysis['error_rate']:.1%}")
            print(f"   Error Types:")
            for error_type, count in error_analysis['error_type_distribution'].items():
                print(f"     {error_type}: {count}")

def main():
    parser = argparse.ArgumentParser(description="Analyze NobelLM audit logs")
    parser.add_argument("--recent", type=str, help="Analyze recent logs (e.g., '24h', '7d')")
    parser.add_argument("--since", type=str, help="Analyze since date (YYYY-MM-DD)")
    parser.add_argument("--query", type=str, help="Filter by specific query text")
    parser.add_argument("--export", action="store_true", help="Export data to CSV")
    parser.add_argument("--log-dir", type=str, default="logs/audit", help="Audit log directory")
    
    args = parser.parse_args()
    
    analyzer = AuditLogAnalyzer(args.log_dir)
    
    # Load audit logs
    if args.recent:
        try:
            hours = int(args.recent.replace('h', ''))
            analyzer.load_audit_logs(hours=hours)
        except ValueError:
            print(f"Invalid time format: {args.recent}. Use '24h', '7d', etc.")
            return
    elif args.since:
        try:
            since = datetime.fromisoformat(args.since)
            analyzer.load_audit_logs(since=since)
        except ValueError:
            print(f"Invalid date format: {args.since}. Use YYYY-MM-DD")
            return
    else:
        # Default to last 24 hours
        analyzer.load_audit_logs(hours=24)
    
    # Filter by query if specified
    if args.query:
        filtered_logs = analyzer.filter_by_query(args.query)
        if not filtered_logs:
            print(f"No audit logs found for query: {args.query}")
            return
        analyzer.audit_logs = filtered_logs
        print(f"Found {len(filtered_logs)} audit logs for query: {args.query}")
    
    # Export if requested
    if args.export:
        output_file = f"audit_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        analyzer.export_to_csv(output_file)
    
    # Print comprehensive analysis
    analyzer.print_comprehensive_analysis()

if __name__ == "__main__":
    main() 