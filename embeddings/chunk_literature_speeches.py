"""
chunk_literature_speeches.py

Chunk and tag Nobel Literature speeches for embedding.
Supports multiple embedding models and optional chunk overlap.
Ensures all chunks remain under model token limits.

Inputs:
- data/nobel_literature.json
- data/nobel_lectures/*.txt
- data/acceptance_speeches/*.txt
- data/ceremony_speeches/*.txt

Outputs (model-dependent):
- data/chunks_literature_labeled_{model}.jsonl

Run via CLI with optional flags:
    python chunk_literature_speeches.py --model bge-large --overlap 50
"""

import os
import json
import logging
import argparse
import re
from typing import List, Dict, Any
from transformers import AutoTokenizer
from rag.model_config import get_model_config, DEFAULT_MODEL_ID

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def load_metadata(path: str) -> List[Dict[str, Any]]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_text(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().strip()


def split_paragraphs(text: str) -> List[str]:
    return [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]


def split_long_text(text: str, tokenizer, max_tokens: int) -> List[str]:
    tokens = tokenizer.encode(text, add_special_tokens=False)
    chunks = []
    while tokens:
        sub_tokens = tokens[:max_tokens]
        chunks.append(tokenizer.decode(sub_tokens))
        tokens = tokens[max_tokens:]
    return chunks


def chunk_paragraphs(paragraphs: List[str], tokenizer, max_tokens: int, overlap: int = 0) -> List[str]:
    chunks, current_chunk, current_tokens = [], [], []
    for para in paragraphs:
        para_tokens = tokenizer.encode(para, add_special_tokens=False)
        while len(para_tokens) > max_tokens:
            sub_tokens = para_tokens[:max_tokens]
            chunks.append(tokenizer.decode(sub_tokens))
            para_tokens = para_tokens[max_tokens:]
        if len(current_tokens) + len(para_tokens) > max_tokens and current_chunk:
            chunk_text = " ".join(current_chunk)
            if len(tokenizer.encode(chunk_text, add_special_tokens=False)) <= max_tokens:
                chunks.append(chunk_text)
            else:
                chunks.extend(split_long_text(chunk_text, tokenizer, max_tokens))
            if overlap > 0:
                overlap_tokens = current_tokens[-overlap:]
                current_chunk = [tokenizer.decode(overlap_tokens)]
                current_tokens = overlap_tokens.copy()
            else:
                current_chunk, current_tokens = [], []
        current_chunk.append(para)
        current_tokens.extend(para_tokens)
    if current_chunk:
        final_text = " ".join(current_chunk)
        if len(tokenizer.encode(final_text, add_special_tokens=False)) <= max_tokens:
            chunks.append(final_text)
        else:
            chunks.extend(split_long_text(final_text, tokenizer, max_tokens))
    return chunks


def build_chunk(text: str, source_type: str, chunk_index: int, **meta) -> Dict[str, Any]:
    chunk_id = f"{meta['year_awarded']}_{meta['lastname']}_{source_type}_{chunk_index}"
    return {
        "chunk_id": chunk_id,
        "source_type": source_type,
        "chunk_index": chunk_index,
        "text": text,
        **meta
    }


def chunk_speech_file(path: str, source_type: str, tokenizer, max_tokens: int, overlap: int, meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    text = load_text(path)
    if not text:
        return []
    paragraphs = split_paragraphs(text)
    chunked = chunk_paragraphs(paragraphs, tokenizer, max_tokens, overlap)
    return [build_chunk(text=c, source_type=source_type, chunk_index=i, **meta) for i, c in enumerate(chunked)]


def process_all(metadata_path: str, lectures_dir: str, acceptance_dir: str, ceremony_dir: str, output_path: str, tokenizer, max_tokens: int, overlap: int) -> None:
    metadata = load_metadata(metadata_path)
    chunks = []
    for record in metadata:
        year, category = record["year_awarded"], record["category"]
        for laureate in record["laureates"]:
            name = laureate["full_name"]
            lastname = name.split()[-1].lower()
            meta = {
                "laureate": name,
                "year_awarded": year,
                "category": category,
                "gender": laureate.get("gender", ""),
                "country": laureate.get("country", ""),
                "specific_work_cited": laureate.get("specific_work_cited", False),
                "prize_motivation": laureate.get("prize_motivation", ""),
                "lastname": lastname
            }
            chunks.extend(chunk_speech_file(os.path.join(lectures_dir, f"{year}_{lastname}.txt"), "nobel_lecture", tokenizer, max_tokens, overlap, meta))
            chunks.extend(chunk_speech_file(os.path.join(acceptance_dir, f"{year}_{lastname}.txt"), "acceptance_speech", tokenizer, max_tokens, overlap, meta))
            chunks.extend(chunk_speech_file(os.path.join(ceremony_dir, f"{year}.txt"), "ceremony_speech", tokenizer, max_tokens, overlap, meta))
            for field, stype in [("prize_motivation", "prize_motivation"), ("life_blurb", "life_blurb"), ("work_blurb", "work_blurb")]:
                value = laureate.get(field)
                if value:
                    split = split_long_text(value, tokenizer, max_tokens) if stype in ["life_blurb", "work_blurb"] else [value]
                    for i, text in enumerate(split):
                        chunks.append(build_chunk(text, stype, i, **meta))
    with open(output_path, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    logging.info(f"Wrote {len(chunks)} chunks to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL_ID, choices=list(get_model_config().keys()), help="Embedding model name")
    parser.add_argument("--overlap", type=int, default=0, help="Token overlap between chunks")
    args = parser.parse_args()

    config = get_model_config(args.model)
    tokenizer = AutoTokenizer.from_pretrained(config["model_name"])
    # Set max_tokens based on model config or a sensible default
    max_tokens = 500 if args.model == "bge-large" else 250

    output_file = f"data/chunks_literature_labeled_{args.model}.jsonl"
    process_all(
        metadata_path="data/nobel_literature.json",
        lectures_dir="data/nobel_lectures",
        acceptance_dir="data/acceptance_speeches",
        ceremony_dir="data/ceremony_speeches",
        output_path=output_file,
        tokenizer=tokenizer,
        max_tokens=max_tokens,
        overlap=args.overlap
    )
