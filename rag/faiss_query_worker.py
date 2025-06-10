# ---- Import global threading configuration ----
import sys
from pathlib import Path

# Add parent dir to sys.path to allow running as subprocess
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Configure threading globally (inherits from parent process)
from config.threading import configure_threading
configure_threading()

# ---- Now proceed with normal imports ----
"""
FAISS Worker for Subprocess-Based RAG Retrieval (Tempdir Version)

Loads a query embedding, runs FAISS search, and saves results.
Uses a temp directory for safe concurrent execution.
Supports metadata filtering via --filters argument (JSON file).
"""

import numpy as np
import json
import argparse
import logging
from rag.retriever import query_index
from typing import Dict, Any, List, Optional
from sentence_transformers import SentenceTransformer
from rag.model_config import get_model_config, DEFAULT_MODEL_ID
from rag.utils import filter_top_chunks

# Configure logging to use stderr for all diagnostic output
logging.basicConfig(level=logging.INFO, stream=sys.stderr)

logger = logging.getLogger(__name__)

def main(
    query: str,
    model_id: str = None,
    top_k: int = 5,
    filters: Dict[str, Any] = None,
    score_threshold: float = 0.2,
    min_return: int = 3,
    max_return: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Worker process for FAISS retrieval.
    Runs in a separate process to avoid PyTorch/FAISS conflicts on Mac/Intel.

    Args:
        query: The query string
        model_id: Optional model identifier
        top_k: Number of chunks to retrieve (default: 5)
        filters: Optional metadata filters
        score_threshold: Minimum similarity score (default: 0.2)
        min_return: Minimum number of chunks to return (default: 3)
        max_return: Optional maximum number of chunks to return

    Returns:
        List of chunks, filtered by score threshold
    """
    # Get model config
    model_id = model_id or DEFAULT_MODEL_ID
    config = get_model_config(model_id)
    if not config:
        raise ValueError(f"No config found for model_id: {model_id}")

    # Load model and check dimensions
    model = SentenceTransformer(config["model_name"])
    model_dim = model.get_sentence_embedding_dimension()
    logger.info(f"[Worker] Loaded model {model_id} with dimension {model_dim}")

    # Embed query
    query_embedding = model.encode([query], normalize_embeddings=True)[0]
    logger.info(f"[Worker] Query embedding shape: {query_embedding.shape}")

    # Query index
    chunks = query_index(
        query_embedding,
        model_id=model_id,
        top_k=top_k,
        filters=filters
    )
    logger.info(f"[Worker] Retrieved {len(chunks)} chunks before filtering")

    # Apply consistent filtering
    filtered_chunks = filter_top_chunks(
        chunks,
        score_threshold=score_threshold,
        min_return=min_return,
        max_return=max_return
    )
    logger.info(f"[Worker] Final filtered chunks: {len(filtered_chunks)}")

    # Output results as JSON to stdout (only this should go to stdout)
    print(json.dumps(filtered_chunks, ensure_ascii=False))
    return filtered_chunks

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FAISS query worker")
    parser.add_argument("--query", required=True, help="Query string")
    parser.add_argument("--model_id", help="Model identifier")
    parser.add_argument("--top_k", type=int, default=5, help="Number of chunks to retrieve")
    parser.add_argument("--filters", type=json.loads, help="JSON string of metadata filters")
    parser.add_argument("--score_threshold", type=float, default=0.2, help="Minimum similarity score")
    parser.add_argument("--min_return", type=int, default=3, help="Minimum number of chunks to return")
    parser.add_argument("--max_return", type=int, help="Maximum number of chunks to return")
    args = parser.parse_args()

    main(
        query=args.query,
        model_id=args.model_id,
        top_k=args.top_k,
        filters=args.filters,
        score_threshold=args.score_threshold,
        min_return=args.min_return,
        max_return=args.max_return
    )
