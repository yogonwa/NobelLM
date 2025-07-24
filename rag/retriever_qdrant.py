"""
QdrantRetriever module for NobelLM RAG pipeline.

- Implements a Qdrant-based retriever that conforms to the BaseRetriever interface.
- Enables backend-agnostic retrieval: the pipeline can use Qdrant transparently.
- Handles input validation and result normalization.
- Used by the retriever factory in `rag/retriever.py`.
- Calls low-level Qdrant query logic in `rag/query_qdrant.py`.
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from rag.retriever import BaseRetriever
from rag.model_config import get_model_config, DEFAULT_MODEL_ID
from rag.query_qdrant import query_qdrant, query_qdrant_with_embedding
from rag.logging_utils import get_module_logger, log_with_context, QueryContext
from rag.validation import validate_query_string, validate_retrieval_parameters, validate_filters

logger = get_module_logger(__name__)

# Import unified embedding service
from rag.modal_embedding_service import embed_query

class QdrantRetriever(BaseRetriever):
    """
    Qdrant-based retriever that implements the BaseRetriever interface.
    This retriever uses Qdrant as the vector database backend while maintaining
    compatibility with the existing RAG pipeline architecture.
    """
    def __init__(self, model_id: str = None):
        """
        Initialize the Qdrant retriever.
        Args:
            model_id: Model identifier (default: DEFAULT_MODEL_ID)
        """
        if model_id is None:
            model_id = DEFAULT_MODEL_ID
        from rag.validation import validate_model_id
        validate_model_id(model_id, context="QdrantRetriever")
        self.model_id = model_id
        config = get_model_config(self.model_id)
        self.embedding_dim = config["embedding_dim"]
        log_with_context(
            logger,
            logging.INFO,
            "QdrantRetriever",
            "Initialized Qdrant retriever",
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
        Retrieve chunks using Qdrant vector search.
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
            validate_query_string(query, context="QdrantRetriever.retrieve")
            validate_retrieval_parameters(
                top_k=top_k,
                score_threshold=score_threshold,
                min_return=min_return,
                max_return=max_return,
                context="QdrantRetriever.retrieve"
            )
            validate_filters(filters, context="QdrantRetriever.retrieve")
            log_with_context(
                logger,
                logging.INFO,
                "QdrantRetriever",
                "Starting Qdrant retrieval",
                {
                    "query": query,
                    "top_k": top_k,
                    "score_threshold": score_threshold,
                    "has_filters": filters is not None
                }
            )
            try:
                chunks = query_qdrant(
                    query_text=query,
                    filters=filters,
                    top_k=top_k,
                    score_threshold=score_threshold
                )
                if not chunks:
                    chunks = []
                    logger.warning("Qdrant returned None or empty response, using empty list")
                if min_return and len(chunks) < min_return:
                    logger.warning(f"Qdrant returned {len(chunks)} chunks, but min_return={min_return}")
                if max_return and len(chunks) > max_return:
                    chunks = chunks[:max_return]
                    logger.info(f"Truncated results to {max_return} chunks")
                log_with_context(
                    logger,
                    logging.INFO,
                    "QdrantRetriever",
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
                    "QdrantRetriever",
                    "Retrieval failed",
                    {
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                raise

    def retrieve_with_embedding(
        self,
        embedding: np.ndarray,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.2,
        min_return: int = 3,
        max_return: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks using Qdrant vector search with a pre-computed embedding.
        Args:
            embedding: Pre-computed query embedding as numpy array
            top_k: Number of chunks to retrieve
            filters: Optional metadata filters
            score_threshold: Minimum similarity score
            min_return: Minimum number of chunks to return
            max_return: Maximum number of chunks to return
        Returns:
            List of chunk dictionaries with metadata and scores
        """
        with QueryContext(self.model_id):
            if embedding is None or embedding.size == 0:
                raise ValueError("Embedding cannot be None or empty")
            validate_retrieval_parameters(
                top_k=top_k,
                score_threshold=score_threshold,
                min_return=min_return,
                max_return=max_return,
                context="QdrantRetriever.retrieve_with_embedding"
            )
            validate_filters(filters, context="QdrantRetriever.retrieve_with_embedding")
            log_with_context(
                logger,
                logging.INFO,
                "QdrantRetriever",
                "Starting Qdrant retrieval with pre-computed embedding",
                {
                    "embedding_shape": embedding.shape,
                    "top_k": top_k,
                    "score_threshold": score_threshold,
                    "has_filters": filters is not None
                }
            )
            try:
                embedding_list = embedding.tolist()
                chunks = query_qdrant_with_embedding(
                    embedding=embedding_list,
                    top_k=top_k,
                    filters=filters,
                    score_threshold=score_threshold
                )
                if not chunks:
                    chunks = []
                    logger.warning("Qdrant returned None or empty response, using empty list")
                if min_return and len(chunks) < min_return:
                    logger.warning(f"Qdrant returned {len(chunks)} chunks, but min_return={min_return}")
                if max_return and len(chunks) > max_return:
                    chunks = chunks[:max_return]
                    logger.info(f"Truncated results to {max_return} chunks")
                log_with_context(
                    logger,
                    logging.INFO,
                    "QdrantRetriever",
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
                    "QdrantRetriever",
                    "Retrieval failed",
                    {
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                raise
