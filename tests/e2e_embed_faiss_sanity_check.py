"""
End-to-End Embedding + FAISS Sanity Check Script

This script tests the full pipeline: embedding a string and searching the NobelLM FAISS index.
Use this to debug integration issues or segmentation faults in isolation from the test harness.
"""
# Configure threading globally before any FAISS/PyTorch imports
from config.threading import configure_threading
configure_threading()

import logging
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import sys

logging.basicConfig(level=logging.INFO)

MODEL_NAME = "BAAI/bge-large-en-v1.5"
INDEX_PATH = "data/faiss_index_bge-large/index.faiss"

try:
    logging.info(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    logging.info("Model loaded.")
    text = "Test embedding for NobelLM end-to-end check."
    emb = model.encode(text, show_progress_bar=False, normalize_embeddings=True)
    logging.info(f"Embedding shape: {emb.shape}, first 5 values: {emb[:5]}")
    if emb.ndim == 1:
        emb = emb.reshape(1, -1)
    logging.info(f"Loading FAISS index from {INDEX_PATH} ...")
    index = faiss.read_index(INDEX_PATH)
    d = index.d
    if emb.shape[1] != d:
        raise ValueError(f"Embedding dim {emb.shape[1]} does not match index dim {d}")
    faiss.normalize_L2(emb)
    logging.info("Running search ...")
    D, I = index.search(emb, 3)
    logging.info(f"Search results: D={D}, I={I}")
    logging.info("End-to-end embedding + FAISS sanity check completed successfully.")
except Exception as e:
    logging.error(f"Error during end-to-end check: {e}")
    sys.exit(1) 