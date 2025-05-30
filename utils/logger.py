import os
from datetime import datetime

def log_query(query: str, source: str = "home"):
    """
    Append a query log entry to data/query_log.tsv with UTC timestamp, source, and query.
    Does not log user IP or identifiers.
    """
    try:
        os.makedirs("data", exist_ok=True)
        with open("data/query_log.tsv", "a", encoding="utf-8") as f:
            timestamp = datetime.utcnow().isoformat()
            f.write(f"{timestamp}\t{source}\t{query}\n")
    except Exception:
        pass 