"""
Generate sentence embeddings for Nobel Literature speech chunks using MiniLM.

- Loads chunks from data/chunks_literature_labeled.jsonl
- Generates embeddings using all-MiniLM-L6-v2 (Hugging Face)
- Writes output to data/literature_embeddings.json

This script can be run as a CLI or imported as a module.
"""
import os
import json
import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Model choice explanation
# We use 'all-MiniLM-L6-v2' from Hugging Face for its balance of speed, size, and semantic accuracy.
# See: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
MODEL_NAME = 'all-MiniLM-L6-v2'
CHUNKS_PATH = os.path.join('data', 'chunks_literature_labeled.jsonl')
EMBEDDINGS_PATH = os.path.join('data', 'literature_embeddings.json')


def generate_embedding(text: str, model: SentenceTransformer) -> List[float]:
    """
    Generate a sentence embedding for the given text using MiniLM.
    Args:
        text (str): The input text to embed.
        model (SentenceTransformer): The loaded sentence transformer model.
    Returns:
        List[float]: The embedding vector as a list of floats.
    """
    return model.encode(text, show_progress_bar=False).tolist()


def load_chunks(path: str) -> List[Dict[str, Any]]:
    """
    Load chunked speech data from a JSONL file.
    Args:
        path (str): Path to the JSONL file.
    Returns:
        List[Dict[str, Any]]: List of chunk dicts.
    """
    chunks = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks


def main():
    logging.info(f"Loading chunks from {CHUNKS_PATH}")
    chunks = load_chunks(CHUNKS_PATH)
    logging.info(f"Loaded {len(chunks)} chunks. Initializing model...")
    model = SentenceTransformer(MODEL_NAME)
    logging.info(f"Model '{MODEL_NAME}' loaded. Generating embeddings...")

    output = []
    for chunk in tqdm(chunks, desc="Embedding chunks"):
        try:
            embedding = generate_embedding(chunk['text'], model)
            chunk_out = dict(chunk)
            chunk_out['embedding'] = embedding
            output.append(chunk_out)
        except Exception as e:
            logging.error(f"Failed to embed chunk {chunk.get('chunk_id', '[no id]')}: {e}")

    logging.info(f"Writing {len(output)} embeddings to {EMBEDDINGS_PATH}")
    with open(EMBEDDINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    logging.info("Done.")


if __name__ == '__main__':
    main() 