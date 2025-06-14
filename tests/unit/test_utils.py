"""
Unit tests for rag.utils.format_chunks_for_prompt.

These tests ensure that chunk formatting for LLM prompt context includes all required metadata, handles missing fields, and supports custom templates.
"""
import pytest
from rag.utils import format_chunks_for_prompt

def test_format_chunks_for_prompt_basic():
    """
    Test that basic chunk formatting includes text and all metadata fields.
    """
    chunks = [
        {"text": "This is a test.", "laureate": "Alice Smith", "year_awarded": 2001, "source_type": "nobel_lecture"},
        {"text": "Another chunk.", "laureate": "Bob Jones", "year_awarded": 1999, "source_type": "acceptance_speech"}
    ]
    result = format_chunks_for_prompt(chunks)
    # Check that all fields are present in the output
    assert "This is a test." in result
    assert "Alice Smith" in result
    assert "2001" in result
    assert "nobel_lecture" in result
    assert "Another chunk." in result
    assert "Bob Jones" in result
    assert "1999" in result
    assert "acceptance_speech" in result
    # There should be one separator between two chunks
    assert result.count("\n\n") == 1  # two chunks, one separator

def test_format_chunks_for_prompt_missing_fields():
    """
    Test that missing metadata fields are replaced with 'Unknown' in the output.
    """
    chunks = [
        {"text": "No metadata here."},
        {"text": "Partial.", "laureate": "Jane Doe"}
    ]
    result = format_chunks_for_prompt(chunks)
    assert "No metadata here." in result
    assert "Unknown" in result  # for missing fields
    assert "Partial." in result
    assert "Jane Doe" in result
    assert result.count("\n\n") == 1

def test_format_chunks_for_prompt_custom_template():
    """
    Test that a custom template formats the chunk as specified.
    """
    chunks = [
        {"text": "Custom template.", "laureate": "X", "year_awarded": 2020, "source_type": "speech"}
    ]
    template = "{laureate} ({year_awarded}): {text}"
    result = format_chunks_for_prompt(chunks, template=template)
    assert result == "X (2020): Custom template."

def test_format_chunks_for_prompt_empty_list():
    """Test that formatting an empty chunk list returns an empty string."""
    result = format_chunks_for_prompt([])
    assert result == ""

def test_format_chunks_for_prompt_all_metadata_missing():
    """Test that a chunk with only text and no metadata fields falls back to 'Unknown' for all metadata."""
    chunks = [{"text": "Only text."}]
    result = format_chunks_for_prompt(chunks)
    assert "Only text." in result
    assert "Unknown" in result  # for laureate, year_awarded, source_type 