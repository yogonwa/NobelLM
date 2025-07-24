# NobelLM Audit Logging

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
