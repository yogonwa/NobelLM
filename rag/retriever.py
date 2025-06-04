"""
retriever.py

Model-aware query_index function for the NobelLM RAG pipeline.
Loads the appropriate FAISS index and metadata based on the model config.
Used at runtime to retrieve top-k relevant chunks for a given query embedding.
Supports pre-retrieval metadata filtering for efficient, accurate, and explainable search.
"""

import os
import json
import logging
from typing import List, Dict, Tuple, Any, Optional
import numpy as np
import faiss
from rag.model_config import get_model_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Cache loaded index and metadata to avoid reloading on every call
_loaded_resources: Dict[str, Tuple[faiss.Index, List[Dict[str, Any]]]] = {}


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
    model_id: str = "bge-large",
    top_k: int = 3,
    min_score: float = 0.2,
    filters: Optional[Dict[str, Any]] = None,
    index_path: Optional[str] = None,
    metadata_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Query the FAISS index for a given model using a normalized query embedding.
    Supports pre-retrieval metadata filtering: only chunks matching filters are searched.
    Returns top-k results with metadata and similarity scores.
    """
    # Defensive: Check for invalid vector
    if is_invalid_vector(query_embedding):
        raise ValueError("Embedding is invalid (zero vector, NaN, or wrong shape)")
    # Defensive: Ensure correct shape and dtype
    if query_embedding.ndim == 1:
        query_embedding = query_embedding.reshape(1, -1)
    if query_embedding.dtype != np.float32:
        query_embedding = query_embedding.astype(np.float32)

    if index_path and metadata_path:
        # Load index/metadata directly from provided paths (no cache)
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Index file not found: {index_path}")
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
        index = faiss.read_index(index_path)
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = [json.loads(line) for line in f]
    else:
        index, metadata = load_index_and_metadata(model_id)
    logger = logging.getLogger(__name__)
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

    # Extract vectors for filtered indices
    all_vectors = index.reconstruct_n(0, index.ntotal)  # shape: (N, D)
    filtered_vectors = all_vectors[valid_indices]
    faiss.normalize_L2(filtered_vectors)

    # Defensive: Check filtered_vectors shape
    if filtered_vectors.ndim != 2 or query_embedding.ndim != 2:
        raise ValueError(f"Vectors have unexpected shape: filtered_vectors={filtered_vectors.shape}, query_embedding={query_embedding.shape}")

    # Search over filtered vectors (cosine similarity via inner product)
    # Compute scores manually
    scores = np.dot(filtered_vectors, query_embedding[0])  # shape: (num_filtered,)
    top_indices = scores.argsort()[::-1][:top_k]
    results = []
    for rank, i in enumerate(top_indices):
        if scores[i] >= min_score:
            result = filtered_metadata[i].copy()
            result["score"] = float(scores[i])
            result["rank"] = rank
            results.append(result)
    return results 