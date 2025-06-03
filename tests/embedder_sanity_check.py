"""
Embedding Model Sanity Check Script

This script tests loading the NobelLM embedding model and generating an embedding for a simple string.
Use this to debug segmentation faults or model compatibility issues in isolation from the main pipeline.
"""
import logging
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)

MODEL_NAME = "BAAI/bge-large-en-v1.5"  # Change to 'sentence-transformers/all-MiniLM-L6-v2' if needed

try:
    logging.info(f"Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    logging.info("Model loaded.")
    emb = model.encode("Test embedding", show_progress_bar=False, normalize_embeddings=True)
    logging.info(f"Embedding shape: {emb.shape}, first 5 values: {emb[:5]}")
    logging.info("Embedding model sanity check completed successfully.")
except Exception as e:
    logging.error(f"Error during embedding: {e}") 