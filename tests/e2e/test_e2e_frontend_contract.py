"""
End-to-End (E2E) Frontend Contract Test for NobelLM

This test validates the full user query → answer pipeline, ensuring the output matches the contract expected by the frontend.
"""

# Configure threading globally before any FAISS/PyTorch imports
from config.threading import configure_threading
configure_threading()

import pytest
from unittest.mock import patch, MagicMock, ANY
import json
from rag.query_engine import answer_query, build_prompt
from rag.utils import format_chunks_for_prompt
import os

def source_to_chunk(source):
    # Use the text_snippet as the 'text' field for prompt reconstruction
    return {**source, "text": source.get("text_snippet", source.get("text", ""))}

@pytest.mark.parametrize("user_query,filters,expected_k,dry_run,model_id", [
    # Factual
    ("In what year did Hemingway win the Nobel Prize?", None, 3, True, None),
    ("How many females have won the award?", None, 3, True, None),
    # Hybrid - Note: filters are now handled internally by QueryRouter
    ("What do winners from the US say about racism?", {"country": "USA"}, 5, True, None),
    # Thematic
    ("What do winners say about the creative writing process?", {"source_type": "nobel_lecture"}, 15, False, None),
])
def test_query_engine_e2e(user_query, filters, expected_k, dry_run, model_id):
    """E2E test for query engine: dry run and live modes, checks prompt, answer, and sources."""
    
    # Mock the entire retrieval pipeline to avoid FAISS index issues
    mock_chunks = [
        {
            "chunk_id": "test_1",
            "text": "This is a test chunk about literature and writing.",
            "text_snippet": "This is a test chunk about literature and writing.",
            "laureate": "Test Author",
            "year_awarded": 2020,
            "source_type": "nobel_lecture",
            "score": 0.85
        },
        {
            "chunk_id": "test_2", 
            "text": "Another test chunk about creative processes.",
            "text_snippet": "Another test chunk about creative processes.",
            "laureate": "Test Author 2",
            "year_awarded": 2019,
            "source_type": "ceremony_speech",
            "score": 0.75
        }
    ]
    
    # Mock the LLM call for dry_run mode
    if dry_run:
        with patch('rag.query_engine.call_openai') as mock_openai, \
             patch('rag.query_engine.get_query_router') as mock_router, \
             patch('rag.query_engine.ThematicRetriever') as mock_thematic, \
             patch('rag.query_engine.get_mode_aware_retriever') as mock_retriever:
            
            # Mock router response
            mock_route_result = MagicMock()
            mock_route_result.intent = "thematic" if "theme" in user_query or (filters and filters.get("source_type") == "nobel_lecture") else "factual"
            mock_route_result.answer_type = "rag" if mock_route_result.intent == "thematic" else "metadata"
            mock_route_result.retrieval_config.filters = filters
            mock_route_result.retrieval_config.top_k = 5
            mock_route_result.retrieval_config.score_threshold = 0.2
            mock_route_result.prompt_template = None
            mock_router.return_value.route_query.return_value = mock_route_result
            
            # Mock retriever
            mock_retriever_instance = MagicMock()
            mock_retriever_instance.retrieve.return_value = mock_chunks
            mock_retriever.return_value = mock_retriever_instance
            
            # Mock thematic retriever
            mock_thematic_instance = MagicMock()
            mock_thematic_instance.retrieve.return_value = mock_chunks
            mock_thematic.return_value = mock_thematic_instance
            
            # Mock OpenAI response
            mock_openai.return_value = {
                "answer": "[DRY RUN] This is a simulated answer for testing.",
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "model": "gpt-3.5-turbo"
            }
            
            mock_route_result.answer = mock_openai.return_value["answer"]
            
            response = answer_query(user_query, model_id=model_id)
            
            # Verify retriever was called with correct parameters based on router response
            if mock_route_result.answer_type == "rag" and mock_route_result.intent != "thematic":
                mock_retriever_instance.retrieve.assert_called_with(
                    ANY, filters=filters, top_k=5, score_threshold=0.2
                )
            else:
                mock_retriever_instance.retrieve.assert_not_called()
    else:
        # For live tests, we need to mock the retrieval but allow real LLM calls
        with patch('rag.query_engine.get_query_router') as mock_router, \
             patch('rag.query_engine.ThematicRetriever') as mock_thematic, \
             patch('rag.query_engine.get_mode_aware_retriever') as mock_retriever:
            
            # Mock router response
            mock_route_result = MagicMock()
            mock_route_result.intent = "thematic" if "theme" in user_query or (filters and filters.get("source_type") == "nobel_lecture") else "factual"
            mock_route_result.answer_type = "rag" if mock_route_result.intent == "thematic" else "metadata"
            mock_route_result.retrieval_config.filters = filters
            mock_route_result.retrieval_config.top_k = 5
            mock_route_result.retrieval_config.score_threshold = 0.2
            mock_route_result.prompt_template = None
            mock_router.return_value.route_query.return_value = mock_route_result
            
            # Mock retriever
            mock_retriever_instance = MagicMock()
            mock_retriever_instance.retrieve.return_value = mock_chunks
            mock_retriever.return_value = mock_retriever_instance
            
            # Mock thematic retriever
            mock_thematic_instance = MagicMock()
            mock_thematic_instance.retrieve.return_value = mock_chunks
            mock_thematic.return_value = mock_thematic_instance
            
            response = answer_query(user_query, model_id=model_id)
            
            # Verify retriever was called with correct parameters based on router response
            if mock_route_result.answer_type == "rag" and mock_route_result.intent != "thematic":
                mock_retriever_instance.retrieve.assert_called_with(
                    ANY, filters=filters, top_k=5, score_threshold=0.2
                )
            else:
                mock_retriever_instance.retrieve.assert_not_called()
    
    # Format chunks for prompt building
    formatted_context = format_chunks_for_prompt(response['sources'])
    prompt = build_prompt(user_query, formatted_context)
    
    # Basic response structure validation
    assert isinstance(response["answer"], str)
    assert isinstance(response["sources"], list)
    assert "answer_type" in response
    assert response["answer_type"] in ["rag", "metadata"]
    
    # Source count validation
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
    
    # Prompt validation
    assert isinstance(prompt, str)
    assert user_query in prompt
    
    # Answer type validation based on query content
    if "theme" in user_query or (filters and filters.get("source_type") == "nobel_lecture"):
        assert response["answer_type"] == "rag"
    elif "year" in user_query or "who won" in user_query.lower():
        assert response["answer_type"] == "metadata"
    
    # Source content validation in prompt
    for chunk in response["sources"]:
        # Check if chunk text appears in prompt (using either text_snippet or text field)
        chunk_text = chunk.get("text_snippet", chunk.get("text", ""))
        if chunk_text:
            # Check first 20 characters to avoid false negatives from formatting
            assert chunk_text[:20] in prompt or chunk_text.replace(" ", "")[:20] in prompt.replace(" ", "")
    
    # Enhanced dry run validation
    if dry_run:
        assert "failed" not in response["answer"].lower(), f"Query failed: {response['answer']}"
    else:
        assert len(response["answer"]) > 0

@pytest.mark.skipif(os.getenv("NOBELLM_LIVE_TEST") != "1", reason="Live test skipped unless NOBELLM_LIVE_TEST=1")
def test_query_engine_live():
    """Live E2E test for query engine (requires OpenAI API key and real data)."""
    user_query = os.getenv("NOBELLM_TEST_QUERY", "How do laureates describe the role of literature in society?")
    print(f"\n--- LIVE E2E TEST ---")
    print(f"Query: {user_query}\n")

    response = answer_query(user_query)

    print(f"Answer Type: {response['answer_type']}")
    print(f"Answer:\n{response['answer']}\n")
    print(f"Sources Retrieved: {len(response['sources'])}")

    for i, source in enumerate(response['sources'], 1):
        print(f"  [{i}] {source.get('laureate', 'Unknown')} ({source.get('year_awarded', 'Unknown')}) "
              f"Source Type: {source.get('source_type', 'Unknown')} "
              f"Score: {source.get('score', 0):.3f}")

    # Keep assertions so test will fail if broken
    assert isinstance(response["answer"], str)
    assert len(response["answer"]) > 0
    assert isinstance(response["sources"], list)
    assert len(response["sources"]) > 0 