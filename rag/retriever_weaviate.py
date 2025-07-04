"""
WeaviateRetriever module for NobelLM RAG pipeline.

This module provides a Weaviate-based retriever that implements the BaseRetriever interface,
allowing seamless integration with the existing RAG pipeline while using Weaviate as the
vector database backend.
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

from rag.retriever import BaseRetriever
from rag.model_config import get_model_config, DEFAULT_MODEL_ID
from rag.query_weaviate import query_weaviate
from rag.logging_utils import get_module_logger, log_with_context, QueryContext
from rag.validation import validate_query_string, validate_retrieval_parameters, validate_filters

logger = get_module_logger(__name__)

# Model caching to avoid repeated loads
_model_cache = {}

def get_model(model_id: str):
    """Get cached embedding model or load it if not cached."""
    if model_id not in _model_cache:
        config = get_model_config(model_id)
        _model_cache[model_id] = SentenceTransformer(config["model_name"])
    return _model_cache[model_id]


class WeaviateRetriever(BaseRetriever):
    """
    Weaviate-based retriever that implements the BaseRetriever interface.
    
    This retriever uses Weaviate as the vector database backend while maintaining
    compatibility with the existing RAG pipeline architecture.
    """

    def __init__(self, model_id: str = None):
        """
        Initialize the Weaviate retriever.
        
        Args:
            model_id: Model identifier (default: DEFAULT_MODEL_ID)
        """
        # Handle None by using default model ID
        if model_id is None:
            model_id = DEFAULT_MODEL_ID
            
        # Validate model_id
        from rag.validation import validate_model_id
        validate_model_id(model_id, context="WeaviateRetriever")
            
        self.model_id = model_id
        
        # Load embedding model for query processing
        # Note: This retriever embeds queries locally, not using Weaviate's inference module
        self.model = get_model(self.model_id)
        
        # Get embedding dimension for logging and validation
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        log_with_context(
            logger,
            logging.INFO,
            "WeaviateRetriever",
            "Initialized Weaviate retriever",
            {
                "model_id": self.model_id,
                "embedding_dim": self.embedding_dim
            }
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.2,
        min_return: int = 3,
        max_return: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks using Weaviate vector search.
        
        Args:
            query: The query string
            top_k: Number of chunks to retrieve
            filters: Optional metadata filters
            score_threshold: Minimum similarity score
            min_return: Minimum number of chunks to return
            max_return: Maximum number of chunks to return
            
        Returns:
            List of chunk dictionaries with metadata and scores
        """
        with QueryContext(self.model_id):
            # Validate inputs
            validate_query_string(query, context="WeaviateRetriever.retrieve")
            validate_retrieval_parameters(
                top_k=top_k,
                score_threshold=score_threshold,
                min_return=min_return,
                max_return=max_return,
                context="WeaviateRetriever.retrieve"
            )
            validate_filters(filters, context="WeaviateRetriever.retrieve")
            
            log_with_context(
                logger,
                logging.INFO,
                "WeaviateRetriever",
                "Starting Weaviate retrieval",
                {
                    "query": query,
                    "top_k": top_k,
                    "score_threshold": score_threshold,
                    "has_filters": filters is not None
                }
            )
            
            try:
                # Use the existing query_weaviate function
                chunks = query_weaviate(
                    query_text=query,
                    filters=filters,
                    top_k=top_k,
                    score_threshold=score_threshold
                )
                
                # Handle edge case of None or malformed response
                if not chunks:
                    chunks = []
                    logger.warning("Weaviate returned None or empty response, using empty list")
                
                # Apply min/max return constraints
                if min_return and len(chunks) < min_return:
                    logger.warning(f"Weaviate returned {len(chunks)} chunks, but min_return={min_return}")
                
                if max_return and len(chunks) > max_return:
                    chunks = chunks[:max_return]
                    logger.info(f"Truncated results to {max_return} chunks")
                
                log_with_context(
                    logger,
                    logging.INFO,
                    "WeaviateRetriever",
                    "Retrieval completed",
                    {
                        "chunks_returned": len(chunks),
                        "mean_score": np.mean([c.get("score", 0) for c in chunks]) if chunks else 0
                    }
                )
                
                return chunks
                
            except Exception as e:
                log_with_context(
                    logger,
                    logging.ERROR,
                    "WeaviateRetriever",
                    "Retrieval failed",
                    {
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                raise
