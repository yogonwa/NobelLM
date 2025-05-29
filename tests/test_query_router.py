import pytest
from rag.intent_classifier import IntentClassifier
from rag.query_router import QueryRouter
from rag.query_router import QueryRouteResult
from unittest.mock import patch

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

def test_router_thematic_query_comprehensive():
    """Comprehensively test thematic query routing and logs."""
    router = QueryRouter(metadata=EXAMPLE_METADATA)
    query = "What are common themes in Nobel lectures?"
    result = router.route_query(query)
    # Basic checks
    assert result.answer_type == "rag"
    assert result.intent == "thematic"
    assert result.metadata_answer is None
    # Check logs for theme extraction
    assert "thematic_canonical_themes" in result.logs
    assert "thematic_expanded_terms" in result.logs
    # Check retrieval config
    assert result.retrieval_config.top_k == 15
    # Check prompt template
    assert "literary analyst" in result.prompt_template  # or a more specific string from the thematic template 

def test_select_thematic_prompt_template():
    """Unit test: Ensure the correct thematic prompt template is returned for 'thematic' intent."""
    from rag.query_router import PromptTemplateSelector
    selector = PromptTemplateSelector()
    template = selector.select('thematic')
    # Check for key thematic instructions and structure
    assert "literary analyst" in template
    assert "User question:" in template
    assert "Excerpts:" in template
    assert "Instructions:" in template
    assert "Identify prominent or recurring themes" in template
    assert "Reference the speaker and year when relevant" in template
    # Should not be a factual template
    assert "Answer the question using only the information in the context" not in template
    # Should raise ValueError for unknown intent
    import pytest
    with pytest.raises(ValueError):
        selector.select('unknown_intent') 

def test_end_to_end_thematic_query():
    """Integration: Simulate a full thematic query pipeline with mocked retrieval and LLM."""
    from rag.query_engine import answer_query

    # Mock the retrieval to return fixed chunks
    mock_chunks = [
        {
            "text": "Justice is a recurring theme.",
            "laureate": "Toni Morrison",
            "year_awarded": 1993,
            "source_type": "nobel_lecture",
            "score": 0.95,
            "chunk_id": 1
        }
    ]
    # Patch the retrieval and LLM call
    with patch("rag.query_engine.ThematicRetriever.retrieve", return_value=mock_chunks), \
         patch("rag.query_engine.call_openai", return_value={"answer": "Justice is a key theme across laureates.", "completion_tokens": 20}):
        result = answer_query("What are common themes in Nobel lectures?")
        assert result["answer_type"] == "rag"
        assert "justice" in result["answer"].lower()
        assert result["sources"][0]["laureate"] == "Toni Morrison"
        assert "text_snippet" in result["sources"][0] 

def test_thematic_query_with_last_name_scoping():
    clf = IntentClassifier()
    # Should match last name 'Morrison' (Toni Morrison)
    result = clf.classify("What did Morrison say about justice?")
    assert isinstance(result, dict)
    assert result["intent"] == "thematic"
    assert result["scoped_entity"] == "Morrison" 