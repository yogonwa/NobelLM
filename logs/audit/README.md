# NobelLM Audit Logging

This directory contains comprehensive audit logs for the NobelLM RAG pipeline.

## What is captured

Each audit log entry contains the complete trace of a query through the system:

1. **User Query**: The original user input
2. **Intent Classification**: How the system classified the query intent
3. **Thematic Subtype Detection**: For thematic queries, which subtype was detected (synthesis, enumerative, analytical, exploratory)
4. **Keyword Expansion**: For thematic queries, what terms were expanded
5. **Retrieval Process**: What chunks were retrieved and their scores
6. **Prompt Construction**: The final prompt sent to the LLM
7. **LLM Interaction**: The LLM response and token usage
8. **Final Result**: The compiled answer and sources used
9. **Performance Metrics**: Processing times and costs
10. **Error Information**: Any errors that occurred

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

# Analyze thematic subtype distribution
python scripts/analyze_audit_logs.py --subtype-analysis

# Export to CSV for further analysis
python scripts/analyze_audit_logs.py --export --since 2025-07-24

# Test audit logging
python scripts/test_audit_logging.py
```

## Thematic Subtype Tracking

For thematic queries, the system now tracks:

- **Subtype Detection**: Which subtype was identified (synthesis, enumerative, analytical, exploratory)
- **Confidence Score**: How confident the system was in the subtype classification
- **Triggering Cues**: Which keywords or patterns triggered the subtype detection
- **Template Selection**: Which prompt template was used based on the subtype

This enables analysis of:
- Subtype distribution and frequency
- Detection accuracy and confidence patterns
- Template effectiveness by subtype
- User query patterns that trigger different subtypes

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
- ✅ Thematic subtype detection results
- ❌ No user IP addresses
- ❌ No personal identifiers
- ❌ No session data

Logs are stored locally and can be deleted at any time.

## Recent Updates

**2025-01-XX**: Added thematic subtype tracking to audit logs
- Enhanced `QueryAuditLog` with `thematic_subtype`, `subtype_confidence`, and `subtype_cues` fields
- Added `log_thematic_subtype()` method to `AuditLogger`
- Updated query engine audit to capture subtype detection
- Extended `QueryRouteResult` to include subtype information
