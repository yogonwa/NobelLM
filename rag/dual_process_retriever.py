"""
Dual-Process Retriever for NobelLM RAG

Implements subprocess-based FAISS retrieval for Mac/Intel compatibility.
This function is used when NOBELLM_USE_FAISS_SUBPROCESS=1 is set.
"""
import tempfile
import os
import subprocess
import json
import numpy as np
import logging
from sentence_transformers import SentenceTransformer
from rag.model_config import get_model_config

logging.basicConfig(level=logging.INFO)

def retrieve_chunks_dual_process(user_query: str, model_id: str = "bge-large", top_k: int = 5) -> list:
    config = get_model_config(model_id)
    model = SentenceTransformer(config["model_name"])
    embedding = model.encode(user_query, normalize_embeddings=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        emb_path = os.path.join(tmpdir, "query_embedding.npy")
        results_path = os.path.join(tmpdir, "retrieval_results.json")
        np.save(emb_path, embedding)
        logging.info(f"[DualProcess] Saved query embedding to {emb_path}")
        subprocess.run(
            ["python", "rag/faiss_query_worker.py", "--model", model_id, "--dir", tmpdir],
            check=True
        )
        with open(results_path, "r", encoding="utf-8") as f:
            results = json.load(f)
        logging.info(f"[DualProcess] Loaded retrieval results from {results_path}")
    return results 