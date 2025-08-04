#!/usr/bin/env python3
"""
Export Audit Logs to CSV

Simple script to convert audit logs to CSV format for easy analysis in Excel/Sheets.
"""

import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_audit_logs(log_dir: str) -> List[Dict[str, Any]]:
    """Load audit logs from JSONL files."""
    log_path = Path(log_dir)
    audit_logs = []
    
    for log_file in log_path.glob("audit_log_*.jsonl"):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        audit_data = json.loads(line.strip())
                        audit_logs.append(audit_data)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Error reading audit file {log_file}: {e}")
    
    logger.info(f"Loaded {len(audit_logs)} audit log entries")
    return audit_logs

def export_to_csv(audit_logs: List[Dict[str, Any]], output_file: str = "audit_logs.csv"):
    """Export audit logs to CSV format."""
    
    if not audit_logs:
        logger.error("No audit logs to export")
        return
    
    # Define the fields we want to export
    fields = [
        'query_id',
        'timestamp',
        'user_query',
        'intent',
        'confidence',
        'thematic_subtype',
        'subtype_confidence',
        'retrieval_method',
        'top_k',
        'score_threshold',
        'chunk_count',
        'prompt_tokens',
        'completion_tokens',
        'total_tokens',
        'estimated_cost_usd',
        'total_processing_time_ms',
        'retrieval_time_ms',
        'llm_time_ms',
        'llm_model',
        'llm_temperature',
        'answer_type',
        'answer_length',
        'error_occurred',
        'error_message',
        'environment',
        'source'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        
        for audit in audit_logs:
            # Extract the fields we want
            row = {}
            for field in fields:
                value = audit.get(field, '')
                
                # Handle nested data
                if field == 'answer_length' and audit.get('final_answer'):
                    value = len(audit.get('final_answer', ''))
                
                # Handle lists (convert to string)
                if isinstance(value, list):
                    value = ', '.join(str(v) for v in value)
                
                # Handle booleans
                if isinstance(value, bool):
                    value = 'Yes' if value else 'No'
                
                row[field] = value
            
            writer.writerow(row)
    
    logger.info(f"Exported {len(audit_logs)} records to {output_file}")

def export_detailed_csv(audit_logs: List[Dict[str, Any]], output_file: str = "audit_logs_detailed.csv"):
    """Export detailed audit logs with sources and scores."""
    
    if not audit_logs:
        logger.error("No audit logs to export")
        return
    
    # For detailed export, we'll create one row per source
    detailed_rows = []
    
    for audit in audit_logs:
        base_row = {
            'query_id': audit.get('query_id'),
            'timestamp': audit.get('timestamp'),
            'user_query': audit.get('user_query'),
            'intent': audit.get('intent'),
            'confidence': audit.get('confidence'),
            'thematic_subtype': audit.get('thematic_subtype'),
            'retrieval_method': audit.get('retrieval_method'),
            'chunk_count': audit.get('chunk_count'),
            'total_tokens': audit.get('total_tokens'),
            'estimated_cost_usd': audit.get('estimated_cost_usd'),
            'total_processing_time_ms': audit.get('total_processing_time_ms'),
            'llm_model': audit.get('llm_model'),
            'final_answer': audit.get('final_answer'),
            'error_occurred': 'Yes' if audit.get('error_occurred') else 'No'
        }
        
        # Add source information
        sources = audit.get('sources_used', [])
        scores = audit.get('retrieval_scores', [])
        
        if sources:
            for i, source in enumerate(sources):
                row = base_row.copy()
                row['source_rank'] = i + 1
                row['source_laureate'] = source.get('laureate', '')
                row['source_year'] = source.get('year_awarded', '')
                row['source_category'] = source.get('category', '')
                row['source_country'] = source.get('country', '')
                row['source_score'] = source.get('score', '')
                row['source_chunk_id'] = source.get('chunk_id', '')
                if i < len(scores):
                    row['retrieval_score'] = scores[i]
                detailed_rows.append(row)
        else:
            # No sources, just add the base row
            detailed_rows.append(base_row)
    
    # Write detailed CSV
    if detailed_rows:
        fields = detailed_rows[0].keys()
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields)
            writer.writeheader()
            for row in detailed_rows:
                writer.writerow(row)
        
        logger.info(f"Exported {len(detailed_rows)} detailed records to {output_file}")

def main():
    """Main function to export audit logs to CSV."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Export audit logs to CSV")
    parser.add_argument("--log-dir", default="logs/audit/production", help="Directory containing audit logs")
    parser.add_argument("--output", default="audit_logs.csv", help="Output CSV file")
    parser.add_argument("--detailed", action="store_true", help="Export detailed format with sources")
    args = parser.parse_args()
    
    # Load audit logs
    audit_logs = load_audit_logs(args.log_dir)
    
    if not audit_logs:
        print("❌ No audit logs found")
        return
    
    # Export to CSV
    if args.detailed:
        export_detailed_csv(audit_logs, args.output)
    else:
        export_to_csv(audit_logs, args.output)
    
    print(f"✅ Exported {len(audit_logs)} audit log entries to {args.output}")
    print(f"📊 You can now open this file in:")
    print(f"   • Excel")
    print(f"   • Google Sheets")
    print(f"   • Numbers (Mac)")
    print(f"   • Any database viewer (SQLite, etc.)")
    print(f"   • Python pandas: df = pd.read_csv('{args.output}')")

if __name__ == "__main__":
    main() 