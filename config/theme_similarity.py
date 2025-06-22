"""
Theme Similarity Computation for NobelLM RAG Pipeline

This module provides similarity computation between query embeddings and theme keywords
using the existing safe_faiss_scoring pattern for consistency and robustness.

Key Features:
- Uses existing safe_faiss_scoring pattern for consistency
- Model-aware similarity computation
- Configurable similarity thresholds
- Comprehensive logging and validation
- Performance monitoring

Usage:
    from config.theme_similarity import compute_theme_similarities
    
    # Compute similarities for a query embedding
    similarities = compute_theme_similarities(
        query_embedding=query_emb,
        model_id="bge-large",
        similarity_threshold=0.3
    )
    
    # Get ranked theme keywords
    ranked_keywords = [(kw, score) for kw, score in similarities.items() if score >= 0.3]

Author: NobelLM Team
"""
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from config.theme_embeddings import ThemeEmbeddings
from rag.validation import safe_faiss_scoring, validate_embedding_vector
from rag.model_config import get_model_config

logger = logging.getLogger(__name__)

def compute_theme_similarities(
    query_embedding: np.ndarray,
    model_id: str = "bge-large",
    similarity_threshold: float = 0.3,
    max_results: Optional[int] = None
) -> Dict[str, float]:
    """
    Compute similarity scores between a query embedding and all theme keywords.
    
    Uses the existing safe_faiss_scoring pattern for consistency and robustness.
    Returns a dictionary mapping theme keywords to similarity scores.
    
    Args:
        query_embedding: Normalized query embedding vector
        model_id: Model identifier for theme embeddings
        similarity_threshold: Minimum similarity score to include (default: 0.3)
        max_results: Maximum number of results to return (default: None, return all)
        
    Returns:
        Dictionary mapping theme keywords to similarity scores
        
    Raises:
        ValueError: If inputs are invalid or similarity computation fails
        RuntimeError: If theme embeddings are not available
    """
    # Validate inputs
    validate_embedding_vector(query_embedding, context="theme_similarity_query")
    
    if similarity_threshold < 0.0 or similarity_threshold > 1.0:
        raise ValueError(f"Invalid similarity threshold: {similarity_threshold} (must be 0.0-1.0)")
    
    if max_results is not None and max_results <= 0:
        raise ValueError(f"Invalid max_results: {max_results} (must be > 0)")
    
    # Get model config for validation
    config = get_model_config(model_id)
    expected_dim = config["embedding_dim"]
    
    if query_embedding.shape[0] != expected_dim:
        raise ValueError(
            f"Query embedding dimension mismatch: expected {expected_dim}, got {query_embedding.shape[0]}"
        )
    
    try:
        # Load theme embeddings
        theme_embeddings = ThemeEmbeddings(model_id)
        all_embeddings = theme_embeddings.get_all_embeddings()
        
        if not all_embeddings:
            logger.warning("No theme embeddings available")
            return {}
        
        # Extract keywords and embeddings
        keywords = list(all_embeddings.keys())
        embeddings = np.array(list(all_embeddings.values()), dtype=np.float32)
        
        logger.info(f"Computing similarities for {len(keywords)} theme keywords")
        
        # Use safe_faiss_scoring pattern for consistency
        similarities = safe_faiss_scoring(
            filtered_vectors=embeddings,
            query_embedding=query_embedding.reshape(1, -1),
            context="theme_similarity"
        )
        
        # Create keyword -> score mapping
        keyword_scores = {}
        for keyword, score in zip(keywords, similarities):
            if score >= similarity_threshold:
                keyword_scores[keyword] = float(score)
        
        # Sort by score (descending) and apply max_results limit
        sorted_items = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
        
        if max_results is not None:
            sorted_items = sorted_items[:max_results]
        
        result = dict(sorted_items)
        
        logger.info(
            f"Theme similarity computation completed",
            extra={
                "total_keywords": len(keywords),
                "above_threshold": len(result),
                "max_similarity": max(result.values()) if result else 0.0,
                "min_similarity": min(result.values()) if result else 0.0,
                "threshold": similarity_threshold
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Theme similarity computation failed: {e}")
        raise ValueError(f"Theme similarity computation failed: {e}")


def get_ranked_theme_keywords(
    query_embedding: np.ndarray,
    model_id: str = "bge-large",
    similarity_threshold: float = 0.3,
    max_results: Optional[int] = None
) -> List[Tuple[str, float]]:
    """
    Get ranked list of theme keywords with similarity scores.
    
    Args:
        query_embedding: Normalized query embedding vector
        model_id: Model identifier for theme embeddings
        similarity_threshold: Minimum similarity score to include
        max_results: Maximum number of results to return
        
    Returns:
        List of (keyword, score) tuples, sorted by score descending
    """
    similarities = compute_theme_similarities(
        query_embedding=query_embedding,
        model_id=model_id,
        similarity_threshold=similarity_threshold,
        max_results=max_results
    )
    
    return list(similarities.items())


def validate_similarity_threshold(threshold: float, context: str = "similarity_threshold") -> None:
    """
    Validate similarity threshold value.
    
    Args:
        threshold: Threshold value to validate
        context: Context for error messages
        
    Raises:
        ValueError: If threshold is invalid
    """
    if not isinstance(threshold, (int, float)):
        raise ValueError(f"{context} must be a number, got {type(threshold)}")
    
    if threshold < 0.0 or threshold > 1.0:
        raise ValueError(f"{context} must be between 0.0 and 1.0, got {threshold}")


def get_similarity_stats(similarities: Dict[str, float]) -> Dict[str, any]:
    """
    Get statistics about similarity scores.
    
    Args:
        similarities: Dictionary of keyword -> score mappings
        
    Returns:
        Dictionary with similarity statistics
    """
    if not similarities:
        return {
            "count": 0,
            "mean": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
            "median": 0.0
        }
    
    scores = list(similarities.values())
    
    return {
        "count": len(scores),
        "mean": float(np.mean(scores)),
        "std": float(np.std(scores)),
        "min": float(np.min(scores)),
        "max": float(np.max(scores)),
        "median": float(np.median(scores))
    } 