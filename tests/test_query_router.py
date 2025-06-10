# tests/test_query_router.py

import pytest
import logging
from rag.query_router import QueryRouter, QueryIntent
from rag.metadata_utils import load_laureate_metadata

# Example metadata fixture — use your real EXAMPLE_METADATA or load a small sample
EXAMPLE_METADATA = load_laureate_metadata()

# -----------------------------------------------------------------------------------
# Test basic routing behavior
# -----------------------------------------------------------------------------------

def test_router_factual_query():
    router = QueryRouter(metadata=EXAMPLE_METADATA)
    result = router.route_query("What year did Toni Morrison win the Nobel Prize?")
    
    assert result.intent == QueryIntent.FACTUAL
    assert result.answer_type in ("metadata", "rag")  # Allow both for coverage
    assert isinstance(result.logs, dict)

def test_router_thematic_query():
    router = QueryRouter(metadata=EXAMPLE_METADATA)
    result = router.route_query("What are common themes in Nobel lectures?")
    
    assert result.intent == QueryIntent.THEMATIC
    assert result.answer_type == "rag"
    assert isinstance(result.logs, dict)
    # Optional: check that thematic logs include themes
    assert "thematic_canonical_themes" in result.logs
    assert "thematic_expanded_terms" in result.logs

def test_router_generative_query():
    router = QueryRouter(metadata=EXAMPLE_METADATA)
    result = router.route_query("Write a speech in the style of Toni Morrison.")
    
    assert result.intent == QueryIntent.GENERATIVE
    assert result.answer_type == "rag"
    assert isinstance(result.logs, dict)

# -----------------------------------------------------------------------------------
# Test fallback / invalid intent handling
# -----------------------------------------------------------------------------------

def test_router_invalid_intent_fallback(monkeypatch, caplog):
    """Test that the router handles invalid intents gracefully by logging and falling back to factual."""
    router = QueryRouter(metadata=EXAMPLE_METADATA)

    # Force intent classifier to return unknown intent
    monkeypatch.setattr(router.intent_classifier, "classify", lambda q: "nonsense_intent")

    # Run the query and capture logs
    with caplog.at_level(logging.ERROR):
        result = router.route_query("This is a test query with invalid intent.")

        # Verify error was logged
        assert any("Invalid intent from classifier" in record.message for record in caplog.records)
        assert any("nonsense_intent" in record.message for record in caplog.records)

        # Verify fallback behavior — your router currently falls back to FACTUAL intent
        assert result.intent == QueryIntent.FACTUAL
        assert result.answer_type in ("metadata", "rag")  # Allow either fallback path
        assert isinstance(result.logs, dict)

    

# -----------------------------------------------------------------------------------
# Test logging for thematic query
# -----------------------------------------------------------------------------------

def test_router_thematic_logging(caplog):
    router = QueryRouter(metadata=EXAMPLE_METADATA)
    query = "What are common themes in Nobel lectures?"
    
    with caplog.at_level(logging.INFO):
        result = router.route_query(query)
        
        # Verify basic result is correct
        assert result.intent == QueryIntent.THEMATIC
        
        # Verify expected log messages
        assert any("Routing query" in record.message for record in caplog.records)
        assert any("Intent classified" in record.message for record in caplog.records)
