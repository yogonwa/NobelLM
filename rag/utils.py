"""
rag.utils: Shared utilities for the NobelLM RAG pipeline.

Includes:
- format_chunks_for_prompt: Utility to format retrieved text chunks (with metadata) for LLM prompt construction.
- filter_top_chunks: Function to filter chunks based on score threshold and ensure a minimum number of results.

This ensures that every chunk passed to the LLM includes not just the text, but also key metadata (laureate, year, source type), improving answer quality and explainability.
"""
from typing import List, Dict, Any, Optional
import logging
import numpy as np
from .retrieval_logic import apply_retrieval_fallback, log_retrieval_metrics

logger = logging.getLogger(__name__)

def format_chunks_for_prompt(
    chunks: List[Dict[str, Any]],
    fields=("text", "laureate", "year_awarded", "source_type"),
    template="{text} (by {laureate}, {year_awarded}, {source_type})"
) -> str:
    """
    Format a list of text chunks (with metadata) for inclusion in an LLM prompt.

    Each chunk is formatted as a string including its text and selected metadata fields.
    The default template is: '{text} (by {laureate}, {year_awarded}, {source_type})'.
    All formatted chunks are joined with double newlines for clear separation in the prompt context.

    Args:
        chunks: List of chunk dicts, each with at least a 'text' field and optional metadata.
        fields: Tuple of fields to include (default: text, laureate, year_awarded, source_type).
        template: Format string for each chunk. Should use named placeholders matching the fields.
    Returns:
        String with all formatted chunks, separated by double newlines, ready for LLM prompt context.
    Example:
        >>> chunks = [{"text": "Example.", "laureate": "Alice", "year_awarded": 2000, "source_type": "lecture"}]
        >>> format_chunks_for_prompt(chunks)
        'Example. (by Alice, 2000, lecture)'
    """
    lines = []
    for chunk in chunks:
        # Use .get() for safety in case some fields are missing; fallback to 'Unknown' for missing metadata
        lines.append(template.format(
            text=chunk.get("text", ""),
            laureate=chunk.get("laureate", "Unknown"),
            year_awarded=chunk.get("year_awarded", "Unknown"),
            source_type=chunk.get("source_type", "Unknown")
        ))
    return "\n\n".join(lines)

def filter_top_chunks(
    chunks: List[Dict[str, Any]],
    score_threshold: float = 0.2,
    min_return: Optional[int] = None,
    max_return: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Filter chunks by score threshold while ensuring minimum and maximum return counts.
    
    This function uses the centralized retrieval logic to ensure consistent behavior
    across all retrieval paths. It:
    1. Applies score threshold filtering
    2. Guarantees minimum return count when possible
    3. Respects maximum return limits
    4. Provides comprehensive logging of filtering decisions
    
    The function is used in:
    - answer_query() for all query types
    - ThematicRetriever.retrieve() after deduplication
    - query_index() for direct FAISS search
    
    Args:
        chunks: List of chunk dictionaries with 'score' field
        score_threshold: Minimum similarity score (default: 0.2)
        min_return: Minimum number of chunks to return
        max_return: Maximum number of chunks to return
        
    Returns:
        Filtered list of chunks, sorted by score descending
        
    Note:
        If fewer than min_return chunks pass the threshold, the top min_return
        chunks are returned regardless of score. This ensures consistent prompt
        construction while still preferring high-quality matches.
    """
    if not chunks:
        logger.warning("[RAG][Filter] No chunks provided to filter")
        return []

    # Use centralized retrieval logic for consistent behavior
    filtered_chunks = apply_retrieval_fallback(
        chunks=chunks,
        score_threshold=score_threshold,
        min_return=min_return or 3,
        max_return=max_return
    )
    
    # Log final metrics for monitoring
    log_retrieval_metrics(filtered_chunks, context="filter_top_chunks")
    
    return filtered_chunks 