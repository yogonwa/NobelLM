"""
WeaviateRetriever module for NobelLM RAG pipeline.

- Implements a Weaviate-based retriever that conforms to the BaseRetriever interface.
- Enables backend-agnostic retrieval: the pipeline can use either Weaviate or FAISS transparently.
- Handles model loading, input validation, and result normalization.
- Used by the retriever factory in `rag/retriever.py`.
- Calls low-level Weaviate query logic in `rag/query_weaviate.py`.

Configuration:
- Enable Weaviate by setting the appropriate config/env vars (e.g., `USE_WEAVIATE=1`, `WEAVIATE_URL`, `WEAVIATE_API_KEY`).
- Embedding is always performed locally using the configured model (not via Weaviate inference module).
- If Weaviate is not enabled/configured, the pipeline falls back to FAISS retrievers.

Related files:
- rag/retriever.py: Retriever factory and interface.
- rag/query_weaviate.py: Low-level Weaviate query logic.
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

# Import unified embedding service
from rag.modal_embedding_service import embed_query


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
        
        # Get embedding dimension for logging and validation
        config = get_model_config(self.model_id)
        self.embedding_dim = config["embedding_dim"]
        
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
