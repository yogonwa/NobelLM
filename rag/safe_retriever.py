"""
Safe Retriever Module for NobelLM RAG Pipeline

This module provides a safe, reusable pattern for chunk retrieval that handles
embedding correctly based on the USE_FAISS_SUBPROCESS environment flag.

The pattern ensures:
1. Embedding happens exactly once
2. Embedding happens in the right process (in-process vs subprocess)
3. Consistent parameter handling across all retrieval paths
4. No circular import issues
"""

import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from rag.model_config import get_model_config, DEFAULT_MODEL_ID
from sentence_transformers import SentenceTransformer
from rag.dual_process_retriever import retrieve_chunks_dual_process
from rag.retriever import query_index
from rag.logging_utils import get_module_logger, log_with_context, QueryContext

logger = get_module_logger(__name__)

USE_FAISS_SUBPROCESS = os.getenv("NOBELLM_USE_FAISS_SUBPROCESS", "0") == "1"

# Cache for the embedding model to avoid reloading
_MODEL = None
_MODEL_LOCK = None

def get_embedding_model(model_id: str = None) -> SentenceTransformer:
    """
    Get the embedding model for the specified model_id.
    Uses caching to avoid reloading the model.
    """
    global _MODEL, _MODEL_LOCK
    if _MODEL_LOCK is None:
        import threading
        _MODEL_LOCK = threading.Lock()
    
    if _MODEL is None:
        with _MODEL_LOCK:
            if _MODEL is None:
                config = get_model_config(model_id or DEFAULT_MODEL_ID)
                logger.info(f"Loading embedding model '{config['model_name']}'...")
                _MODEL = SentenceTransformer(config['model_name'])
    return _MODEL


def embed_query_safe(query: str, model_id: str = None) -> np.ndarray:
    """
    Safely embed a query string using the specified model.
    
    Args:
        query: The query string to embed
        model_id: Optional model identifier
        
    Returns:
        Normalized query embedding as numpy array
    """
    model = get_embedding_model(model_id)
    emb = model.encode(query, show_progress_bar=False, normalize_embeddings=True)
    return np.array(emb, dtype=np.float32)


def safe_retrieve_chunks(
    query_string: str,
    model_id: str = None,
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None,
    score_threshold: float = 0.2,
    min_return: int = 3,
    max_return: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Safely retrieve chunks with proper embedding handling based on environment.
    
    This function implements the correct pattern for handling embedding:
    - In subprocess mode: Pass raw query string to worker (worker embeds it)
    - In in-process mode: Embed first, then pass embedding to FAISS
    
    Args:
        query_string: The raw user query (string)
        model_id: Model identifier (default: DEFAULT_MODEL_ID)
        top_k: Number of results to retrieve
        filters: Metadata filters to apply
        score_threshold: Minimum similarity score
        min_return: Minimum number of results to return
        max_return: Maximum number of results to return
        
    Returns:
        List of chunks with metadata and scores
        
    Raises:
        ValueError: If query_string is empty or invalid
        RuntimeError: If retrieval fails
    """
    if not query_string or not query_string.strip():
        raise ValueError("Query string cannot be empty")
    
    model_id = model_id or DEFAULT_MODEL_ID
    
    with QueryContext(model_id) as ctx:
        log_with_context(
            logger,
            logging.INFO,
            "SafeRetriever",
            "Starting safe chunk retrieval",
            {
                "query_length": len(query_string),
                "model_id": model_id,
                "top_k": top_k,
                "use_subprocess": USE_FAISS_SUBPROCESS
            }
        )
        
        try:
            if USE_FAISS_SUBPROCESS:
                # Subprocess mode: pass raw query string to worker (worker embeds it)
                log_with_context(
                    logger,
                    logging.INFO,
                    "SafeRetriever",
                    "Using subprocess mode",
                    {"query_preview": query_string[:50] + "..."}
                )
                
                chunks = retrieve_chunks_dual_process(
                    query_string,  # raw string — worker embeds it
                    model_id=model_id,
                    top_k=top_k,
                    filters=filters,
                    score_threshold=score_threshold,
                    min_return=min_return,
                    max_return=max_return
                )
            else:
                # In-process mode: embed first, then query
                log_with_context(
                    logger,
                    logging.INFO,
                    "SafeRetriever",
                    "Using in-process mode",
                    {"query_preview": query_string[:50] + "..."}
                )
                
                query_embedding = embed_query_safe(query_string, model_id=model_id)
                
                chunks = query_index(
                    query_embedding,
                    top_k=top_k,
                    filters=filters,
                    model_id=model_id,
                    score_threshold=score_threshold,
                    min_return=min_return,
                    max_return=max_return
                )
            
            log_with_context(
                logger,
                logging.INFO,
                "SafeRetriever",
                "Retrieval completed",
                {
                    "chunk_count": len(chunks),
                    "mean_score": np.mean([c["score"] for c in chunks]) if chunks else 0
                }
            )
            
            return chunks
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "SafeRetriever",
                "Retrieval failed",
                {
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise RuntimeError(f"Safe retrieval failed: {e}")


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