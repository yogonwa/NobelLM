"""
embed_texts.py

Generate sentence embeddings for Nobel Literature chunks.
Supports both MiniLM and BGE-Large models via toggle.

Inputs:
- data/chunks_literature_labeled_{model}.jsonl

Outputs:
- data/literature_embeddings_{model}.json

Usage:
    python embed_texts.py --model bge-large
"""

import os
import json
import logging
import argparse
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from rag.model_config import get_model_config, DEFAULT_MODEL_ID

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def load_chunks(path: str) -> List[Dict[str, Any]]:
    with open(path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]


def generate_embedding(text: str, model: SentenceTransformer) -> List[float]:
    return model.encode(text, show_progress_bar=False).tolist()


def embed_chunks(model_id: str):
    config = get_model_config(model_id)
    chunk_file = f"data/chunks_literature_labeled_{model_id}.jsonl"
    output_file = f"data/literature_embeddings_{model_id}.json"
    logging.info(f"Loading chunks from {chunk_file}")
    chunks = load_chunks(chunk_file)
    logging.info(f"Loaded {len(chunks)} chunks. Initializing model '{config['model_name']}'...")

    model = SentenceTransformer(config['model_name'])
    output = []

    for chunk in tqdm(chunks, desc=f"Embedding with {config['model_name']}"):
        try:
            embedding = generate_embedding(chunk['text'], model)
            chunk_out = dict(chunk)
            chunk_out['embedding'] = embedding
            output.append(chunk_out)
        except Exception as e:
            logging.error(f"Failed to embed chunk {chunk.get('chunk_id', '[no id]')}: {e}")

    logging.info(f"Writing {len(output)} embeddings to {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    logging.info("Embedding complete.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default=DEFAULT_MODEL_ID, choices=list(get_model_config().keys()), help='Embedding model to use')
    args = parser.parse_args()
    embed_chunks(args.model)
