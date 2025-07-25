"""
Dependency injection for NobelLM FastAPI backend.

This module provides shared resources and dependencies that are
initialized once and reused across requests.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import Depends

from rag.query_engine import answer_query
from rag.model_config import DEFAULT_MODEL_ID
from .config import get_settings, Settings

logger = logging.getLogger(__name__)


class RAGDependencies:
    """Container for RAG pipeline dependencies (Qdrant-only)."""
    
    def __init__(self):
        self._model_id = DEFAULT_MODEL_ID
        self._initialized = False
    
    def initialize(self, model_id: str = None) -> None:
        """Initialize RAG dependencies (Qdrant-only)."""
        if self._initialized:
            return
        self._model_id = model_id or DEFAULT_MODEL_ID
        self._initialized = True
        logger.info(f"RAG dependencies initialized for model: {self._model_id}")
    
    @property
    def model_id(self) -> str:
        """Get current model ID."""
        return self._model_id


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