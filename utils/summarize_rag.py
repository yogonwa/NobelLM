"""
summarize_rag.py

Summarize the state of the NobelLM RAG pipeline: counts of laureates, speech files, chunks, embeddings, and FAISS index vectors.

Usage:
    python -m utils.summarize_rag

Outputs a summary to stdout. Uses logging for errors.
"""
import json
import logging
import os
from pathlib import Path
import faiss
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Paths
BASE_PATH = Path("data")
JSON_FILE = BASE_PATH / "nobel_literature.json"
CHUNKS_FILE = BASE_PATH / "chunks_literature_labeled.jsonl"
EMBEDDINGS_FILE = BASE_PATH / "literature_embeddings.json"
FAISS_INDEX_FILE = BASE_PATH / "faiss_index" / "index.faiss"
SPEECH_FOLDERS = [
    BASE_PATH / "nobel_lectures",
    BASE_PATH / "acceptance_speeches",
    BASE_PATH / "ceremony_speeches",
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


def count_faiss_vectors(faiss_index_file: Path) -> int:
    if not faiss_index_file.exists():
        logging.error(f"FAISS index file not found at {faiss_index_file}")
        return 0
    index = faiss.read_index(str(faiss_index_file))
    return index.ntotal


def main():
    parser = argparse.ArgumentParser(description="Summarize NobelLM RAG pipeline data.")
    args = parser.parse_args()

    laureate_count = count_laureates(JSON_FILE)
    speech_file_count = count_speech_files(SPEECH_FOLDERS)
    chunk_count = count_chunks(CHUNKS_FILE)
    embedding_count, vector_dim = count_embeddings(EMBEDDINGS_FILE)
    faiss_count = count_faiss_vectors(FAISS_INDEX_FILE)

    print("\n✅ NobelLM Data Summary:")
    print(f"- Laureates:            {laureate_count}")
    print(f"- Speech Text Files:    {speech_file_count}")
    print(f"- Text Chunks:          {chunk_count}")
    print(f"- Embeddings:           {embedding_count}")
    print(f"- Vector Dimension:     {vector_dim}")
    print(f"- FAISS Index Vectors:  {faiss_count}")

if __name__ == "__main__":
    main() 