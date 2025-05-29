"""
rag.utils: Shared utilities for the NobelLM RAG pipeline.

Includes:
- format_chunks_for_prompt: Utility to format retrieved text chunks (with metadata) for LLM prompt construction.

This ensures that every chunk passed to the LLM includes not just the text, but also key metadata (laureate, year, source type), improving answer quality and explainability.
"""
from typing import List, Dict

def format_chunks_for_prompt(
    chunks: List[Dict],
    fields=("text", "laureate", "year_awarded", "source_type"),
    template="{text} (by {laureate}, {year_awarded}, {source_type})"
) -> str:
    """
    Format a list of text chunks (with metadata) for inclusion in an LLM prompt.

    Each chunk is formatted as a string including its text and selected metadata fields.
    The default template is: '{text} (by {laureate}, {year_awarded}, {source_type})'.
    All formatted chunks are joined with double newlines for clear separation in the prompt context.

    Args:
        chunks: List of chunk dicts, each with at least a 'text' field and optional metadata.
        fields: Tuple of fields to include (default: text, laureate, year_awarded, source_type).
        template: Format string for each chunk. Should use named placeholders matching the fields.
    Returns:
        String with all formatted chunks, separated by double newlines, ready for LLM prompt context.
    Example:
        >>> chunks = [{"text": "Example.", "laureate": "Alice", "year_awarded": 2000, "source_type": "lecture"}]
        >>> format_chunks_for_prompt(chunks)
        'Example. (by Alice, 2000, lecture)'
    """
    lines = []
    for chunk in chunks:
        # Use .get() for safety in case some fields are missing; fallback to 'Unknown' for missing metadata
        lines.append(template.format(
            text=chunk.get("text", ""),
            laureate=chunk.get("laureate", "Unknown"),
            year_awarded=chunk.get("year_awarded", "Unknown"),
            source_type=chunk.get("source_type", "Unknown")
        ))
    return "\n\n".join(lines) 