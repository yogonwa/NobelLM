"""
Retriever module for NobelLM RAG pipeline.

This module provides a unified interface for retrieving chunks from the FAISS index,
with support for both in-process and subprocess retrieval modes. The retriever requires
a FAISS IndexFlatIP index for metadata filtering - other index types (IVF, PQ, HNSW)
are not supported for filtered queries.

Key features:
- Mode-agnostic retrieval (in-process vs subprocess)
- Consistent score threshold filtering
- Metadata filtering (requires IndexFlatIP)
- Model-aware configuration
"""

import os
import json
import logging
from typing import List, Dict, Tuple, Any, Optional
import numpy as np
import faiss
from rag.model_config import get_model_config, DEFAULT_MODEL_ID
from sentence_transformers import SentenceTransformer
from rag.dual_process_retriever import retrieve_chunks_dual_process
from abc import ABC, abstractmethod
from .utils import filter_top_chunks
from .faiss_index import load_index, health_check
from .logging_utils import get_module_logger, log_with_context, QueryContext

# Get module logger
logger = get_module_logger(__name__)

# Cache loaded index and metadata to avoid reloading on every call
_loaded_resources: Dict[str, Tuple[faiss.Index, List[Dict[str, Any]]]] = {}

def is_supported_index(index: faiss.Index) -> bool:
    """
    Check if the FAISS index type is supported for metadata filtering.
    
    Currently, only IndexFlatIP is supported because it provides:
    1. Direct similarity search (no quantization)
    2. Support for reconstruct_n() needed for metadata filtering
    3. Guaranteed score consistency
    
    Args:
        index: The FAISS index to check
        
    Returns:
        bool: True if the index is IndexFlatIP, False otherwise
    """
    return isinstance(index, faiss.IndexFlatIP)

def is_invalid_vector(vec: np.ndarray) -> bool:
    return (
        np.isnan(vec).any()
        or np.isinf(vec).any()
        or np.allclose(vec, 0.0)
    )


def load_index_and_metadata(model_id: str) -> Tuple[faiss.Index, List[Dict]]:
    """
    Loads and caches the FAISS index and metadata for the given model_id.
    """
    if model_id in _loaded_resources:
        return _loaded_resources[model_id]

    config = get_model_config(model_id)
    index_path = config["index_path"]
    metadata_path = config["metadata_path"]

    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Index file not found: {index_path}")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    index = faiss.read_index(index_path)
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = [json.loads(line) for line in f]

    _loaded_resources[model_id] = (index, metadata)
    return index, metadata


def query_index(
    query_embedding: np.ndarray,
    top_k: int,
    filters: Optional[Dict[str, Any]] = None,
    model_id: Optional[str] = None,
    score_threshold: float = 0.2,
    min_return: Optional[int] = None,
    max_return: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Query the FAISS index for relevant chunks, with optional metadata filtering.
    
    This function requires a FAISS IndexFlatIP index for metadata filtering.
    Other index types (IVF, PQ, HNSW) are not supported for filtered queries
    because they may not support reconstruct_n() or provide consistent scores.
    
    The function applies a score threshold to filter out low-quality matches,
    while ensuring a minimum number of results are returned. If fewer than
    min_return chunks pass the threshold, the top min_return chunks are returned
    regardless of score.
    
    Args:
        query_embedding: The query embedding vector
        top_k: Number of results to retrieve
        filters: Optional metadata filters to apply
        model_id: Optional model identifier for model-specific index
        score_threshold: Minimum similarity score (default: 0.2)
        min_return: Minimum number of chunks to return
        max_return: Maximum number of chunks to return
        
    Returns:
        List of chunk dictionaries with metadata and scores
        
    Raises:
        ValueError: If top_k is not provided or index type is unsupported
        FileNotFoundError: If index or metadata files are missing
    """
    if top_k is None:
        raise ValueError("top_k must be provided")
    # Defensive: Check for invalid vector
    if is_invalid_vector(query_embedding):
        raise ValueError("Embedding is invalid (zero vector, NaN, or wrong shape)")
    # Defensive: Ensure correct shape and dtype
    if query_embedding.ndim == 1:
        query_embedding = query_embedding.reshape(1, -1)
    if query_embedding.dtype != np.float32:
        query_embedding = query_embedding.astype(np.float32)

    if model_id:
        index, metadata = load_index_and_metadata(model_id)
    else:
        raise ValueError("model_id must be provided")

    # Verify index type is supported
    if not is_supported_index(index):
        raise ValueError(
            f"Unsupported FAISS index type: {type(index).__name__}. "
            "Only IndexFlatIP (cosine similarity) is supported as it guarantees "
            "reconstruct_n support and direct similarity search."
        )

    logger.info(f"FAISS index is trained: {getattr(index, 'is_trained', 'N/A')}, total vectors: {getattr(index, 'ntotal', 'N/A')}")
    logger.info(f"Query embedding shape: {query_embedding.shape}, dtype: {query_embedding.dtype}")
    logger.info(f"First few values: {query_embedding[0][:5]}")
    faiss.normalize_L2(query_embedding)

    # --- Pre-retrieval metadata filtering ---
    if filters:
        filtered_metadata = [m for m in metadata if all(m.get(k) == v for k, v in filters.items())]
    else:
        filtered_metadata = metadata

    if not filtered_metadata:
        return []  # No results match filter

    # Map chunk_id to index in metadata (which matches FAISS vector order)
    id_to_idx = {meta["chunk_id"]: i for i, meta in enumerate(metadata)}
    valid_indices = [id_to_idx[m["chunk_id"]] for m in filtered_metadata]

    # After filtering
    logger.info(f"[RAG][ShapeCheck] valid_indices: {valid_indices}, count: {len(valid_indices)}")

    if not filters:
        # If no filters, use direct FAISS search (faster)
        scores, indices = index.search(query_embedding, top_k)
        scores = scores[0]  # Remove batch dimension
        indices = indices[0]
        results = []
        for rank, (score, idx) in enumerate(zip(scores, indices)):
            if score >= score_threshold:
                result = metadata[idx].copy()
                result["score"] = float(score)
                result["rank"] = rank
                results.append(result)
        return results
    else:
        # With filters, we need to reconstruct vectors and do manual scoring
        # This is safe because we verified index type is IndexFlatIP
        all_vectors = index.reconstruct_n(0, index.ntotal)
        filtered_vectors = all_vectors[valid_indices]
        if filtered_vectors.ndim == 1:
            logger.warning("[RAG][ShapeCheck] filtered_vectors was 1D, reshaping to 2D.")
            filtered_vectors = filtered_vectors.reshape(1, -1)
        assert filtered_vectors.ndim == 2, f"filtered_vectors shape: {filtered_vectors.shape}"
        faiss.normalize_L2(filtered_vectors)
        logger.info(f"[RAG][ShapeCheck] filtered_vectors shape: {filtered_vectors.shape}, dtype: {filtered_vectors.dtype}")

        # Search over filtered vectors (cosine similarity via inner product)
        scores = np.dot(filtered_vectors, query_embedding[0])  # shape: (num_filtered,)
        logger.info(f"[RAG][ShapeCheck] scores shape: {scores.shape}, dtype: {scores.dtype}")
        if np.isscalar(scores):
            logger.warning("[RAG][ShapeCheck] scores was scalar, converting to 1D array.")
            scores = np.array([scores])
        if scores.ndim == 0:
            scores = scores.reshape(1)
        assert scores.ndim == 1, f"scores shape: {scores.shape}"
        logger.info(f"[RAG][ShapeCheck] Number of chunks after filtering: {len(scores)}")
        top_indices = scores.argsort()[::-1][:top_k]
        logger.info(f"Top 10 scores: {scores[top_indices][:10]}")
        logger.info(f"Top 10 chunk IDs: {[filtered_metadata[i]['chunk_id'] for i in top_indices[:10]]}")
        logger.info(f"Number of chunks before score threshold: {len(filtered_metadata)}")
        logger.info(f"Number of chunks after score threshold: {len([s for s in scores if s >= score_threshold])}")
        results = []
        for rank, i in enumerate(top_indices):
            if scores[i] >= score_threshold:
                result = filtered_metadata[i].copy()
                result["score"] = float(scores[i])
                result["rank"] = rank
                results.append(result)
        return results


class BaseRetriever(ABC):
    """Abstract base class for all retrievers."""

    def __init__(self, model_id: str = None):
        """
        Initialize the retriever.

        Args:
            model_id: Model identifier (default: DEFAULT_MODEL_ID)
        """
        # Handle None by using default model ID
        if model_id is None:
            model_id = DEFAULT_MODEL_ID
            
        self.model_id = model_id
        self.model, self.embedding_dim = self._validate_model_config(model_id)
        log_with_context(
            logger,
            logging.INFO,
            "Retriever",
            "Initialized retriever",
            {
                "model_id": model_id,
                "embedding_dim": self.embedding_dim
            }
        )

    @abstractmethod
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
        Retrieve chunks for a query.

        Args:
            query: The query string
            top_k: Number of chunks to retrieve (default: 5)
            filters: Optional metadata filters
            score_threshold: Minimum similarity score (default: 0.2)
            min_return: Minimum number of chunks to return (default: 3)
            max_return: Optional maximum number of chunks to return

        Returns:
            List of chunks, filtered by score threshold
        """
        pass

    def _validate_model_config(self, model_id: str) -> Tuple[SentenceTransformer, int]:
        """
        Validate model config and return model and embedding dimension.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Tuple of (model, embedding_dim)
            
        Raises:
            ValueError: If model config is invalid or dimensions don't match
        """
        with QueryContext(model_id):
            config = get_model_config(model_id)
            if not config:
                log_with_context(
                    logger,
                    logging.ERROR,
                    "Retriever",
                    "No config found for model",
                    {"model_id": model_id}
                )
                raise ValueError(f"No config found for model_id: {model_id}")
                
            # Load model and check dimensions
            model = SentenceTransformer(config["model_name"])
            model_dim = model.get_sentence_embedding_dimension()
            
            # Load index and check dimensions
            index = load_index(model_id)
            if not index.is_trained:
                log_with_context(
                    logger,
                    logging.ERROR,
                    "Retriever",
                    "FAISS index is not trained",
                    {"model_id": model_id}
                )
                raise ValueError(f"FAISS index for {model_id} is not trained")
                
            index_dim = index.d
            if model_dim != index_dim:
                log_with_context(
                    logger,
                    logging.ERROR,
                    "Retriever",
                    "Model and index dimensions don't match",
                    {
                        "model_id": model_id,
                        "model_dim": model_dim,
                        "index_dim": index_dim
                    }
                )
                raise ValueError(
                    f"Model dimension ({model_dim}) does not match index dimension ({index_dim}) "
                    f"for model_id: {model_id}"
                )
                
            return model, model_dim


class InProcessRetriever(BaseRetriever):
    """Retriever that runs FAISS search in-process."""

    def __init__(self, model_id: str = None):
        """Initialize the in-process retriever."""
        super().__init__(model_id)
        # Load index and metadata for in-process retrieval
        self.index, self.metadata = load_index_and_metadata(self.model_id)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.2,
        min_return: int = 3,
        max_return: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve chunks using in-process FAISS search."""
        from rag.safe_retriever import safe_retrieve_chunks
        
        # Use the safe retrieval pattern that handles embedding correctly
        chunks = safe_retrieve_chunks(
            query_string=query,
            model_id=self.model_id,
            top_k=top_k,
            filters=filters,
            score_threshold=score_threshold,
            min_return=min_return,
            max_return=max_return
        )
        
        # Apply consistent filtering
        return filter_top_chunks(
            chunks,
            score_threshold=score_threshold,
            min_return=min_return,
            max_return=max_return
        )


class SubprocessRetriever(BaseRetriever):
    """Retriever that runs FAISS search in a subprocess."""

    def __init__(self, model_id: str = None):
        """Initialize the subprocess retriever."""
        super().__init__(model_id)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.2,
        min_return: int = 3,
        max_return: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve chunks using subprocess FAISS search."""
        from rag.safe_retriever import safe_retrieve_chunks
        
        # Use the safe retrieval pattern that handles embedding correctly
        chunks = safe_retrieve_chunks(
            query_string=query,
            model_id=self.model_id,
            top_k=top_k,
            filters=filters,
            score_threshold=score_threshold,
            min_return=min_return,
            max_return=max_return
        )
        
        return chunks


def get_mode_aware_retriever(model_id: str = None) -> BaseRetriever:
    """
    Get the appropriate retriever based on environment.

    Args:
        model_id: Model identifier (default: DEFAULT_MODEL_ID)

    Returns:
        BaseRetriever implementation (InProcessRetriever or SubprocessRetriever)
    """
    use_subprocess = os.getenv("NOBELLM_USE_FAISS_SUBPROCESS") == "1"
    if use_subprocess:
        log_with_context(
            logger,
            logging.INFO,
            "Retriever",
            "Using subprocess mode",
            {"env_var": "NOBELLM_USE_FAISS_SUBPROCESS=1"}
        )
        return SubprocessRetriever(model_id)
    else:
        log_with_context(
            logger,
            logging.INFO,
            "Retriever",
            "Using in-process mode"
        )
        return InProcessRetriever(model_id) 