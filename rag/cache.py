import os
import json
import faiss
import logging
from typing import Tuple, List, Dict, Any
from sentence_transformers import SentenceTransformer
from rag.metadata_utils import load_laureate_metadata
from rag.model_config import get_model_config, DEFAULT_MODEL_ID

logger = logging.getLogger(__name__)

class ModelCache:
    """Simple in-memory cache for models and data."""
    _instance = None
    _cache = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.info("Initialized ModelCache singleton")
        return cls._instance
    
    def get_or_load(self, key: str, loader_func, *args, **kwargs):
        """Get cached value or load it using the provided function."""
        if key not in self._cache:
            logger.info(f"Loading {key} into cache")
            self._cache[key] = loader_func(*args, **kwargs)
            logger.info(f"Successfully loaded {key}")
        else:
            logger.debug(f"Using cached {key}")
        return self._cache[key]
    
    def clear(self):
        """Clear all cached items."""
        self._cache.clear()
        logger.info("Cache cleared")

# Global cache instance
_cache = ModelCache()

def get_faiss_index_and_metadata(model_id: str = None) -> Tuple[object, List[Dict[str, Any]]]:
    """
    Load and cache the FAISS index and chunk metadata for fast retrieval for the specified model.
    
    Returns:
        (index, chunk_metadata): Tuple of FAISS index object and list of chunk metadata dicts.
    """
    model_id = model_id or DEFAULT_MODEL_ID
    cache_key = f"faiss_metadata_{model_id}"
    
    def loader():
        config = get_model_config(model_id)
        index_path = config["index_path"]
        metadata_path = config["metadata_path"]

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Index file not found: {index_path}")
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

        logger.info(f"Loading FAISS index from {index_path}")
        index = faiss.read_index(index_path)
        
        logger.info(f"Loading metadata from {metadata_path}")
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = [json.loads(line) for line in f]

        logger.info(f"Loaded {len(metadata)} metadata entries")
        return index, metadata
    
    return _cache.get_or_load(cache_key, loader)

def get_flattened_metadata() -> List[Dict[str, Any]]:
    """
    Load and cache the flattened laureate metadata from the canonical JSON file.
    
    Returns:
        List of laureate metadata dicts.
    """
    return _cache.get_or_load("flattened_metadata", load_laureate_metadata, "config/nobel_literature.json")

def get_model(model_id: str = None) -> SentenceTransformer:
    """
    Load and cache the sentence-transformers model for embedding queries for the specified model.
    
    Returns:
        SentenceTransformer model instance.
    """
    model_id = model_id or DEFAULT_MODEL_ID
    cache_key = f"model_{model_id}"
    
    def loader():
        config = get_model_config(model_id)
        logger.info(f"Loading model: {config['model_name']}")
        return SentenceTransformer(config["model_name"])
    
    return _cache.get_or_load(cache_key, loader)

def clear_cache():
    """Clear all cached items. Useful for testing or memory management."""
    _cache.clear() 