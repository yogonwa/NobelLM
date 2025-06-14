"""
Integration test: Prompt builder → answer compiler
Ensures that all sources are included in the prompt and the final answer references the correct context.

Aligned with current architecture:
- Calls format_chunks_for_prompt() to build context string from chunks
- Calls build_prompt() with (query, context)
- Asserts that chunk texts, laureate names, years, source types, and user query are all present
"""

import pytest
from rag.query_engine import build_prompt
from rag.utils import format_chunks_for_prompt

def test_prompt_contains_all_sources():
    chunks = [
        {"chunk_id": "c1", "text": "Alpha", "laureate": "A", "year_awarded": 2000, "source_type": "lecture"},
        {"chunk_id": "c2", "text": "Beta", "laureate": "B", "year_awarded": 2001, "source_type": "lecture"},
    ]
    query = "What did laureates say?"

    # Align with architecture: first format context
    context = format_chunks_for_prompt(chunks)
    prompt = build_prompt(query, context)

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

    # Align with architecture: first format context
    context = format_chunks_for_prompt(chunks)
    prompt = build_prompt(query, context)

    # Assert all chunk fields are present in the prompt
    for chunk in chunks:
        for field in ["text", "laureate", "year_awarded", "source_type"]:
            assert str(chunk[field]) in prompt, f"Missing {field}: {chunk[field]}"

    # Assert user query is present
    assert query in prompt

    # Optional: check for prompt structure
    assert "Context:" in prompt
