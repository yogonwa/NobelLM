"""
Main Driver for Subprocess-Based RAG Retrieval (Tempdir Version)

Embeds a user query, saves the embedding, launches a FAISS subprocess, and prints results.
Uses a temp directory for safe concurrent execution.
"""
import numpy as np
import json
import subprocess
import logging
import tempfile
import os
from sentence_transformers import SentenceTransformer
from rag.model_config import get_model_config

logging.basicConfig(level=logging.INFO)

user_query = "What do laureates say about the creative process?"
model_id = "bge-large"
config = get_model_config(model_id)

logging.info(f"Loading embedding model: {config['model_name']}")
model = SentenceTransformer(config["model_name"])
embedding = model.encode(user_query, normalize_embeddings=True)

with tempfile.TemporaryDirectory() as tmpdir:
    emb_path = os.path.join(tmpdir, "query_embedding.npy")
    results_path = os.path.join(tmpdir, "retrieval_results.json")
    np.save(emb_path, embedding)
    logging.info(f"Saved query embedding to {emb_path}")
    logging.info("Launching FAISS worker subprocess...")
    subprocess.run(["python", "rag/faiss_query_worker.py", "--model", model_id, "--dir", tmpdir], check=True)
    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)
    logging.info("Retrieved Chunks:")
    for r in results:
        logging.info(f"Score: {r.get('score', 0):.2f} — {r.get('laureate', 'Unknown')} ({r.get('year_awarded', '?')})")
        logging.info(f"  {r.get('text', '')[:200]}...") 