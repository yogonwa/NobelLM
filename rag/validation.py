"""
Centralized validation module for NobelLM RAG pipeline.

This module provides consistent validation for all inputs across the RAG pipeline,
eliminating scattered validation logic and ensuring robust error handling.
"""
import re
import logging
from typing import Dict, Any, Optional, List
import numpy as np
from rag.logging_utils import get_module_logger, log_with_context, QueryContext

logger = get_module_logger(__name__)


def is_invalid_vector(vec: np.ndarray) -> bool:
    """
    Check if a vector is invalid (NaN, inf, or zero).
    
    Args:
        vec: The vector to check
        
    Returns:
        True if the vector is invalid, False otherwise
    """
    return (
        np.isnan(vec).any()
        or np.isinf(vec).any()
        or np.allclose(vec, 0.0)
    )


def validate_query_string(query: str, context: str = "query") -> None:
    """
    Validate a query string before processing.
    
    Args:
        query: The query string to validate
        context: Context for logging (e.g., "user_query", "thematic_term")
        
    Raises:
        ValueError: If query is invalid
    """
    if not query or not isinstance(query, str):
        raise ValueError(f"{context} must be a non-empty string")
    
    if not query.strip():
        raise ValueError(f"{context} cannot be whitespace-only")
    
    if len(query.strip()) < 2:
        raise ValueError(f"{context} must be at least 2 characters long")
    
    # Check for suspicious patterns that might cause issues
    suspicious_patterns = [
        r'^\s*$',  # Only whitespace
        r'^[^\w\s]+$',  # Only special characters
        r'^\d+$',  # Only digits
    ]
    
    for pattern in suspicious_patterns:
        if re.match(pattern, query.strip()):
            raise ValueError(f"{context} contains suspicious pattern: {query}")
    
    # Log validation success
    log_with_context(
        logger,
        logging.DEBUG,
        "Validation",
        f"Query string validated",
        {
            "context": context,
            "length": len(query),
            "preview": query[:50] + "..." if len(query) > 50 else query
        }
    )


def validate_embedding_vector(
    vec: np.ndarray, 
    expected_dim: Optional[int] = None,
    context: str = "embedding"
) -> None:
    """
    Validate an embedding vector before FAISS operations.
    
    Args:
        vec: The embedding vector to validate
        expected_dim: Expected embedding dimension (optional)
        context: Context for logging
        
    Raises:
        ValueError: If vector is invalid
    """
    if not isinstance(vec, np.ndarray):
        raise ValueError(f"{context} must be a numpy array")
    
    if vec.size == 0:
        raise ValueError(f"{context} cannot be empty")
    
    # Check for invalid values
    if np.isnan(vec).any():
        raise ValueError(f"{context} contains NaN values")
    
    if np.isinf(vec).any():
        raise ValueError(f"{context} contains infinite values")
    
    # Check for zero vector
    if np.allclose(vec, 0.0):
        raise ValueError(f"{context} is a zero vector")
    
    # Check shape
    if vec.ndim == 0:
        raise ValueError(f"{context} is a scalar, expected array")
    
    if vec.ndim > 2:
        raise ValueError(f"{context} has too many dimensions: {vec.ndim}")
    
    # Ensure 2D for FAISS compatibility
    if vec.ndim == 1:
        vec = vec.reshape(1, -1)
    
    # Check dimension if specified
    if expected_dim is not None and vec.shape[1] != expected_dim:
        raise ValueError(
            f"{context} dimension mismatch: got {vec.shape[1]}, expected {expected_dim}"
        )
    
    # Check dtype
    if vec.dtype != np.float32:
        logger.warning(f"{context} dtype is {vec.dtype}, converting to float32")
        vec = vec.astype(np.float32)
    
    log_with_context(
        logger,
        logging.DEBUG,
        "Validation",
        f"Embedding vector validated",
        {
            "context": context,
            "shape": vec.shape,
            "dtype": vec.dtype,
            "norm": np.linalg.norm(vec)
        }
    )


def validate_filters(
    filters: Optional[Dict[str, Any]], 
    valid_keys: Optional[List[str]] = None,
    context: str = "filters"
) -> None:
    """
    Validate metadata filters before application.
    
    Args:
        filters: The filters dictionary to validate
        valid_keys: List of valid filter keys (optional)
        context: Context for logging
        
    Raises:
        ValueError: If filters are invalid
    """
    if filters is None:
        return  # None is valid
    
    if not isinstance(filters, dict):
        raise ValueError(f"{context} must be a dictionary or None")
    
    if not filters:
        logger.warning(f"{context} is empty dictionary")
        return
    
    # Check for invalid keys
    for key, value in filters.items():
        if not isinstance(key, str):
            raise ValueError(f"{context} keys must be strings, got {type(key)}")
        
        if not key.strip():
            raise ValueError(f"{context} contains empty key")
        
        if value is None:
            logger.warning(f"{context} key '{key}' has None value")
    
    # Check against valid keys if provided
    if valid_keys is not None:
        invalid_keys = [k for k in filters.keys() if k not in valid_keys]
        if invalid_keys:
            raise ValueError(
                f"{context} contains invalid keys: {invalid_keys}. "
                f"Valid keys: {valid_keys}"
            )
    
    log_with_context(
        logger,
        logging.DEBUG,
        "Validation",
        f"Filters validated",
        {
            "context": context,
            "filter_count": len(filters),
            "keys": list(filters.keys())
        }
    )


def validate_retrieval_parameters(
    top_k: int,
    score_threshold: float,
    min_return: int,
    max_return: Optional[int] = None,
    context: str = "retrieval"
) -> None:
    """
    Validate retrieval parameters for consistency.
    
    Args:
        top_k: Number of results to retrieve
        score_threshold: Minimum similarity score
        min_return: Minimum number of results to return
        max_return: Maximum number of results to return
        context: Context for logging
        
    Raises:
        ValueError: If parameters are invalid
    """
    if not isinstance(top_k, int) or top_k <= 0:
        raise ValueError(f"{context} top_k must be positive integer, got {top_k}")
    
    if not isinstance(score_threshold, (int, float)) or score_threshold < 0:
        raise ValueError(f"{context} score_threshold must be non-negative, got {score_threshold}")
    
    if not isinstance(min_return, int) or min_return <= 0:
        raise ValueError(f"{context} min_return must be positive integer, got {min_return}")
    
    if max_return is not None:
        if not isinstance(max_return, int) or max_return <= 0:
            raise ValueError(f"{context} max_return must be positive integer, got {max_return}")
        
        if max_return < min_return:
            raise ValueError(
                f"{context} max_return ({max_return}) cannot be less than min_return ({min_return})"
            )
    
    if min_return > top_k:
        raise ValueError(
            f"{context} min_return ({min_return}) cannot be greater than top_k ({top_k})"
        )
    
    log_with_context(
        logger,
        logging.DEBUG,
        "Validation",
        f"Retrieval parameters validated",
        {
            "context": context,
            "top_k": top_k,
            "score_threshold": score_threshold,
            "min_return": min_return,
            "max_return": max_return
        }
    )


def validate_model_id(model_id: str, context: str = "model") -> None:
    """
    Validate model identifier.
    
    Args:
        model_id: The model identifier to validate
        context: Context for logging
        
    Raises:
        ValueError: If model_id is invalid
    """
    if not model_id or not isinstance(model_id, str):
        raise ValueError(f"{context} model_id must be non-empty string")
    
    if not model_id.strip():
        raise ValueError(f"{context} model_id cannot be whitespace-only")
    
    # Check for suspicious characters
    if re.search(r'[<>:"|?*]', model_id):
        raise ValueError(f"{context} model_id contains invalid characters: {model_id}")
    
    log_with_context(
        logger,
        logging.DEBUG,
        "Validation",
        f"Model ID validated",
        {
            "context": context,
            "model_id": model_id
        }
    )


def safe_faiss_scoring(
    filtered_vectors: np.ndarray, 
    query_embedding: np.ndarray,
    context: str = "faiss_scoring"
) -> np.ndarray:
    """
    Safely compute FAISS similarity scores with robust shape handling.
    
    Args:
        filtered_vectors: Vectors to score against
        query_embedding: Query vector
        context: Context for logging
        
    Returns:
        Array of similarity scores
        
    Raises:
        ValueError: If inputs are invalid or scoring fails
    """
    try:
        # Validate inputs
        validate_embedding_vector(filtered_vectors, context=f"{context}_filtered")
        validate_embedding_vector(query_embedding, context=f"{context}_query")
        
        # Ensure correct shapes
        if filtered_vectors.ndim == 1:
            filtered_vectors = filtered_vectors.reshape(1, -1)
        
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Ensure 2D arrays
        assert filtered_vectors.ndim == 2, f"filtered_vectors shape: {filtered_vectors.shape}"
        assert query_embedding.ndim == 2, f"query_embedding shape: {query_embedding.shape}"
        
        # Check dimension consistency before dot product
        if filtered_vectors.shape[1] != query_embedding.shape[1]:
            raise ValueError(
                f"Dimension mismatch: filtered_vectors has {filtered_vectors.shape[1]} dimensions, "
                f"query_embedding has {query_embedding.shape[1]} dimensions"
            )
        
        # Compute scores
        scores = np.dot(filtered_vectors, query_embedding[0])
        
        # Handle edge cases
        if np.isscalar(scores):
            scores = np.array([scores])
        
        if scores.ndim == 0:
            scores = scores.reshape(1)
        
        # Ensure 1D output
        assert scores.ndim == 1, f"scores shape: {scores.shape}"
        
        log_with_context(
            logger,
            logging.DEBUG,
            "Validation",
            f"FAISS scoring completed",
            {
                "context": context,
                "input_shape": filtered_vectors.shape,
                "output_shape": scores.shape,
                "score_range": (float(scores.min()), float(scores.max()))
            }
        )
        
        return scores
        
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Validation",
            f"FAISS scoring failed",
            {
                "context": context,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        raise ValueError(f"FAISS scoring failed: {e}") 