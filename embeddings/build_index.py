"""
build_index.py

Builds and persists a FAISS cosine similarity index for Nobel Literature speech embeddings.
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"  # Prevents FAISS/PyTorch segfaults on macOS (threading issue)
import json
import logging
from typing import List, Dict, Any, Tuple, Optional, Sequence
import numpy as np
import faiss
import sys

logging.basicConfig(level=logging.INFO)


def load_embeddings(
    json_path: str,
    fields: Optional[Sequence[str]] = None
) -> List[Dict[str, Any]]:
    """
    Load embeddings or metadata from a JSON or JSONL file.
    Args:
        json_path: Path to the file
        fields: Optional tuple/list of fields to keep (None = all)
    Returns:
        List of dicts
    """
    data = []
    if json_path.endswith(".jsonl"):
        with open(json_path, "r", encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)
                if fields:
                    obj = {k: v for k, v in obj.items() if k in fields}
                data.append(obj)
    else:
        with open(json_path, "r", encoding="utf-8") as f:
            arr = json.load(f)
            for obj in arr:
                if fields:
                    obj = {k: v for k, v in obj.items() if k in fields}
                data.append(obj)
    return data


def build_index(
    embeddings_path: str = "data/literature_embeddings.json",
    index_dir: str = "data/faiss_index/"
) -> None:
    """
    Build a FAISS cosine similarity index from embedding vectors and save index + metadata mapping (as JSONL).
    """
    os.makedirs(index_dir, exist_ok=True)
    index_path = os.path.join(index_dir, "index.faiss")
    metadata_path = os.path.join(index_dir, "chunk_metadata.jsonl")

    logging.info(f"Loading embeddings from {embeddings_path}")
    with open(embeddings_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        logging.error("No embeddings found in the input file.")
        return

    embeddings = np.array([d["embedding"] for d in data], dtype=np.float32)
    dim = embeddings.shape[1]
    # Validate all embeddings have the same dimension
    if not all(len(vec) == dim for vec in embeddings):
        raise ValueError("Inconsistent embedding dimensions detected.")
    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    faiss.write_index(index, index_path)
    logging.info(f"FAISS index written to {index_path}")

    # Save metadata mapping (excluding the embedding field) as JSONL
    with open(metadata_path, "w", encoding="utf-8") as f:
        for d in data:
            meta = {k: v for k, v in d.items() if k != "embedding"}
            f.write(json.dumps(meta, ensure_ascii=False) + "\n")
    logging.info(f"Chunk metadata written to {metadata_path}")


def load_index(
    index_dir: str = "data/faiss_index/"
) -> Tuple[faiss.Index, List[Dict[str, Any]]]:
    """
    Load the FAISS index and metadata mapping from disk (JSONL).
    """
    index_path = os.path.join(index_dir, "index.faiss")
    metadata_path = os.path.join(index_dir, "chunk_metadata.jsonl")

    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        raise FileNotFoundError("FAISS index or metadata mapping not found. Run build_index() first.")

    index = faiss.read_index(index_path)
    metadata = load_embeddings(metadata_path)
    return index, metadata


def query_index(
    index: faiss.Index,
    metadata: List[Dict[str, Any]],
    query_embedding: np.ndarray,
    top_k: int = 3,
    min_score: float = 0.2
) -> List[Dict[str, Any]]:
    """
    Query the FAISS index and return top_k most similar chunks with metadata.
    Args:
        index: FAISS index object
        metadata: List of chunk metadata dicts
        query_embedding: 1D numpy array (should be normalized)
        top_k: Number of results to return
        min_score: Minimum score threshold for a match
    Returns:
        List of metadata dicts for top_k results, each with a 'score' and 'rank' field
    """
    if query_embedding.ndim == 1:
        query_embedding = query_embedding.reshape(1, -1)
    faiss.normalize_L2(query_embedding)
    scores, indices = index.search(query_embedding, top_k)
    results = []
    if scores.size == 0 or all(s < min_score for s in scores[0]):
        return [{"score": 0.0, "note": "No strong matches found"}]
    for i, (idx, score) in enumerate(zip(indices[0], scores[0])):
        if idx < 0 or idx >= len(metadata):
            continue
        result = metadata[idx].copy()
        result["score"] = float(score)
        result["rank"] = i
        results.append(result)
    return results


if __name__ == "__main__":
    def print_usage():
        print("Usage: python -m embeddings.build_index [build|test]")
        print("  build : Build the FAISS index and metadata (default)")
        print("  test  : Run interactive query test harness (requires sentence-transformers)")

    mode = sys.argv[1] if len(sys.argv) > 1 else "build"
    if mode == "build":
        build_index()
    elif mode == "test":
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            logging.error("sentence-transformers not installed. Please install it to use the CLI test harness.")
            sys.exit(1)
        try:
            index, metadata = load_index()
        except FileNotFoundError as e:
            logging.error(str(e))
            print("You must build the index first: python -m embeddings.build_index build")
            sys.exit(1)
        model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Type a query (or 'exit' to quit):")
        while True:
            query = input("Query: ").strip()
            if not query or query.lower() == "exit":
                break
            emb = model.encode(query, normalize_embeddings=True)
            results = query_index(index, metadata, np.array(emb), top_k=5)
            for r in results:
                if "note" in r:
                    print(r["note"])
                else:
                    print(f"{r.get('laureate', 'N/A')} ({r.get('year_awarded', 'N/A')}) [{r.get('source_type', 'N/A')}]: {r['score']:.2f} (rank {r['rank']})")
    else:
        print_usage()
        sys.exit(1) 