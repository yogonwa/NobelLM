"""
rag.retrieval_logic: Centralized retrieval logic for Phase 4 enhancements.

This module provides unified fallback logic, standardized result formats, and
consistent filtering behavior across all retrieval paths in the NobelLM RAG pipeline.

Key features:
- Unified fallback logic with comprehensive logging
- Standardized scored result format with filtering reasons
- Consistent score threshold application
- Performance monitoring and metrics
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ScoredChunk:
    """
    Standardized format for scored chunks with filtering metadata.
    
    This class ensures consistent result format across all retrieval paths
    and provides transparency about filtering decisions.
    """
    chunk_id: str
    text: str
    score: float
    metadata: Dict[str, Any]
    rank: Optional[int] = None
    filtering_reason: Optional[str] = None  # "threshold", "min_return", "max_return"
    source_terms: List[str] = field(default_factory=list)  # For thematic queries
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for backward compatibility."""
        result = {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "score": self.score,
            "rank": self.rank,
            "filtering_reason": self.filtering_reason,
            "source_terms": self.source_terms,
            **self.metadata
        }
        return result


def apply_score_threshold(
    chunks: List[Dict[str, Any]], 
    score_threshold: float
) -> List[Dict[str, Any]]:
    """
    Apply score threshold filtering to chunks.
    
    Args:
        chunks: List of chunk dictionaries with 'score' field
        score_threshold: Minimum similarity score
        
    Returns:
        List of chunks that pass the threshold
    """
    if not chunks:
        return []
    
    # Sort by score descending for consistent behavior
    sorted_chunks = sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)
    
    # Apply threshold
    filtered_chunks = [c for c in sorted_chunks if c.get("score", 0) >= score_threshold]
    
    logger.debug(
        f"[RetrievalLogic] Score threshold {score_threshold}: "
        f"{len(filtered_chunks)}/{len(chunks)} chunks passed"
    )
    
    return filtered_chunks


def apply_min_return_fallback(
    chunks: List[Dict[str, Any]], 
    min_return: int
) -> List[Dict[str, Any]]:
    """
    Apply minimum return fallback to ensure at least min_return chunks.
    
    Args:
        chunks: List of chunk dictionaries (should be sorted by score descending)
        min_return: Minimum number of chunks to return
        
    Returns:
        List of chunks with fallback applied
    """
    if not chunks:
        return []
    
    # Ensure chunks are sorted by score descending
    sorted_chunks = sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)
    
    if len(sorted_chunks) < min_return:
        logger.warning(
            f"[RetrievalLogic] Only {len(sorted_chunks)} chunks available, "
            f"cannot meet min_return={min_return}"
        )
        return sorted_chunks
    
    # Take top min_return chunks and mark them as fallback
    fallback_chunks = sorted_chunks[:min_return]
    
    # Mark chunks as fallback if they weren't already marked
    for chunk in fallback_chunks:
        if not chunk.get("filtering_reason"):
            chunk["filtering_reason"] = "min_return_fallback"
    
    logger.info(
        f"[RetrievalLogic] Applied min_return fallback: "
        f"returning {len(fallback_chunks)} chunks"
    )
    
    return fallback_chunks


def apply_max_return_limit(
    chunks: List[Dict[str, Any]], 
    max_return: int
) -> List[Dict[str, Any]]:
    """
    Apply maximum return limit to chunks.
    
    Args:
        chunks: List of chunk dictionaries (should be sorted by score descending)
        max_return: Maximum number of chunks to return
        
    Returns:
        List of chunks with max_return limit applied
    """
    if not chunks:
        return []
    
    # Ensure chunks are sorted by score descending
    sorted_chunks = sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)
    
    if len(sorted_chunks) <= max_return:
        return sorted_chunks
    
    # Take top max_return chunks
    limited_chunks = sorted_chunks[:max_return]
    
    # Mark chunks as max_return limited if they weren't already marked
    for chunk in limited_chunks:
        if not chunk.get("filtering_reason"):
            chunk["filtering_reason"] = "max_return_limit"
    
    logger.info(
        f"[RetrievalLogic] Applied max_return limit: "
        f"capped at {len(limited_chunks)} chunks (had {len(sorted_chunks)})"
    )
    
    return limited_chunks


def apply_retrieval_fallback(
    chunks: List[Dict[str, Any]],
    score_threshold: float,
    min_return: int,
    max_return: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Apply comprehensive retrieval fallback logic with detailed logging.
    
    This function implements the unified fallback logic that ensures:
    1. Score threshold filtering is applied first
    2. Minimum return guarantee is enforced when possible
    3. Maximum return limit is respected
    4. All filtering decisions are logged with reasons
    
    Args:
        chunks: List of chunk dictionaries with 'score' field
        score_threshold: Minimum similarity score
        min_return: Minimum number of chunks to return
        max_return: Optional maximum number of chunks to return
        
    Returns:
        List of chunks with comprehensive fallback applied
    """
    if not chunks:
        logger.warning("[RetrievalLogic] No chunks provided for filtering")
        return []
    
    # Get initial score distribution for logging
    scores = [c.get("score", 0) for c in chunks]
    logger.info(
        f"[RetrievalLogic] Initial {len(scores)} chunks — "
        f"mean score: {np.mean(scores):.3f}, stddev: {np.std(scores):.3f}, "
        f"min: {min(scores):.3f}, max: {max(scores):.3f}"
    )
    
    # Step 1: Apply score threshold
    filtered_chunks = apply_score_threshold(chunks, score_threshold)
    
    # Step 2: Apply min_return fallback if needed
    if len(filtered_chunks) < min_return:
        logger.warning(
            f"[RetrievalLogic] Only {len(filtered_chunks)} chunks above threshold {score_threshold}, "
            f"applying min_return fallback for {min_return} chunks"
        )
        filtered_chunks = apply_min_return_fallback(chunks, min_return)
    else:
        # Mark chunks that passed threshold
        for chunk in filtered_chunks:
            if not chunk.get("filtering_reason"):
                chunk["filtering_reason"] = "threshold"
    
    # Step 3: Apply max_return limit if specified
    if max_return is not None and len(filtered_chunks) > max_return:
        filtered_chunks = apply_max_return_limit(filtered_chunks, max_return)
    
    # Log final score distribution
    final_scores = [c.get("score", 0) for c in filtered_chunks]
    filtering_reasons = [c.get("filtering_reason", "unknown") for c in filtered_chunks]
    
    logger.info(
        f"[RetrievalLogic] Final {len(final_scores)} chunks — "
        f"mean score: {np.mean(final_scores):.3f}, stddev: {np.std(final_scores):.3f}, "
        f"min: {min(final_scores):.3f}, max: {max(final_scores):.3f}"
    )
    
    logger.debug(
        f"[RetrievalLogic] Filtering reasons: {dict(zip(*np.unique(filtering_reasons, return_counts=True)))}"
    )
    
    return filtered_chunks


def create_scored_chunk(
    chunk_id: str,
    text: str,
    score: float,
    metadata: Dict[str, Any],
    rank: Optional[int] = None,
    filtering_reason: Optional[str] = None,
    source_terms: Optional[List[str]] = None
) -> ScoredChunk:
    """
    Create a standardized ScoredChunk object.
    
    Args:
        chunk_id: Unique identifier for the chunk
        text: The chunk text content
        score: Similarity score
        metadata: Additional metadata (laureate, year, source_type, etc.)
        rank: Optional rank in results
        filtering_reason: Why this chunk was included
        source_terms: Terms that led to this chunk (for thematic queries)
        
    Returns:
        ScoredChunk object
    """
    return ScoredChunk(
        chunk_id=chunk_id,
        text=text,
        score=score,
        metadata=metadata,
        rank=rank,
        filtering_reason=filtering_reason,
        source_terms=source_terms or []
    )


def convert_to_scored_chunks(
    chunks: List[Dict[str, Any]],
    filtering_reason: Optional[str] = None
) -> List[ScoredChunk]:
    """
    Convert list of chunk dictionaries to ScoredChunk objects.
    
    Args:
        chunks: List of chunk dictionaries
        filtering_reason: Default filtering reason for all chunks
        
    Returns:
        List of ScoredChunk objects
    """
    scored_chunks = []
    for i, chunk in enumerate(chunks):
        scored_chunk = create_scored_chunk(
            chunk_id=chunk.get("chunk_id", f"chunk_{i}"),
            text=chunk.get("text", ""),
            score=chunk.get("score", 0.0),
            metadata={k: v for k, v in chunk.items() 
                     if k not in ["chunk_id", "text", "score", "rank", "filtering_reason", "source_terms"]},
            rank=chunk.get("rank", i),
            filtering_reason=chunk.get("filtering_reason", filtering_reason),
            source_terms=chunk.get("source_terms", [])
        )
        scored_chunks.append(scored_chunk)
    
    return scored_chunks


def log_retrieval_metrics(
    chunks: List[Dict[str, Any]],
    context: str = "retrieval"
) -> None:
    """
    Log comprehensive retrieval metrics for monitoring and debugging.
    
    Args:
        chunks: List of chunk dictionaries
        context: Context for logging (e.g., "factual", "thematic", "generative")
    """
    if not chunks:
        logger.info(f"[RetrievalLogic][{context}] No chunks retrieved")
        return
    
    scores = [c.get("score", 0) for c in chunks]
    filtering_reasons = [c.get("filtering_reason", "unknown") for c in chunks]
    
    logger.info(
        f"[RetrievalLogic][{context}] Retrieved {len(chunks)} chunks — "
        f"mean score: {np.mean(scores):.3f}, stddev: {np.std(scores):.3f}, "
        f"min: {min(scores):.3f}, max: {max(scores):.3f}"
    )
    
    # Log filtering reason distribution
    reason_counts = {}
    for reason in filtering_reasons:
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    
    logger.debug(f"[RetrievalLogic][{context}] Filtering reasons: {reason_counts}")
    
    # Log source term distribution for thematic queries
    if any("source_terms" in chunk for chunk in chunks):
        all_source_terms = []
        for chunk in chunks:
            all_source_terms.extend(chunk.get("source_terms", []))
        
        if all_source_terms:
            term_counts = {}
            for term in all_source_terms:
                term_counts[term] = term_counts.get(term, 0) + 1
            
            logger.debug(f"[RetrievalLogic][{context}] Source terms: {term_counts}") 