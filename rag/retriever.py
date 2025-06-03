"""
retriever.py

Model-aware query_index function for the NobelLM RAG pipeline.
Loads the appropriate FAISS index and metadata based on the model config.
Used at runtime to retrieve top-k relevant chunks for a given query embedding.
"""

import os
import json
import logging
from typing import List, Dict, Tuple, Any
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
    min_score: float = 0.2
) -> List[Dict[str, Any]]:
    """
    Query the FAISS index for a given model using a normalized query embedding.
    Returns top-k results with metadata and similarity scores.
    """
    index, metadata = load_index_and_metadata(model_id)
    logger = logging.getLogger(__name__)
    logger.info(f"FAISS index is trained: {getattr(index, 'is_trained', 'N/A')}, total vectors: {getattr(index, 'ntotal', 'N/A')}")
    if query_embedding.ndim == 1:
        query_embedding = query_embedding.reshape(1, -1)
    logger.info(f"Query embedding shape: {query_embedding.shape}, dtype: {query_embedding.dtype}")
    logger.info(f"First few values: {query_embedding[0][:5]}")
    # Check for invalid vectors before normalization
    if is_invalid_vector(query_embedding):
        logger.error(f"Invalid query embedding detected: {query_embedding}")
        raise ValueError("Invalid query embedding: contains NaN, inf, or is all zeros.")
    else:
        logger.info("Query embedding passed validation.")
    faiss.normalize_L2(query_embedding)
    scores, indices = index.search(query_embedding, top_k)
    results = []
    if scores.size == 0 or all(s < min_score for s in scores[0]):
        return [{"score": 0.0, "note": "No strong matches found."}]
    for i, (idx, score) in enumerate(zip(indices[0], scores[0])):
        if idx < 0 or idx >= len(metadata):
            continue
        result = metadata[idx].copy()
        result["score"] = float(score)
        result["rank"] = i
        results.append(result)
    return results 