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
import os
from rag.retriever import query_index

logging.basicConfig(level=logging.INFO)

def main(model_id: str, tmpdir: str, filters_path: str = None, index_path: str = None, metadata_path: str = None):
    emb_path = os.path.join(tmpdir, "query_embedding.npy")
    results_path = os.path.join(tmpdir, "retrieval_results.json")
    query_vector = np.load(emb_path)
    logging.info(f"Loaded query embedding from {emb_path}, shape: {query_vector.shape}")
    filters = None
    if filters_path and os.path.exists(filters_path):
        with open(filters_path, "r", encoding="utf-8") as f:
            filters = json.load(f)
        logging.info(f"Loaded filters from {filters_path}: {filters}")
    results = query_index(query_vector, model_id=model_id, top_k=5, filters=filters, index_path=index_path, metadata_path=metadata_path)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logging.info(f"Saved retrieval results to {results_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="bge-large")
    parser.add_argument("--dir", default=".")
    parser.add_argument("--filters", default=None, help="Path to filters JSON file (optional)")
    parser.add_argument("--index_path", default=None, help="Override index path (optional)")
    parser.add_argument("--metadata_path", default=None, help="Override metadata path (optional)")
    args = parser.parse_args()
    main(args.model, args.dir, args.filters, args.index_path, args.metadata_path) 