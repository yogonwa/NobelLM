"""
chunk_literature_speeches.py

Chunk and tag Nobel Literature speeches for embedding.
Outputs newline-delimited JSONL with rich metadata per chunk.

Inputs:
- data/nobel_literature.json
- data/nobel_lectures/*.txt
- data/acceptance_speeches/*.txt
- data/ceremony_speeches/*.txt

Output:
- data/chunks_literature_labeled.jsonl
"""

import os
import json
import logging
from typing import List, Dict, Any
import re

logging.basicConfig(level=logging.INFO)


def load_metadata(json_path: str) -> List[Dict[str, Any]]:
    """Load laureate metadata from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_speech_text(file_path: str) -> str:
    """Load text from a speech file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read().strip()


def split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs using double newlines."""
    return [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]


def chunk_paragraphs(paragraphs: List[str], min_words: int = 200, max_words: int = 500) -> List[str]:
    """Accumulate paragraphs into chunks of ~300–500 words, no mid-sentence splits."""
    chunks = []
    current_chunk = []
    current_len = 0
    for para in paragraphs:
        para_words = para.split()
        if current_len + len(para_words) > max_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_len = 0
        current_chunk.append(para)
        current_len += len(para_words)
    if current_chunk:
        # Merge with previous if too short
        if len(current_chunk) > 1 and sum(len(p.split()) for p in current_chunk) < min_words and chunks:
            chunks[-1] += " " + " ".join(current_chunk)
        else:
            chunks.append(" ".join(current_chunk))
    return chunks


def build_chunk(
    text: str,
    source_type: str,
    laureate: str,
    year_awarded: int,
    category: str,
    chunk_index: int,
    gender: str,
    country: str,
    specific_work_cited: bool,
    prize_motivation: str,
    lastname: str
) -> Dict[str, Any]:
    """Build a chunk dict with all required metadata fields, including a unique chunk_id."""
    chunk_id = f"{year_awarded}_{lastname}_{source_type}_{chunk_index}"
    return {
        "chunk_id": chunk_id,
        "source_type": source_type,
        "category": category,
        "laureate": laureate,
        "year_awarded": year_awarded,
        "chunk_index": chunk_index,
        "gender": gender,
        "country": country,
        "specific_work_cited": specific_work_cited,
        "prize_motivation": prize_motivation,
        "text": text
    }


def process_all_speeches(
    metadata_path: str,
    lectures_dir: str,
    acceptance_dir: str,
    ceremony_dir: str,
    output_path: str
) -> None:
    """Main pipeline: loads metadata, processes all speeches, writes output JSONL."""
    metadata = load_metadata(metadata_path)
    chunks = []
    for year_record in metadata:
        year = year_record["year_awarded"]
        category = year_record["category"]
        for laureate in year_record["laureates"]:
            name = laureate["full_name"]
            gender = laureate.get("gender", "")
            country = laureate.get("country", "")
            specific_work_cited = laureate.get("specific_work_cited", False)
            prize_motivation = laureate.get("prize_motivation", "")
            lastname = name.split()[-1].lower()
            # Nobel lecture
            lecture_path = os.path.join(lectures_dir, f"{year}_{lastname}.txt")
            if os.path.exists(lecture_path):
                text = load_speech_text(lecture_path)
                paragraphs = split_paragraphs(text)
                for idx, chunk_text in enumerate(chunk_paragraphs(paragraphs)):
                    chunk = build_chunk(
                        text=chunk_text,
                        source_type="nobel_lecture",
                        laureate=name,
                        year_awarded=year,
                        category=category,
                        chunk_index=idx,
                        gender=gender,
                        country=country,
                        specific_work_cited=specific_work_cited,
                        prize_motivation=prize_motivation,
                        lastname=lastname
                    )
                    chunks.append(chunk)
            # Acceptance speech
            acceptance_path = os.path.join(acceptance_dir, f"{year}_{lastname}.txt")
            if os.path.exists(acceptance_path):
                text = load_speech_text(acceptance_path)
                paragraphs = split_paragraphs(text)
                for idx, chunk_text in enumerate(chunk_paragraphs(paragraphs)):
                    chunk = build_chunk(
                        text=chunk_text,
                        source_type="acceptance_speech",
                        laureate=name,
                        year_awarded=year,
                        category=category,
                        chunk_index=idx,
                        gender=gender,
                        country=country,
                        specific_work_cited=specific_work_cited,
                        prize_motivation=prize_motivation,
                        lastname=lastname
                    )
                    chunks.append(chunk)
            # Ceremony speech
            ceremony_path = os.path.join(ceremony_dir, f"{year}.txt")
            if os.path.exists(ceremony_path):
                text = load_speech_text(ceremony_path)
                paragraphs = split_paragraphs(text)
                for idx, chunk_text in enumerate(chunk_paragraphs(paragraphs)):
                    chunk = build_chunk(
                        text=chunk_text,
                        source_type="ceremony_speech",
                        laureate=name,
                        year_awarded=year,
                        category=category,
                        chunk_index=idx,
                        gender=gender,
                        country=country,
                        specific_work_cited=specific_work_cited,
                        prize_motivation=prize_motivation,
                        lastname=lastname
                    )
                    chunks.append(chunk)
            # Prize motivation, life_blurb, work_blurb as single chunks
            for field, stype in [("prize_motivation", "prize_motivation"), ("life_blurb", "life_blurb"), ("work_blurb", "work_blurb")]:
                value = laureate.get(field, None)
                if value:
                    chunk = build_chunk(
                        text=value,
                        source_type=stype,
                        laureate=name,
                        year_awarded=year,
                        category=category,
                        chunk_index=0,
                        gender=gender,
                        country=country,
                        specific_work_cited=specific_work_cited,
                        prize_motivation=prize_motivation,
                        lastname=lastname
                    )
                    chunks.append(chunk)
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    logging.info(f"Wrote {len(chunks)} chunks to {output_path}")


if __name__ == "__main__":
    process_all_speeches(
        metadata_path="data/nobel_literature.json",
        lectures_dir="data/nobel_lectures",
        acceptance_dir="data/acceptance_speeches",
        ceremony_dir="data/ceremony_speeches",
        output_path="data/chunks_literature_labeled.jsonl"
    ) 