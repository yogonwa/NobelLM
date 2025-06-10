"""
summarize_rag.py

Summarize the state of the NobelLM RAG pipeline: counts of laureates, speech files, chunks, embeddings, and FAISS index vectors.
Model-aware: works for any supported embedding model.

Usage:
    python -m utils.summarize_rag --model bge-large

Outputs a summary to stdout. Uses logging for errors.
"""
# Configure threading globally before any FAISS/PyTorch imports
from config.threading import configure_threading
configure_threading()

import json
import logging
import os
from pathlib import Path
import faiss
import argparse
from rag.model_config import get_model_config, DEFAULT_MODEL_ID

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

SPEECH_FOLDERS = [
    Path("data/nobel_lectures"),
    Path("data/acceptance_speeches"),
    Path("data/ceremony_speeches"),
]

def count_laureates(json_file: Path) -> int:
    if not json_file.exists():
        logging.error(f"nobel_literature.json not found at {json_file}")
        return 0
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return sum(len(prize["laureates"]) for prize in data)

def count_speech_files(folders) -> int:
    count = 0
    for folder in folders:
        if folder.exists():
            count += len(list(folder.glob("*.txt")))
        else:
            logging.warning(f"Speech folder not found: {folder}")
    return count

def count_chunks(chunks_file: Path) -> int:
    if not chunks_file.exists():
        logging.error(f"Chunks file not found at {chunks_file}")
        return 0
    count = 0
    with open(chunks_file, "r", encoding="utf-8") as f:
        for _ in f:
            count += 1
    return count

def count_embeddings(embeddings_file: Path):
    if not embeddings_file.exists():
        logging.error(f"Embeddings file not found at {embeddings_file}")
        return 0, None
    with open(embeddings_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    count = len(data)
    vector_dim = len(data[0]["embedding"]) if count > 0 and "embedding" in data[0] else None
    return count, vector_dim

def count_faiss_vectors(faiss_index_file: Path, expected_dim: int = None) -> int:
    if not faiss_index_file.exists():
        logging.error(f"FAISS index file not found at {faiss_index_file}")
        return 0
    index = faiss.read_index(str(faiss_index_file))
    if expected_dim is not None and hasattr(index, 'd') and index.d != expected_dim:
        raise ValueError(f"FAISS index dimension ({index.d}) does not match expected ({expected_dim})")
    return index.ntotal


def main():
    parser = argparse.ArgumentParser(description="Summarize NobelLM RAG pipeline data.")
    parser.add_argument('--model', default=DEFAULT_MODEL_ID, choices=list(get_model_config().keys()), help='Embedding model to summarize')
    args = parser.parse_args()
    config = get_model_config(args.model)

    BASE_PATH = Path("data")
    JSON_FILE = BASE_PATH / "nobel_literature.json"
    CHUNKS_FILE = BASE_PATH / f"chunks_literature_labeled_{args.model}.jsonl"
    EMBEDDINGS_FILE = BASE_PATH / f"literature_embeddings_{args.model}.json"
    FAISS_INDEX_FILE = Path(config["index_path"])
    expected_dim = config["embedding_dim"]

    laureate_count = count_laureates(JSON_FILE)
    speech_file_count = count_speech_files(SPEECH_FOLDERS)
    chunk_count = count_chunks(CHUNKS_FILE)
    embedding_count, vector_dim = count_embeddings(EMBEDDINGS_FILE)
    faiss_count = count_faiss_vectors(FAISS_INDEX_FILE, expected_dim=expected_dim)

    print(f"\n✅ NobelLM Data Summary (model: {args.model}):")
    print(f"- Laureates:            {laureate_count}")
    print(f"- Speech Text Files:    {speech_file_count}")
    print(f"- Text Chunks:          {chunk_count}")
    print(f"- Embeddings:           {embedding_count}")
    print(f"- Vector Dimension:     {vector_dim}")
    print(f"- FAISS Index Vectors:  {faiss_count}")

if __name__ == "__main__":
    main() 