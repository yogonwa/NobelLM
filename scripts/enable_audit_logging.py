#!/usr/bin/env python3
"""
Enable Comprehensive Audit Logging in NobelLM Production

This script updates the production system to use comprehensive audit logging
that captures the complete RAG pipeline trace.
"""

import os
import sys
from pathlib import Path

def enable_audit_logging():
    """Enable audit logging by updating the backend configuration."""
    
    # Create logs directory
    logs_dir = Path("logs/audit")
    logs_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created audit logs directory: {logs_dir}")
    
    # Update backend routes to use audit logging
    backend_routes_file = Path("backend/app/routes.py")
    
    if backend_routes_file.exists():
        print("🔄 Updating backend routes to enable audit logging...")
        
        # Read current content
        with open(backend_routes_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Add audit logging import
        if "from utils.audit_logger import start_query_audit, complete_query_audit" not in content:
            # Find the imports section
            import_section = content.find("from fastapi import")
            if import_section != -1:
                # Add audit logging import after other imports
                audit_import = "\nfrom utils.audit_logger import start_query_audit, complete_query_audit"
                content = content[:import_section] + audit_import + "\n" + content[import_section:]
        
        # Update the process_query function to use audit logging
        if "def process_query(" in content and "start_query_audit" not in content:
            # Find the process_query function
            process_query_start = content.find("async def process_query(")
            if process_query_start != -1:
                # Find the start of the function body
                body_start = content.find(":", process_query_start) + 1
                
                # Add audit logging at the start of the function
                audit_start = """
    # Start audit logging
    query_id = start_query_audit(query, source="api")
    
    try:"""
                
                # Find the existing try block
                try_start = content.find("try:", body_start)
                if try_start != -1:
                    # Replace the existing try with our enhanced version
                    content = content[:try_start] + audit_start + content[try_start + 4:]
                else:
                    # Add try block if it doesn't exist
                    content = content[:body_start] + audit_start + content[body_start:]
                
                # Add audit completion at the end
                audit_complete = """
    finally:
        # Complete audit logging
        complete_query_audit(query_id)
"""
                
                # Find the end of the function
                function_end = content.rfind("return QueryResponse")
                if function_end != -1:
                    # Find the actual return statement
                    return_end = content.find("\n", function_end)
                    if return_end != -1:
                        content = content[:return_end] + audit_complete + content[return_end:]
        
        # Write updated content
        with open(backend_routes_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        print("✅ Updated backend routes with audit logging")
    else:
        print("❌ Backend routes file not found")
    
    # Update requirements to include audit logger dependencies
    requirements_file = Path("backend/requirements.txt")
    if requirements_file.exists():
        print("🔄 Checking requirements for audit logging dependencies...")
        
        with open(requirements_file, "r", encoding="utf-8") as f:
            requirements = f.read()
        
        # Add pandas for analysis if not present
        if "pandas" not in requirements:
            with open(requirements_file, "a", encoding="utf-8") as f:
                f.write("\n# Audit logging analysis\npandas\n")
            print("✅ Added pandas to requirements for audit analysis")
    
    # Create a simple test script
    test_script = """#!/usr/bin/env python3
\"\"\"
Test script to verify audit logging is working.
\"\"\"

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.audit_logger import get_audit_logger, start_query_audit, complete_query_audit

def test_audit_logging():
    \"\"\"Test that audit logging is working.\"\"\"
    print("🧪 Testing audit logging...")
    
    # Test audit logger initialization
    audit_logger = get_audit_logger()
    print("✅ Audit logger initialized")
    
    # Test audit creation
    query_id = start_query_audit("test query", source="test")
    print(f"✅ Started audit for query: {query_id}")
    
    # Test audit completion
    audit = complete_query_audit(query_id)
    print(f"✅ Completed audit: {audit.query_id if audit else 'None'}")
    
    # Test summary
    summary = audit_logger.get_audit_summary(hours=1)
    print(f"✅ Audit summary: {summary.get('total_queries', 0)} queries")
    
    print("🎉 Audit logging test completed successfully!")

if __name__ == "__main__":
    test_audit_logging()
"""
    
    test_file = Path("scripts/test_audit_logging.py")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_script)
    
    print(f"✅ Created test script: {test_file}")
    
    # Create README for audit logging
    readme_content = """# NobelLM Audit Logging

This directory contains comprehensive audit logs for the NobelLM RAG pipeline.

## What is captured

Each audit log entry contains the complete trace of a query through the system:

1. **User Query**: The original user input
2. **Intent Classification**: How the system classified the query intent
3. **Keyword Expansion**: For thematic queries, what terms were expanded
4. **Retrieval Process**: What chunks were retrieved and their scores
5. **Prompt Construction**: The final prompt sent to the LLM
6. **LLM Interaction**: The LLM response and token usage
7. **Final Result**: The compiled answer and sources used
8. **Performance Metrics**: Processing times and costs
9. **Error Information**: Any errors that occurred

## File Format

Audit logs are stored in JSONL format (one JSON object per line) with filenames:
- `audit_log_YYYY-MM-DD.jsonl`

## Analysis Tools

Use the analysis scripts to gain insights:

```bash
# Analyze recent activity
python scripts/analyze_audit_logs.py --recent 24h

# Analyze specific query
python scripts/analyze_audit_logs.py --query "your query text"

# Export to CSV for further analysis
python scripts/analyze_audit_logs.py --export --since 2025-07-24

# Test audit logging
python scripts/test_audit_logging.py
```

## Monitoring

For real-time monitoring:

```bash
# Monitor live queries
python scripts/monitor_production.py live

# Show recent activity
python scripts/monitor_production.py recent

# Dashboard view
python scripts/query_dashboard.py
```

## Privacy

Audit logs contain:
- ✅ User queries (for analysis)
- ✅ System processing details
- ✅ Performance metrics
- ❌ No user IP addresses
- ❌ No personal identifiers
- ❌ No session data

Logs are stored locally and can be deleted at any time.
"""
    
    readme_file = Path("logs/audit/README.md")
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print(f"✅ Created audit logging documentation: {readme_file}")
    
    print("\n🎉 Audit logging has been enabled!")
    print("\nNext steps:")
    print("1. Test the audit logging: python scripts/test_audit_logging.py")
    print("2. Deploy the updated backend: fly deploy --app nobellm-api")
    print("3. Monitor production queries: python scripts/monitor_production.py live")
    print("4. Analyze logs: python scripts/analyze_audit_logs.py --recent 24h")

if __name__ == "__main__":
    enable_audit_logging() 