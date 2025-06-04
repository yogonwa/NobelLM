"""
faiss_index.py

FAISS index loader, cache, and health check utilities for the NobelLM RAG pipeline.

- Loads and caches FAISS index for fast retrieval.
- Supports force reload, cache clearing, and health checks.
- Used by retriever and query engine modules.
"""
import os
import faiss
import logging
from rag.model_config import get_model_config, DEFAULT_MODEL_ID

_INDEX_CACHE = {}

logger = logging.getLogger(__name__)


def is_subprocess_mode():
    """
    Return True if FAISS retrieval should run in subprocess mode (for Mac/Intel safety).
    """
    return os.getenv("NOBELLM_USE_FAISS_SUBPROCESS") == "1"


def load_index(force_reload=False, model_id=None):
    """
    Load and cache the FAISS index for the specified model_id.
    If force_reload is True, reload from disk even if cached.
    Uses model config for index path.
    """
    model_id = model_id or DEFAULT_MODEL_ID
    config = get_model_config(model_id)
    index_path = config["index_path"]
    if force_reload or is_subprocess_mode() or model_id not in _INDEX_CACHE:
        logger.info(f"Loading FAISS index from {index_path} (force_reload={force_reload}, subprocess_mode={is_subprocess_mode()})")
        _INDEX_CACHE[model_id] = faiss.read_index(index_path)
        logger.info(f"[RAG][ShapeCheck] Index loaded with {_INDEX_CACHE[model_id].ntotal} vectors.")
    return _INDEX_CACHE[model_id]


def reload_index(model_id=None):
    """
    Force reload the FAISS index from disk for the given model_id.
    """
    logger.info(f"Forcing FAISS index reload for model_id={model_id or DEFAULT_MODEL_ID}")
    return load_index(force_reload=True, model_id=model_id)


def clear_index(model_id=None):
    """
    Clear the cached FAISS index for the given model_id, or all if None.
    """
    if model_id:
        _INDEX_CACHE.pop(model_id, None)
        logger.info(f"Cleared FAISS index cache for model_id={model_id}")
    else:
        _INDEX_CACHE.clear()
        logger.info("Cleared FAISS index cache for all models.")


def health_check(model_id=None):
    """
    Check index and metadata integrity for the given model_id. Logs stats and errors.
    """
    model_id = model_id or DEFAULT_MODEL_ID
    config = get_model_config(model_id)
    index_path = config["index_path"]
    metadata_path = config["metadata_path"]
    try:
        index = load_index(model_id=model_id)
        import json
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = [json.loads(line) for line in f]
        logger.info(f"Health check for model_id={model_id}:")
        logger.info(f"  Index path: {index_path}")
        logger.info(f"  Metadata path: {metadata_path}")
        logger.info(f"  Index vectors: {getattr(index, 'ntotal', 'N/A')}")
        logger.info(f"  Metadata records: {len(metadata)}")
        if hasattr(index, 'd'):
            logger.info(f"  Index dimension: {index.d}")
        logger.info(f"  Model config dimension: {config['embedding_dim']}")
        if hasattr(index, 'd') and index.d != config['embedding_dim']:
            logger.error(f"  Dimension mismatch: index.d={index.d} vs config={config['embedding_dim']}")
        if getattr(index, 'ntotal', 0) != len(metadata):
            logger.error(f"  Vector count mismatch: index.ntotal={index.ntotal} vs metadata={len(metadata)}")
        logger.info("  Health check complete.")
    except Exception as e:
        logger.error(f"Health check failed: {e}") 