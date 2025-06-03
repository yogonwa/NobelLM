"""
FAISS Worker for Subprocess-Based RAG Retrieval (Tempdir Version)

Loads a query embedding, runs FAISS search, and saves results.
Uses a temp directory for safe concurrent execution.
"""
import numpy as np
import json
import argparse
import logging
import os
from rag.retriever import query_index

logging.basicConfig(level=logging.INFO)

def main(model_id: str, tmpdir: str):
    emb_path = os.path.join(tmpdir, "query_embedding.npy")
    results_path = os.path.join(tmpdir, "retrieval_results.json")
    query_vector = np.load(emb_path)
    logging.info(f"Loaded query embedding from {emb_path}, shape: {query_vector.shape}")
    results = query_index(query_vector, model_id=model_id, top_k=5)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logging.info(f"Saved retrieval results to {results_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="bge-large")
    parser.add_argument("--dir", default=".")
    args = parser.parse_args()
    main(args.model, args.dir) 