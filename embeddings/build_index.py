"""
build_index.py

Builds and saves a FAISS cosine similarity index from Nobel Literature embeddings.
Supports model toggling and creates separate index directories per model.

Usage:
    python build_index.py --model bge-large
"""

import os
import json
import logging
import argparse
from typing import List, Dict, Tuple
import numpy as np
import faiss
from rag.model_config import get_model_config, DEFAULT_MODEL_ID, MODEL_CONFIGS

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def load_embeddings(path: str) -> List[Dict]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_faiss_index(model_id: str):
    config = get_model_config(model_id)
    embedding_file = f"data/literature_embeddings_{model_id}.json"
    index_path = config["index_path"]
    metadata_path = config["metadata_path"]
    index_dir = os.path.dirname(index_path)
    os.makedirs(index_dir, exist_ok=True)

    logging.info(f"Loading embeddings from {embedding_file}")
    data = load_embeddings(embedding_file)
    if not data:
        raise ValueError("No embeddings found.")

    embeddings = np.array([d["embedding"] for d in data], dtype=np.float32)
    dim = embeddings.shape[1]
    if dim != config["embedding_dim"]:
        raise ValueError(f"Embedding dimension ({dim}) does not match config ({config['embedding_dim']}) for model '{model_id}'")
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    faiss.write_index(index, index_path)
    logging.info(f"FAISS index saved to {index_path}")

    with open(metadata_path, 'w', encoding='utf-8') as f:
        for d in data:
            meta = {k: v for k, v in d.items() if k != "embedding"}
            f.write(json.dumps(meta, ensure_ascii=False) + "\n")
    logging.info(f"Metadata saved to {metadata_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default=DEFAULT_MODEL_ID, choices=list(MODEL_CONFIGS.keys()), help='Embedding model to use')
    args = parser.parse_args()
    build_faiss_index(args.model)


if __name__ == '__main__':
    main()
