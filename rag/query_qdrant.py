"""
Qdrant query interface for NobelLM RAG pipeline.

- Provides low-level functions to connect to and query a Qdrant vector database.
- Handles client instantiation, query embedding (using Modal service), and result normalization.
- Used by QdrantRetriever in rag/retriever_qdrant.py for backend-agnostic retrieval.
- Configuration is via environment variables or backend config.

Related files:
- rag/retriever_qdrant.py: Implements the QdrantRetriever using this interface.
- rag/retriever.py: Retriever factory and interface.

Configuration:
- Set QDRANT_URL and QDRANT_API_KEY as environment variables or via backend config.
- Embedding is performed via Modal service (not locally).
"""
import os
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from dotenv import load_dotenv

# Import unified embedding service
from rag.modal_embedding_service import embed_query

logging.basicConfig(level=logging.INFO)

COLLECTION_NAME = "nobellm_bge_large"

load_dotenv()

def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client with environment-based configuration."""
    try:
        from backend.app.config import get_settings
        settings = get_settings()
        url = settings.qdrant_url
        api_key = settings.qdrant_api_key
    except ImportError:
        url = os.getenv("QDRANT_URL")
        api_key = os.getenv("QDRANT_API_KEY")
    if not url or not api_key:
        raise ValueError("QDRANT_URL and QDRANT_API_KEY must be set in the environment or backend config.")
    return QdrantClient(url=url, api_key=api_key)

def query_qdrant(
    query_text: str,
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None,
    score_threshold: float = 0.2
) -> List[Dict[str, Any]]:
    """
    Embed the query and search Qdrant for similar vectors.
    """
    embedding = embed_query(query_text).tolist()
    return query_qdrant_with_embedding(embedding, top_k, filters, score_threshold)

def query_qdrant_with_embedding(
    embedding: list,
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None,
    score_threshold: float = 0.2
) -> List[Dict[str, Any]]:
    """
    Query Qdrant using a pre-computed embedding.
    Args:
        embedding: Pre-computed embedding as a list of floats
        top_k: Number of results to return
        filters: Optional metadata filters
        score_threshold: Minimum similarity score
    Returns:
        List of normalized chunk results
    """
    client = get_qdrant_client()
    qdrant_filter = None
    if filters:
        conditions = [FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filters.items()]
        qdrant_filter = Filter(must=conditions)
    try:
        search_result = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=embedding,
            limit=top_k,
            score_threshold=score_threshold,
            query_filter=qdrant_filter,
            with_payload=True
        )
        normalized_results = []
        for i, r in enumerate(search_result):
            payload = r.payload or {}
            normalized_result = {
                "chunk_id": payload.get("chunk_id"),
                "text": payload.get("text"),
                "laureate": payload.get("laureate"),
                "year_awarded": payload.get("year_awarded"),
                "gender": payload.get("gender"),
                "category": payload.get("category"),
                "country": payload.get("country"),
                "rank": i,
                "score": float(r.score) if hasattr(r, 'score') else 0.0
            }
            normalized_results.append(normalized_result)
        return normalized_results
    except Exception as e:
        logging.error(f"Qdrant query failed: {e}")
        return []