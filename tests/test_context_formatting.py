from rag.query_router import format_factual_context
from rag.utils import format_chunks_for_prompt

def test_context_formatting_helpers():
    chunks = [
        {"text": "Alpha", "laureate": "A", "year_awarded": 2000, "source_type": "lecture"},
        {"text": "Beta", "laureate": "B", "year_awarded": 2001, "source_type": "lecture"},
    ]
    factual_context = format_factual_context(chunks)
    assert "- Alpha (A, 2000)" in factual_context
    assert "- Beta (B, 2001)" in factual_context
    thematic_context = format_chunks_for_prompt(chunks)
    assert "Alpha" in thematic_context
    assert "Beta" in thematic_context
    assert "A" in thematic_context
    assert "B" in thematic_context
    assert "2000" in thematic_context
    assert "2001" in thematic_context 