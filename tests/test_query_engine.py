"""
Test script for the NobelLM Query Engine.

Demonstrates dry run and real query modes, with and without metadata filters.
"""
import logging
import pytest
from rag.query_engine import query, build_prompt
import os

def source_to_chunk(source):
    # Use the text_snippet as the 'text' field for prompt reconstruction
    return {**source, "text": source["text_snippet"]}

def main(model_id=None):
    logging.basicConfig(level=logging.INFO)
    print("\n=== NobelLM Query Engine Test ===\n")

    # Example 1: Dry run, no filters
    user_query = "What do laureates say about justice?"
    print("[Dry Run] General query (no filters):")
    response = query(
        user_query,
        dry_run=False,
        model_id=model_id
    )
    prompt = build_prompt([source_to_chunk(s) for s in response['sources']], user_query)
    print(f"User Query: {user_query}")
    print(f"Prompt to LLM:\n{prompt}\n")
    print(f"Answer:\n{response['answer']}\n")
    print(f"Filters: None")
    print(f"k Value: 3")
    print(f"Sources (count: {len(response['sources'])}):")
    for src in response['sources']:
        print(f"  - {src}")
    print("\n" + "-"*40 + "\n")

    # Example 2: Dry run, with filters
    user_query = "What do USA winners talk about in their lectures?"
    filters = {"country": "USA", "source_type": "nobel_lecture"}
    print("[Dry Run] Filtered by country and source_type:")
    response = query(
        user_query,
        filters=filters,
        dry_run=False,
        model_id=model_id
    )
    prompt = build_prompt([source_to_chunk(s) for s in response['sources']], user_query)
    print(f"User Query: {user_query}")
    print(f"Prompt to LLM:\n{prompt}\n")
    print(f"Answer:\n{response['answer']}\n")
    print(f"Filters: {filters}")
    print(f"k Value: 3")
    print(f"Sources (count: {len(response['sources'])}):")
    for src in response['sources']:
        print(f"  - {src}")
    print("\n" + "-"*40 + "\n")

    # Example 4: Thematic (broad) query to test dynamic top_k
    user_query = "What themes are common across Nobel lectures?"
    filters = {"source_type": "nobel_lecture"}
    print("[Real Query] Thematic query (should trigger top_k=15):")
    response = query(
        user_query,
        filters=filters,
        dry_run=False,
        model_id=model_id
    )
    prompt = build_prompt([source_to_chunk(s) for s in response['sources']], user_query)
    print(f"User Query: {user_query}")
    print(f"Prompt to LLM:\n{prompt}\n")
    print(f"Answer:\n{response['answer']}\n")
    print(f"Filters: {filters}")
    print(f"k Value: 15")
    print(f"Sources (count: {len(response['sources'])}):")
    for src in response['sources']:
        print(f"  - {src}")
    print("\n" + "-"*40 + "\n")

    print("✅ All test queries executed successfully.")

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
    assert len(response["sources"]) <= expected_k
    assert isinstance(prompt, str)
    # Enhanced dry run validation
    if dry_run:
        assert "failed" not in response["answer"].lower(), f"Query failed: {response['answer']}"
    else:
        assert len(response["answer"]) > 0

# Optionally, add a marker or env flag to skip live tests unless requested
@pytest.mark.skipif(os.getenv("NOBELLM_LIVE_TEST") != "1", reason="Live test skipped unless NOBELLM_LIVE_TEST=1")
def test_query_engine_live():
    """Live E2E test for query engine (requires OpenAI API key and real data)."""
    user_query = "How do laureates describe the role of literature in society?"
    response = query(user_query, dry_run=False)
    assert isinstance(response["answer"], str)
    assert len(response["answer"]) > 0
    assert isinstance(response["sources"], list)
    assert len(response["sources"]) > 0

if __name__ == "__main__":
    main() 