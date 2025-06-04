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
from sentence_transformers import SentenceTransformer
from rag.dual_process_retriever import retrieve_chunks_dual_process

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

    # After filtering
    logger.info(f"[RAG][ShapeCheck] valid_indices: {valid_indices}, count: {len(valid_indices)}")
    all_vectors = index.reconstruct_n(0, index.ntotal)
    filtered_vectors = all_vectors[valid_indices]
    if filtered_vectors.ndim == 1:
        logger.warning("[RAG][ShapeCheck] filtered_vectors was 1D, reshaping to 2D.")
        filtered_vectors = filtered_vectors.reshape(1, -1)
    assert filtered_vectors.ndim == 2, f"filtered_vectors shape: {filtered_vectors.shape}"
    faiss.normalize_L2(filtered_vectors)
    logger.info(f"[RAG][ShapeCheck] filtered_vectors shape: {filtered_vectors.shape}, dtype: {filtered_vectors.dtype}")

    # Search over filtered vectors (cosine similarity via inner product)
    # Compute scores manually
    scores = np.dot(filtered_vectors, query_embedding[0])  # shape: (num_filtered,)
    # After scoring
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
    logger.info(f"Number of chunks after score threshold: {len([s for s in scores if s >= min_score])}")
    results = []
    for rank, i in enumerate(top_indices):
        if scores[i] >= min_score:
            result = filtered_metadata[i].copy()
            result["score"] = float(scores[i])
            result["rank"] = rank
            results.append(result)
    return results


class BaseRetriever:
    def retrieve(self, query: str, top_k: int = 5, filters: dict = None) -> List[Dict]:
        raise NotImplementedError


class InProcessRetriever(BaseRetriever):
    def __init__(self, model_id: str):
        config = get_model_config(model_id)
        self.model_id = model_id
        self.embedder = SentenceTransformer(config["model_name"])
    def retrieve(self, query: str, top_k=5, filters=None):
        emb = self.embedder.encode([query], normalize_embeddings=True)[0]
        return query_index(emb, model_id=self.model_id, top_k=top_k, filters=filters)


class SubprocessRetriever(BaseRetriever):
    def __init__(self, model_id: str):
        self.model_id = model_id
    def retrieve(self, query: str, top_k=5, filters=None):
        return retrieve_chunks_dual_process(query, model_id=self.model_id, top_k=top_k, filters=filters)


def get_mode_aware_retriever(model_id: str) -> BaseRetriever:
    if os.getenv("NOBELLM_USE_FAISS_SUBPROCESS") == "1":
        return SubprocessRetriever(model_id)
    else:
        return InProcessRetriever(model_id) 