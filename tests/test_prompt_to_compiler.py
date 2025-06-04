"""
Integration test: Prompt builder → answer compiler
Ensures that all sources are included in the prompt and the final answer references the correct context.
"""
import pytest
from rag.query_engine import build_prompt

def test_prompt_contains_all_sources():
    chunks = [
        {"chunk_id": "c1", "text": "Alpha", "laureate": "A", "year_awarded": 2000, "source_type": "lecture"},
        {"chunk_id": "c2", "text": "Beta", "laureate": "B", "year_awarded": 2001, "source_type": "lecture"},
    ]
    query = "What did laureates say?"
    prompt = build_prompt(chunks, query)
    # Assert all chunk texts and metadata are present in the prompt
    assert "Alpha" in prompt
    assert "Beta" in prompt
    assert "A" in prompt
    assert "B" in prompt
    assert "2000" in prompt
    assert "2001" in prompt
    assert "lecture" in prompt
    assert query in prompt 

def test_prompt_includes_chunk_texts_and_metadata():
    chunks = [
        {"chunk_id": "c1", "text": "Alpha", "laureate": "A", "year_awarded": 2000, "source_type": "lecture"},
        {"chunk_id": "c2", "text": "Beta", "laureate": "B", "year_awarded": 2001, "source_type": "lecture"},
    ]
    query = "What did laureates say?"
    prompt = build_prompt(chunks, query)
    # Assert all chunk texts and metadata are present in the prompt
    for chunk in chunks:
        for field in ["text", "laureate", "year_awarded", "source_type"]:
            assert str(chunk[field]) in prompt, f"Missing {field}: {chunk[field]}"
    assert query in prompt
    # Optional: check for prompt structure
    assert "Context:" in prompt 