"""
Dependency injection for NobelLM FastAPI backend.

This module provides shared resources and dependencies that are
initialized once and reused across requests.
"""

import logging
import os
import json
import faiss
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from fastapi import Depends

from rag.query_engine import answer_query
from rag.model_config import get_model_config, DEFAULT_MODEL_ID
from rag.model_config import MODEL_CONFIGS
from sentence_transformers import SentenceTransformer
from .config import get_settings, Settings

logger = logging.getLogger(__name__)


class RAGDependencies:
    """Container for RAG pipeline dependencies."""
    
    def __init__(self):
        self._faiss_index = None
        self._metadata = None
        self._model = None
        self._model_id = DEFAULT_MODEL_ID
        self._initialized = False
    
    def initialize(self, model_id: str = None) -> None:
        """Initialize RAG dependencies."""
        if self._initialized:
            return
        
        model_id = model_id or DEFAULT_MODEL_ID
        self._model_id = model_id
        
        try:
            logger.info(f"Initializing RAG dependencies for model: {model_id}")
            
            # Check if Weaviate is enabled
            settings = get_settings()
            if settings.use_weaviate:
                logger.info("Weaviate is enabled - skipping FAISS index initialization")
                # Only load the embedding model for Weaviate
                self._model = self._load_model(model_id)
                self._faiss_index = None
                self._metadata = None
            else:
                logger.info("FAISS mode - loading index and metadata")
                # Load FAISS index and metadata directly (avoid Streamlit cache)
                self._faiss_index, self._metadata = self._load_faiss_index_and_metadata(model_id)
                # Load embedding model directly
                self._model = self._load_model(model_id)
            
            self._initialized = True
            logger.info(f"RAG dependencies initialized successfully for model: {model_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG dependencies: {e}")
            raise
    
    def _load_faiss_index_and_metadata(self, model_id: str) -> Tuple[object, List[Dict[str, Any]]]:
        """Load FAISS index and metadata directly."""
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

        return index, metadata
    
    def _load_model(self, model_id: str) -> SentenceTransformer:
        """Load sentence transformer model directly."""
        config = get_model_config(model_id)
        return SentenceTransformer(config["model_name"])
    
    @property
    def faiss_index(self):
        """Get FAISS index."""
        if not self._initialized:
            self.initialize()
        return self._faiss_index
    
    @property
    def metadata(self):
        """Get chunk metadata."""
        if not self._initialized:
            self.initialize()
        return self._metadata
    
    @property
    def model(self):
        """Get embedding model."""
        if not self._initialized:
            self.initialize()
        return self._model
    
    @property
    def model_id(self) -> str:
        """Get current model ID."""
        return self._model_id
    
    @property
    def is_weaviate_mode(self) -> bool:
        """Check if running in Weaviate mode."""
        if not self._initialized:
            self.initialize()
        return self._faiss_index is None and self._metadata is None
    
    @property
    def is_faiss_mode(self) -> bool:
        """Check if running in FAISS mode."""
        if not self._initialized:
            self.initialize()
        return self._faiss_index is not None and self._metadata is not None


# Global RAG dependencies instance
rag_deps = RAGDependencies()


def get_rag_dependencies() -> RAGDependencies:
    """Get RAG dependencies."""
    return rag_deps


def get_settings_dep() -> Settings:
    """Get application settings dependency."""
    return get_settings()


def validate_query(query: str, settings: Settings = Depends(get_settings_dep)) -> str:
    """Validate and clean query input."""
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    query = query.strip()
    if len(query) > settings.max_query_length:
        raise ValueError(f"Query too long. Maximum length: {settings.max_query_length}")
    
    return query 