"""
audit_data.py

Audit the NobelLM data pipeline for consistency and completeness.
"""
# Configure threading globally before any FAISS/PyTorch imports
from config.threading import configure_threading
configure_threading()

import logging
import json
import faiss
from pathlib import Path
from typing import Optional, List, Dict, Any
from rag.model_config import get_model_config, DEFAULT_MODEL_ID

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def load_json_or_jsonl(path: str) -> List[Dict[str, Any]]:
    """Load data from a .json or .jsonl file."""
    try:
        if path.endswith(".jsonl"):
            with open(path, "r", encoding="utf-8") as f:
                return [json.loads(line) for line in f]
        elif path.endswith(".json"):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {path}")
    except Exception as e:
        logging.error(f"Failed to load {path}: {e}")
        return []

def audit_chunks(chunk_path: str) -> int:
    chunks = load_json_or_jsonl(chunk_path)
    logging.info(f"\n🔍 Auditing chunks from {chunk_path}")
    logging.info(f"Total chunks: {len(chunks)}")
    if not chunks:
        return 0
    # Try both 'text_snippet' and 'text' for compatibility
    long_chunks = [c for c in chunks if len(c.get("text_snippet", c.get("text", "")).split()) > 512]
    short_chunks = [c for c in chunks if len(c.get("text_snippet", c.get("text", "")).split()) < 10]
    source_distribution = {}
    for c in chunks:
        source_type = c.get("source_type", "unknown")
        source_distribution[source_type] = source_distribution.get(source_type, 0) + 1
    logging.info(f"Chunks > 512 words: {len(long_chunks)}")
    logging.info(f"Chunks < 10 words: {len(short_chunks)}")
    logging.info(f"Source type distribution: {source_distribution}")
    return len(chunks)

def audit_embeddings(embedding_path: str, expected_dim: int) -> int:
    data = load_json_or_jsonl(embedding_path)
    logging.info(f"\n🔍 Auditing embeddings from {embedding_path}")
    logging.info(f"Total embeddings: {len(data)}")
    malformed = [
        e for e in data if not isinstance(e.get("embedding"), list)
        or len(e["embedding"]) != expected_dim
        or not all(isinstance(x, (float, int)) for x in e["embedding"])
    ]
    logging.info(f"Invalid or malformed vectors: {len(malformed)}")
    return len(data)

def audit_faiss_index(index_path: str, expected_dim: int, expected_count: Optional[int]) -> None:
    logging.info(f"\n🔍 Auditing FAISS index at {index_path}")
    try:
        index = faiss.read_index(index_path)
        logging.info(f"Index contains {index.ntotal} vectors" + (f" (expected: {expected_count})" if expected_count is not None else ""))
        logging.info(f"Index dimension: {index.d} (expected: {expected_dim})")
        if expected_count is not None and index.ntotal != expected_count:
            logging.warning("❗ Mismatch between index and embeddings!")
        if index.d != expected_dim:
            logging.warning("❗ Index dimension does not match expected embedding dimension!")
    except Exception as e:
        logging.error(f"Failed to load FAISS index: {e}")

def run_full_audit(model_id: str = "bge-large") -> None:
    cfg = get_model_config(model_id)
    chunk_count = audit_chunks(cfg["metadata_path"])
    # Dynamically select embedding path
    if "bge" in cfg["index_path"]:
        embed_path = "data/literature_embeddings_bge-large.json"
    else:
        embed_path = "data/literature_embeddings_minilm.json"
    embed_count = audit_embeddings(embed_path, cfg["embedding_dim"])
    expected_count = chunk_count if chunk_count > 0 else None
    audit_faiss_index(cfg["index_path"], expected_dim=cfg["embedding_dim"], expected_count=expected_count)

if __name__ == "__main__":
    run_full_audit() 