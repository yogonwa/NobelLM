"""
utils/cost_logger.py

Modular logger for OpenAI API cost and token usage events.
Logs structured JSON per query for cost monitoring and debugging.
"""
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("cost_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)


def log_cost_event(
    user_query: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    chunk_count: int,
    estimated_cost_usd: float,
    log_destination: Optional[str] = None,
    extra: Optional[dict] = None
) -> None:
    """
    Log a structured JSON event for an OpenAI API call's cost and token usage.

    Args:
        user_query: The user's input query string.
        model: The OpenAI model used (e.g., 'gpt-3.5-turbo').
        prompt_tokens: Number of tokens in the prompt.
        completion_tokens: Number of tokens in the completion.
        chunk_count: Number of retrieved chunks used in the prompt.
        estimated_cost_usd: Estimated cost in USD for this call.
        log_destination: Optional file path to log to (default: stdout).
        extra: Optional dict of additional fields to include in the log.
    """
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user_query": user_query,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "chunk_count": chunk_count,
        "estimated_cost_usd": round(estimated_cost_usd, 6),
    }
    if extra:
        event.update(extra)
    try:
        log_line = json.dumps(event, ensure_ascii=False)
        if log_destination:
            with open(log_destination, "a", encoding="utf-8") as f:
                f.write(log_line + "\n")
        else:
            logger.info(log_line)
    except Exception as e:
        logger.error(f"Failed to log cost event: {e}") 