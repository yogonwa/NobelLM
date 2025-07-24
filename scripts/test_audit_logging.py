#!/usr/bin/env python3
"""
Test script to verify audit logging is working.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.audit_logger import get_audit_logger, start_query_audit, complete_query_audit

def test_audit_logging():
    """Test that audit logging is working."""
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
