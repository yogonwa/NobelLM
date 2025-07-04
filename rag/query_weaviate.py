# query_weaviate.py

import weaviate
import numpy as np
import os
from sentence_transformers import SentenceTransformer

def get_weaviate_client():
    """Get Weaviate client with environment-based configuration."""
    try:
        from backend.app.config import settings
        url = settings.weaviate_url
        api_key = settings.weaviate_api_key
    except ImportError:
        # Fallback to environment variables if config not available
        url = os.getenv("WEAVIATE_URL", "https://a0dq8xtrtkw6lovkllxw.c0.us-east1.gcp.weaviate.cloud")
        api_key = os.getenv("WEAVIATE_API_KEY", "")
    
    if not api_key:
        raise ValueError("WEAVIATE_API_KEY environment variable is required")
    
    client = weaviate.Client(
        url=url,
        auth_client_secret=weaviate.AuthApiKey(api_key) if api_key else None,
        additional_headers={"X-OpenAI-Api-Key": settings.openai_api_key} if settings.openai_api_key else None
    )
    return client

# Initialize client
client = get_weaviate_client()

# Import unified embedding service
from rag.modal_embedding_service import embed_query

def query_weaviate(
    query_text: str,
    top_k: int = 5,
    filters: dict = None,
    score_threshold: float = 0.2
):
    # Embed query using unified service
    embedding = embed_query(query_text).tolist()

    # Build filter if provided
    weaviate_filter = None
    if filters:
        weaviate_filter = {
            "operator": "And",
            "operands": [
                {
                    "path": [k],
                    "operator": "Equal",
                    "valueText": v
                }
                for k, v in filters.items()
            ]
        }

    # Construct query
    query = client.query.get("SpeechChunk", [
        "chunk_id", "text", "laureate", "year_awarded", "gender", "category", "country"
    ]).with_near_vector({
        "vector": embedding,
        "certainty": score_threshold
    }).with_additional(["score"]).with_limit(top_k)

    if weaviate_filter:
        query = query.with_where(weaviate_filter)

    result = query.do()

    try:
        results = result["data"]["Get"]["SpeechChunk"]
        normalized_results = []
        for i, r in enumerate(results):
            # Normalize the result to match expected format
            score_val = r.get("_additional", {}).get("score", 0)
            try:
                score = float(score_val)
            except Exception:
                score = 0.0
            normalized_result = {
                "chunk_id": r.get("chunk_id"),
                "text": r.get("text"),
                "laureate": r.get("laureate"),
                "year_awarded": r.get("year_awarded"),
                "gender": r.get("gender"),
                "category": r.get("category"),
                "country": r.get("country"),
                "rank": i,
                "score": score  # Always a float
            }
            normalized_results.append(normalized_result)
        return normalized_results
    except Exception as e:
        print("Weaviate query failed:", e)
        print("RAW RESPONSE FROM WEAVIATE:")
        print(result)
        return []