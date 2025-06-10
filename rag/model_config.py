"""
model_config.py

Centralized configuration for embedding models, FAISS index, and chunk metadata paths for the NobelLM RAG pipeline.

This module provides a single source of truth for all model-specific configuration:
- Model names and embedding dimensions
- FAISS index and metadata file paths
- Standard defaults (e.g., top_k=5 for retrieval)

Key Features:
- Model-aware: Each model (e.g., BGE-Large, MiniLM) has its own config
- Environment-aware: Supports both in-process and subprocess retrieval
- Standardized defaults: Defines consistent behavior across all models
- Extensible: Easy to add new models by updating MODEL_CONFIGS

Usage:
    from rag.model_config import get_model_config
    
    # Get config for default model (BGE-Large)
    config = get_model_config()
    
    # Get config for specific model
    config = get_model_config("miniLM")
    
    # Use in retrieval
    index_path = config["index_path"]
    model_name = config["model_name"]
    embedding_dim = config["embedding_dim"]

Author: NobelLM Team
"""
from typing import Dict
import os

# Supported models and their configs
MODEL_CONFIGS: Dict[str, Dict] = {
    "bge-large": {
        "model_name": "BAAI/bge-large-en-v1.5",
        "embedding_dim": 1024,
        "index_path": os.path.join("data", "faiss_index_bge-large", "index.faiss"),
        "metadata_path": os.path.join("data", "faiss_index_bge-large", "chunk_metadata.jsonl"),
    },
    "miniLM": {
        "model_name": "sentence-transformers/all-MiniLM-L6-v2",
        "embedding_dim": 384,
        "index_path": os.path.join("data", "faiss_index", "index.faiss"),
        "metadata_path": os.path.join("data", "faiss_index", "chunk_metadata.jsonl"),
    },
}

# Set the default model here
DEFAULT_MODEL_ID = "bge-large"


def get_model_config(model_id: str = None) -> Dict:
    """
    Return the config dict for the given model_id. If not provided, use the default.
    Raises KeyError if the model_id is not supported.
    """
    if model_id is None:
        model_id = DEFAULT_MODEL_ID
    if model_id not in MODEL_CONFIGS:
        raise KeyError(f"Model '{model_id}' is not supported. Available: {list(MODEL_CONFIGS.keys())}")
    return MODEL_CONFIGS[model_id] 