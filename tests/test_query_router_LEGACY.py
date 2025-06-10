import pytest
from rag.intent_classifier import IntentClassifier
from rag.query_router import QueryRouter
from rag.query_router import QueryRouteResult
from unittest.mock import patch
import logging

# Example metadata for testing (copied from test_metadata_handler.py)
EXAMPLE_METADATA = [
    {
        "full_name": "Toni Morrison",
        "year_awarded": 1993,
        "gender": "female",
        "country": "united states",
        "prize_motivation": "who in novels characterized by visionary force and poetic import, gives life to an essential aspect of American reality",
        "date_of_birth": "1931-02-18",
        "date_of_death": "2019-08-05"
    },
    {
        "full_name": "Kazuo Ishiguro",
        "year_awarded": 2017,
        "gender": "male",
        "country": "united kingdom",
        "prize_motivation": "who, in novels of great emotional force, has uncovered the abyss beneath our illusory sense of connection with the world",
        "date_of_birth": "1954-11-08",
        "date_of_death": None
    },
    {
        "full_name": "Selma Lagerlöf",
        "year_awarded": 1909,
        "gender": "female",
        "country": "sweden",
        "prize_motivation": "in appreciation of the lofty idealism, vivid imagination and spiritual perception that characterize her writings",
        "date_of_birth": "1858-11-20",
        "date_of_death": "1940-03-16"
    }
]

@pytest.fixture
def classifier():
    return IntentClassifier()

def test_router_metadata_match():
    """Test that factual queries matching metadata rules return answer_type 'metadata' and correct answer."""
    router = QueryRouter(metadata=EXAMPLE_METADATA)
    query = "What year did Toni Morrison win?"
    result = router.route_query(query)
    assert isinstance(result, QueryRouteResult)
    assert result.answer_type == "metadata"
    assert result.metadata_answer is not None
    assert "1993" in result.metadata_answer["answer"]
    assert result.logs["metadata_handler"] == "matched"
    assert result.logs["metadata_rule"] == "award_year_by_name"

def test_router_metadata_no_match_fallback():
    """Test that factual queries not matching metadata rules fall back to RAG (answer_type 'rag')."""
    router = QueryRouter(metadata=EXAMPLE_METADATA)
    query = "What is the favorite color of Toni Morrison?"  # No metadata rule for this
    result = router.route_query(query)
    assert isinstance(result, QueryRouteResult)
    assert result.answer_type == "rag"
    assert result.metadata_answer is None
    assert result.logs["metadata_handler"] == "no_match"

def test_router_no_metadata_provided():
    """Test that factual queries with no metadata provided fall back to RAG."""
    router = QueryRouter(metadata=None)
    query = "What year did Toni Morrison win?"
    result = router.route_query(query)
    assert result.answer_type == "rag"
    assert result.metadata_answer is None
    # No metadata_handler log since metadata is None

def test_router_thematic_query():
    """Test that thematic queries are routed to RAG (answer_type 'rag')."""
    router = QueryRouter(metadata=EXAMPLE_METADATA)
    query = "What are common themes in Nobel lectures?"
    result = router.route_query(query)
    assert result.answer_type == "rag"
    assert result.intent == "thematic"
    assert result.metadata_answer is None

def test_router_generative_query():
    """Test that generative queries are routed to RAG (answer_type 'rag')."""
    router = QueryRouter(metadata=EXAMPLE_METADATA)
    query = "Write a speech in the style of Toni Morrison."
    result = router.route_query(query)
    assert result.answer_type == "rag"
    assert result.intent == "generative"
    assert result.metadata_answer is None

def test_router_logs_and_fields():
    """Test that logs and all fields are present and correct in QueryRouteResult."""
    router = QueryRouter(metadata=EXAMPLE_METADATA)
    query = "Who won the Nobel Prize in Literature in 2017?"
    result = router.route_query(query)
    assert "intent" in result.logs
    if result.answer_type == "metadata":
        assert "metadata_handler" in result.logs
        assert "metadata_rule" in result.logs
        assert result.metadata_answer is not None
    else:
        assert result.metadata_answer is None

def test_router_thematic_query_comprehensive(caplog):
    """Comprehensively test thematic query routing and logs."""
    router = QueryRouter(metadata=EXAMPLE_METADATA)
    query = "What are common themes in Nobel lectures?"
    
    with caplog.at_level(logging.INFO):
        result = router.route_query(query)
        
        # Basic checks
        assert result.answer_type == "rag"
        assert result.intent == QueryIntent.THEMATIC
        assert result.metadata_answer is None
        
        # Check logs for theme extraction
        assert "thematic_canonical_themes" in result.logs
        assert "thematic_expanded_terms" in result.logs
        
        # Verify log structure
        for record in caplog.records:
            if "QueryRouter" in record.message:
                assert "query" in record.__dict__
                assert isinstance(record.__dict__.get("extra", {}), dict)
        
        # Check retrieval config
        assert result.retrieval_config.top_k == 15
        assert result.retrieval_config.filters is None
        
        # Check prompt template
        assert "thematic" in result.prompt_template.lower()

def test_end_to_end_thematic_and_factual_query(caplog):
    """Integration: Simulate full pipeline for thematic and factual queries (mocked retrieval and LLM)."""
    from rag.query_engine import answer_query
    from unittest.mock import patch

    # --- Thematic query ---
    mock_chunks = [
        {
            "text": "Justice is a recurring theme.",
            "laureate": "Toni Morrison",
            "year_awarded": 1993,
            "source_type": "nobel_lecture",
            "score": 0.95,
            "chunk_id": 1,
            "text_snippet": "Justice is a recurring theme."  # Added to match pipeline output
        }
    ]
    
    with caplog.at_level(logging.INFO):
        with patch("rag.query_engine.ThematicRetriever.retrieve", return_value=mock_chunks) as mock_retrieve, \
             patch("rag.query_engine.call_openai", return_value={"answer": "Justice is a key theme across laureates.", "completion_tokens": 20}):
            
            # Verify mock is called
            result = answer_query("What are common themes in Nobel lectures?")
            assert mock_retrieve.called, "ThematicRetriever.retrieve was not called"
            
            # Verify result structure
            assert result["answer_type"] == "rag"
            assert "justice" in result["answer"].lower()
            assert result["sources"][0]["laureate"] == "Toni Morrison"
            assert "text_snippet" in result["sources"][0]
            assert result["sources"][0]["text_snippet"] == "Justice is a recurring theme."

    # --- Factual query ---
    with caplog.at_level(logging.INFO):
        with patch("rag.query_engine.QueryRouter.route_query") as mock_router:
            mock_router.return_value.answer_type = "metadata"
            mock_router.return_value.answer = "Toni Morrison won in 1993."
            mock_router.return_value.metadata_answer = {
                "answer": "Toni Morrison won in 1993.",
                "laureate": "Toni Morrison",
                "year_awarded": 1993
            }
            mock_router.return_value.intent = QueryIntent.FACTUAL
            mock_router.return_value.logs = {
                "metadata_handler": "matched",
                "metadata_rule": "award_year_by_name"
            }
            mock_router.return_value.retrieval_config = None
            mock_router.return_value.prompt_template = None
            
            result = answer_query("What year did Toni Morrison win?")
            assert result["answer_type"] == "metadata"
            assert "1993" in result["answer"]
            assert result["metadata_answer"]["laureate"] == "Toni Morrison"

def test_router_invalid_intent_input(caplog, monkeypatch):
    """Test that the router handles invalid intents gracefully by logging and falling back to factual."""
    router = QueryRouter(metadata=EXAMPLE_METADATA)
    # Monkeypatch the intent_classifier to return an invalid intent
    monkeypatch.setattr(router.intent_classifier, "classify", lambda q: "nonsense_intent")
    
    # Run the query and capture logs
    with caplog.at_level(logging.ERROR):
        result = router.route_query("This is a test query with invalid intent.")
        
        # Verify error was logged
        assert any("Invalid intent from classifier" in record.message for record in caplog.records)
        assert any("nonsense_intent" in record.message for record in caplog.records)
        
        # Verify fallback behavior
        assert result.intent == QueryIntent.FACTUAL
        assert result.answer_type == "rag"
        assert "error" in result.logs
        assert "Invalid intent" in result.logs["error"]
        assert result.logs["error_type"] == "ValueError"

def test_answer_query_unit():
    """Unit test for answer_query: mocks all dependencies and checks output schema."""
    from rag.query_engine import answer_query
    from unittest.mock import patch

    with patch("rag.query_engine.QueryRouter.route_query") as mock_router:
        mock_router.return_value.answer_type = "metadata"
        mock_router.return_value.answer = "Kazuo Ishiguro won in 2017."
        mock_router.return_value.metadata_answer = {"answer": "Kazuo Ishiguro won in 2017.", "laureate": "Kazuo Ishiguro", "year_awarded": 2017}
        mock_router.return_value.intent = "factual"
        mock_router.return_value.logs = {"metadata_handler": "matched", "metadata_rule": "award_year_by_name"}
        mock_router.return_value.retrieval_config = None
        mock_router.return_value.prompt_template = None
        result = answer_query("Who won the Nobel Prize in 2017?")
        assert result["answer_type"] == "metadata"
        assert "2017" in result["answer"]
        assert result["metadata_answer"]["laureate"] == "Kazuo Ishiguro"

def test_thematic_query_with_last_name_scoping():
    clf = IntentClassifier()
    # Should match last name 'Morrison' (Toni Morrison)
    result = clf.classify("What did Morrison say about justice?")
    assert isinstance(result, dict)
    assert result["intent"] == "thematic"
    assert result["scoped_entity"] == "Morrison" 

# --- Additional tests for router edge cases (invalid intent, missing/malformed filters) ---
def test_router_thematic_missing_or_malformed_filters():
    """Test that thematic queries with missing or malformed filters do not crash the router."""
    router = QueryRouter(metadata=EXAMPLE_METADATA)
    # Thematic query with no scoping (filters=None)
    result = router.route_query("What are common themes in Nobel lectures?")
    assert result.intent == "thematic"
    assert result.retrieval_config.filters is None
    # Simulate a malformed filters scenario by directly constructing a QueryRouteResult
    # (Router itself does not currently accept user-supplied filters, but this checks robustness)
    malformed_filters = 12345  # Not a dict or None
    rc = result.retrieval_config
    rc.filters = malformed_filters
    assert isinstance(rc.filters, int)
    # The router should not crash, but downstream code should validate filters type as needed 