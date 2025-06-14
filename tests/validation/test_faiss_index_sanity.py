"""
FAISS Index Sanity Check Script

This script tests loading the NobelLM FAISS index and running a search with a random vector.
Use this to debug segmentation faults or index compatibility issues in isolation from the main pipeline.
"""
# Configure threading globally before any FAISS/PyTorch imports
from config.threading import configure_threading
configure_threading()

import logging
import faiss
import numpy as np
import sys

logging.basicConfig(level=logging.INFO)

INDEX_PATH = "data/faiss_index_bge-large/index.faiss"  # Adjust if needed

try:
    logging.info(f"Loading FAISS index from {INDEX_PATH} ...")
    index = faiss.read_index(INDEX_PATH)
    d = index.d
    logging.info(f"Index loaded. Dimension: {d}")
    vec = np.random.rand(1, d).astype('float32')
    faiss.normalize_L2(vec)
    logging.info(f"Random vector normalized. Running search ...")
    D, I = index.search(vec, 3)
    logging.info(f"Search results: D={D}, I={I}")
    logging.info("FAISS index sanity check completed successfully.")
except Exception as e:
    logging.error(f"Error during FAISS index sanity check: {e}")
    sys.exit(1) 