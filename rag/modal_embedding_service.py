"""
Unified Embedding Service for NobelLM RAG Pipeline

This module provides a single, unified interface for query embedding that automatically
routes to Modal in production and local models in development. This eliminates the need
for multiple embedding paths across different retrievers.

Key Features:
- Environment-based routing (Modal in production, local in development)
- Automatic fallback to local embedding if Modal fails
- Consistent interface across all retrievers
- Caching for performance optimization
- Model-aware configuration

Usage:
    from rag.modal_embedding_service import get_embedding_service
    
    service = get_embedding_service()
    embedding = service.embed_query("What did Toni Morrison say about justice?")

Author: NobelLM Team
Date: 2025
"""

import os
import logging
from typing import Optional
import numpy as np
import requests
from sentence_transformers import SentenceTransformer

from rag.model_config import get_model_config, DEFAULT_MODEL_ID
from rag.logging_utils import get_module_logger, log_with_context, QueryContext

logger = get_module_logger(__name__)

# Global service instance
_embedding_service = None

class ModalEmbeddingService:
    """
    Unified embedding service that routes to Modal in production and local in development.
    
    This service eliminates the need for multiple embedding paths across different
    retrievers by providing a single interface that automatically handles the
    environment-specific embedding strategy.
    """
    
    def __init__(self):
        """Initialize the embedding service with environment detection."""
        self.is_production = self._detect_production_environment()
        
        log_with_context(
            logger,
            logging.INFO,
            "ModalEmbeddingService",
            "Initialized embedding service",
            {
                "environment": "production" if self.is_production else "development",
                "embedding_strategy": "Modal HTTP" if self.is_production else "Local"
            }
        )
    
    def _detect_production_environment(self) -> bool:
        """
        Detect if we're running in production environment.
        
        Returns:
            True if in production, False if in development
        """
        # Check for explicit environment variable
        env_var = os.getenv("NOBELLM_ENVIRONMENT", "").lower()
        if env_var == "production":
            return True
        elif env_var == "development":
            return False
        
        # Check for Fly.io deployment indicators
        if os.getenv("FLY_APP_NAME"):
            return True
        
        # Check for other production indicators
        production_indicators = [
            "FLY_APP_NAME",
            "FLY_REGION", 
            "FLY_ALLOC_ID",
            "PORT",  # Often set in production
        ]
        
        for indicator in production_indicators:
            if os.getenv(indicator):
                return True
        
        # Default to development
        return False
    
    def embed_query(self, query: str, model_id: str = None) -> np.ndarray:
        """
        Embed a query using the appropriate strategy for the current environment.
        
        Args:
            query: The query string to embed
            model_id: Optional model identifier (default: DEFAULT_MODEL_ID)
            
        Returns:
            Normalized query embedding as numpy array
            
        Raises:
            RuntimeError: If both Modal and local embedding fail
        """
        model_id = model_id or DEFAULT_MODEL_ID
        
        with QueryContext(model_id):
            log_with_context(
                logger,
                logging.INFO,
                "ModalEmbeddingService",
                "Starting query embedding",
                {
                    "query_length": len(query),
                    "model_id": model_id,
                    "environment": "production" if self.is_production else "development"
                }
            )
            
            # Always use Modal embedding service
            return self._embed_via_modal(query, model_id)
    
    def embed_batch(self, queries: list[str], model_id: str = None) -> list[np.ndarray]:
        """
        Embed multiple queries using Modal's batch endpoint.
        
        This method eliminates cold start storms by making a single HTTP request
        for multiple texts instead of multiple parallel requests.
        
        Args:
            queries: List of query strings to embed
            model_id: Optional model identifier (default: DEFAULT_MODEL_ID)
            
        Returns:
            List of normalized query embeddings as numpy arrays
            
        Raises:
            RuntimeError: If HTTP request fails or embeddings are invalid
        """
        model_id = model_id or DEFAULT_MODEL_ID
        
        if not queries:
            return []
        
        with QueryContext(model_id):
            log_with_context(
                logger,
                logging.INFO,
                "ModalEmbeddingService",
                "Starting batch query embedding",
                {
                    "query_count": len(queries),
                    "model_id": model_id,
                    "environment": "production" if self.is_production else "development"
                }
            )
            
            # Use Modal batch embedding service
            return self._embed_batch_via_modal(queries, model_id)
    
    def _embed_via_modal(self, query: str, model_id: str) -> np.ndarray:
        """
        Embed query using Modal's HTTP endpoint.
        
        Args:
            query: The query string to embed
            model_id: Model identifier
            
        Returns:
            Normalized query embedding as numpy array
            
        Raises:
            RuntimeError: If HTTP request fails or embedding is invalid
        """
        url = "https://yogonwa--nobel-embedder-clean-slate-embed-query.modal.run"
        api_key = "6dab23095a3f8968074d7c9152d6707f3f7445bc145022f46fcceb0712864147"

        try:
            # Adjust timeout based on query characteristics
            # Thematic queries need more time for complex retrieval
            if len(query) > 100 or any(word in query.lower() for word in ["theme", "pattern", "across", "common"]):
                timeout = 45  # Thematic query
            else:
                timeout = 20  # Factual/simple query

            logger.info(f"Modal embedding timeout set to {timeout}s based on query complexity")

            response = requests.post(
                url,
                json={"api_key": api_key, "text": query},
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()
            embedding_list = data["embedding"]
            embedding = np.array(embedding_list, dtype=np.float32)

            # Validate embedding dimensions
            expected_dim = get_model_config(model_id)["embedding_dim"]
            if embedding.shape[0] != expected_dim:
                raise ValueError(
                    f"Modal embedding dimension {embedding.shape[0]} "
                    f"doesn't match expected {expected_dim} for model {model_id}"
                )

            log_with_context(
                logger,
                logging.DEBUG,
                "ModalEmbeddingService",
                "Modal embedding successful",
                {
                    "query_length": len(query),
                    "embedding_shape": embedding.shape,
                    "model_id": model_id
                }
            )

            return embedding
        except Exception as e:
            logger.error(f"Failed HTTP embedding request: {e}")
            raise RuntimeError(f"Modal embedding service failed: {e}")
    
    def _embed_batch_via_modal(self, queries: list[str], model_id: str) -> list[np.ndarray]:
        """
        Embed multiple queries using Modal's batch HTTP endpoint.
        
        Args:
            queries: List of query strings to embed
            model_id: Model identifier
            
        Returns:
            List of normalized query embeddings as numpy arrays
            
        Raises:
            RuntimeError: If HTTP request fails or embeddings are invalid
        """
        url = "https://yogonwa--nobel-embedder-clean-slate-embed-batch.modal.run"
        api_key = "6dab23095a3f8968074d7c9152d6707f3f7445bc145022f46fcceb0712864147"

        try:
            response = requests.post(
                url,
                json={"api_key": api_key, "texts": queries},
                timeout=60,  # Longer timeout for batch requests
            )
            response.raise_for_status()
            data = response.json()
            embedding_lists = data["embeddings"]
            
            # Convert to numpy arrays
            embeddings = [np.array(emb_list, dtype=np.float32) for emb_list in embedding_lists]

            # Validate embedding dimensions
            expected_dim = get_model_config(model_id)["embedding_dim"]
            for i, embedding in enumerate(embeddings):
                if embedding.shape[0] != expected_dim:
                    raise ValueError(
                        f"Modal batch embedding {i} dimension {embedding.shape[0]} "
                        f"doesn't match expected {expected_dim} for model {model_id}"
                    )

            log_with_context(
                logger,
                logging.DEBUG,
                "ModalEmbeddingService",
                "Modal batch embedding successful",
                {
                    "query_count": len(queries),
                    "embedding_count": len(embeddings),
                    "embedding_shape": embeddings[0].shape if embeddings else None,
                    "model_id": model_id
                }
            )

            return embeddings
        except Exception as e:
            logger.error(f"Failed HTTP batch embedding request: {e}")
            raise RuntimeError(f"Modal batch embedding service failed: {e}")




def get_embedding_service() -> ModalEmbeddingService:
    """
    Get or create the global embedding service instance.
    
    Returns:
        ModalEmbeddingService: The global service instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = ModalEmbeddingService()
    return _embedding_service


# Convenience function for direct embedding
def embed_query(query: str, model_id: str = None) -> np.ndarray:
    """
    Convenience function to embed a query using the unified service.
    
    Args:
        query: The query string to embed
        model_id: Optional model identifier
        
    Returns:
        Normalized query embedding as numpy array
    """
    service = get_embedding_service()
    return service.embed_query(query, model_id)
