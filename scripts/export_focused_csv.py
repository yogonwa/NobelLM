#!/usr/bin/env python3
"""
Export Focused Audit Logs to CSV

Export only the key fields: User Query, Intent, Prompt Used, Response, Error y/n
"""

import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any

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

def export_focused_csv(audit_logs: List[Dict[str, Any]], output_file: str = "audit_focused.csv"):
    """Export focused audit logs with only key fields."""
    
    if not audit_logs:
        logger.error("No audit logs to export")
        return
    
    # Define the focused fields
    fields = [
        'user_query',
        'intent', 
        'prompt_template',
        'final_prompt',
        'final_answer',
        'error_occurred',
        'error_message',
        'timestamp',
        'query_id'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        
        for audit in audit_logs:
            row = {}
            for field in fields:
                value = audit.get(field, '')
                
                # Handle booleans
                if field == 'error_occurred':
                    value = 'Yes' if value else 'No'
                
                # Truncate long text fields for readability
                if field in ['final_prompt', 'final_answer'] and isinstance(value, str):
                    if len(value) > 500:
                        value = value[:500] + "..."
                
                row[field] = value
            
            writer.writerow(row)
    
    logger.info(f"Exported {len(audit_logs)} focused records to {output_file}")

def main():
    """Main function to export focused audit logs to CSV."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Export focused audit logs to CSV")
    parser.add_argument("--log-dir", default="logs/audit/production", help="Directory containing audit logs")
    parser.add_argument("--output", default="audit_focused.csv", help="Output CSV file")
    args = parser.parse_args()
    
    # Load audit logs
    audit_logs = load_audit_logs(args.log_dir)
    
    if not audit_logs:
        print("❌ No audit logs found")
        return
    
    # Export to CSV
    export_focused_csv(audit_logs, args.output)
    
    print(f"✅ Exported {len(audit_logs)} focused audit log entries to {args.output}")
    print(f"📊 Key fields included:")
    print(f"   • User Query")
    print(f"   • Intent")
    print(f"   • Prompt Template")
    print(f"   • Final Prompt (truncated)")
    print(f"   • Response")
    print(f"   • Error (Yes/No)")
    print(f"   • Timestamp")
    print(f"   • Query ID")

if __name__ == "__main__":
    main() 