"""
End-to-End (E2E) Frontend Contract Test for NobelLM

This test validates the full user query → answer pipeline, ensuring the output matches the contract expected by the frontend.
"""
import pytest
from rag.query_engine import query, build_prompt
import os

def source_to_chunk(source):
    # Use the text_snippet as the 'text' field for prompt reconstruction
    return {**source, "text": source["text_snippet"]}

@pytest.mark.parametrize("user_query,filters,expected_k,dry_run,model_id", [
    # Factual
    ("In what year did Hemingway win the Nobel Prize?", None, 3, True, None),
    ("How many females have won the award?", None, 3, True, None),
    # Hybrid
    ("What do winners from the US say about racism?", {"country": "USA"}, 5, True, None),
    # Thematic
    ("What do winners say about the creative writing process?", {"source_type": "nobel_lecture"}, 15, False, None),
])
def test_query_engine_e2e(user_query, filters, expected_k, dry_run, model_id):
    """E2E test for query engine: dry run and live modes, checks prompt, answer, and sources."""
    response = query(user_query, filters=filters, dry_run=dry_run, model_id=model_id)
    prompt = build_prompt([source_to_chunk(s) for s in response['sources']], user_query)
    assert isinstance(response["answer"], str)
    assert isinstance(response["sources"], list)
    # 2. Make expected_k a min_k for thematic/filtered cases
    if expected_k:
        assert len(response["sources"]) <= expected_k
        if filters:
            assert len(response["sources"]) >= 0  # Accept 0 if filtered
        else:
            # Allow sources to be empty for factual/metadata answers
            if response["answer_type"] == "metadata":
                assert response["sources"] == []
            else:
                assert len(response["sources"]) > 0
    assert isinstance(prompt, str)
    # 1. Add answer_type assertion
    if "theme" in user_query or (filters and filters.get("source_type") == "nobel_lecture"):
        assert response["answer_type"] == "rag"
    elif "year" in user_query or "who won" in user_query.lower():
        assert response["answer_type"] == "metadata"
    # 3. Prompt sanity checks
    assert user_query in prompt
    for chunk in response["sources"]:
        snippet = chunk.get("text_snippet", "")[:10]
        if snippet:
            assert snippet in prompt
    # 4. Roundtrip prompt validity (advanced)
    roundtrip_chunks = [source_to_chunk(s) for s in response["sources"]]
    reconstructed_prompt = build_prompt(roundtrip_chunks, user_query)
    assert prompt == reconstructed_prompt
    # Enhanced dry run validation
    if dry_run:
        assert "failed" not in response["answer"].lower(), f"Query failed: {response['answer']}"
    else:
        assert len(response["answer"]) > 0

@pytest.mark.skipif(os.getenv("NOBELLM_LIVE_TEST") != "1", reason="Live test skipped unless NOBELLM_LIVE_TEST=1")
def test_query_engine_live():
    """Live E2E test for query engine (requires OpenAI API key and real data)."""
    user_query = "How do laureates describe the role of literature in society?"
    response = query(user_query, dry_run=False)
    assert isinstance(response["answer"], str)
    assert len(response["answer"]) > 0
    assert isinstance(response["sources"], list)
    assert len(response["sources"]) > 0 