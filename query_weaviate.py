# query_weaviate.py

import weaviate
import numpy as np
from sentence_transformers import SentenceTransformer

# Connect to Weaviate
client = weaviate.Client(
    url="https://a0dq8xtrtkw6lovkllxw.c0.us-east1.gcp.weaviate.cloud",
    auth_client_secret=weaviate.AuthApiKey("dFovQ01lNVRoUjdEOCtrRV9EQVlKd29GK1ZnWmNiclpFbmxSK2gxTjBrODBSMEZWVVQwMFBtSFhNYUVBPV92MjAw")  # Replace this
)

# Load embedding model
model = SentenceTransformer("BAAI/bge-large-en-v1.5")

def query_weaviate(
    query_text: str,
    top_k: int = 5,
    filters: dict = None,
    score_threshold: float = 0.2
):
    # Embed query
    embedding = model.encode(query_text, normalize_embeddings=True).tolist()

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
        for i, r in enumerate(results):
            r["rank"] = i
        return results
    except Exception as e:
        print("Weaviate query failed:", e)
        print("RAW RESPONSE FROM WEAVIATE:")
        print(result)
        return []