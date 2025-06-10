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
    
    This function is used consistently across all retrieval paths to ensure
    uniform chunk filtering behavior. It:
    1. Sorts chunks by score in descending order
    2. Applies the score threshold
    3. Returns at least min_return chunks (if specified)
    4. Limits to max_return chunks (if specified)
    
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

    # Sort by score descending
    sorted_chunks = sorted(chunks, key=lambda x: x["score"], reverse=True)
    
    # Get initial score distribution
    scores = [c["score"] for c in sorted_chunks]
    logger.info(
        f"[RAG][Filter] Initial {len(scores)} chunks — "
        f"mean score: {np.mean(scores):.3f}, stddev: {np.std(scores):.3f}, "
        f"min: {min(scores):.3f}, max: {max(scores):.3f}"
    )

    # Apply score threshold
    filtered_chunks = [c for c in sorted_chunks if c["score"] >= score_threshold]
    
    # If we don't have enough chunks above threshold, take top min_return by rank
    if len(filtered_chunks) < min_return:
        logger.warning(
            f"[RAG][Filter] Only {len(filtered_chunks)} chunks above threshold {score_threshold}, "
            f"taking top {min_return} by rank"
        )
        filtered_chunks = sorted_chunks[:min_return]
    
    # Apply max_return if specified
    if max_return is not None and len(filtered_chunks) > max_return:
        logger.info(
            f"[RAG][Filter] Capping at {max_return} chunks (had {len(filtered_chunks)})"
        )
        filtered_chunks = filtered_chunks[:max_return]

    # Log final score distribution
    final_scores = [c["score"] for c in filtered_chunks]
    logger.info(
        f"[RAG][Filter] Final {len(final_scores)} chunks — "
        f"mean score: {np.mean(final_scores):.3f}, stddev: {np.std(final_scores):.3f}, "
        f"min: {min(final_scores):.3f}, max: {max(final_scores):.3f}"
    )

    return filtered_chunks 