"""
Integration test: intent_classifier → query_router
Covers routing for thematic queries in the RAG pipeline.
"""
import pytest
import logging
from typing import Any
from rag.query_router import QueryRouter

# Set up logging for test clarity
logging.basicConfig(level=logging.INFO)

@pytest.fixture
def thematic_query() -> str:
    """Fixture for a sample thematic user query."""
    return "What themes of hope are present in Nobel Peace Prize speeches?"


@pytest.mark.integration
def test_routing_from_thematic_intent(thematic_query: str) -> None:
    """
    Integration test: Checks that a thematic query is classified and routed correctly.
    Asserts that the router selects the correct intent, answer_type, and top_k for thematic queries.
    """
    router = QueryRouter()
    route_result = router.route_query(thematic_query)
    logging.info(f"Router output: {route_result}")

    # Assert correct intent
    assert route_result.intent == "thematic", f"Expected intent 'thematic', got '{route_result.intent}'"
    # Assert answer_type is 'rag' (not metadata)
    assert route_result.answer_type == "rag", f"Expected answer_type 'rag', got '{route_result.answer_type}'"
    # Assert top_k is 15 for thematic queries
    assert route_result.retrieval_config.top_k == 15, f"Expected top_k 15 for thematic, got {route_result.retrieval_config.top_k}" 