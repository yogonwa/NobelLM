"""
audit_chunk_sizes.py

Audits the token and word sizes of the chunks produced by
chunk_literature_speeches.py. Works with any supported embedding model.

Usage:
    python audit_chunk_sizes.py --model bge-large

Outputs:
- Token count stats
- Word count stats
- Distribution of oversized chunks
"""

import json
import argparse
from transformers import AutoTokenizer
from rag.model_config import get_model_config, DEFAULT_MODEL_ID, MODEL_CONFIGS


def audit_chunks(path: str, tokenizer) -> None:
    token_sizes = []
    word_sizes = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            chunk = json.loads(line)
            text = chunk["text"]
            tokens = tokenizer.encode(text, add_special_tokens=False)
            token_sizes.append(len(tokens))
            word_sizes.append(len(text.split()))

    print(f"Total chunks: {len(token_sizes)}")
    print(f"Min tokens: {min(token_sizes)}")
    print(f"Max tokens: {max(token_sizes)}")
    print(f"Average tokens: {sum(token_sizes)/len(token_sizes):.2f}")
    print(f"Chunks > 256 tokens: {sum(1 for s in token_sizes if s > 256)}")
    print(f"Chunks > 384 tokens: {sum(1 for s in token_sizes if s > 384)}")
    print(f"Chunks > 512 tokens: {sum(1 for s in token_sizes if s > 512)}")
    print("---")
    print(f"Min words: {min(word_sizes)}")
    print(f"Max words: {max(word_sizes)}")
    print(f"Average words: {sum(word_sizes)/len(word_sizes):.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL_ID, choices=list(MODEL_CONFIGS.keys()), help="Embedding model used for chunking")
    args = parser.parse_args()

    config = get_model_config(args.model)
    tokenizer = AutoTokenizer.from_pretrained(config["model_name"])
    chunk_path = f"data/chunks_literature_labeled_{args.model}.jsonl"

    audit_chunks(chunk_path, tokenizer)
