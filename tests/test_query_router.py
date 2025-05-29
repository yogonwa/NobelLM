import pytest
from rag.query_router import IntentClassifier, QueryRouter
from rag.query_router import QueryRouteResult

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

def test_factual_query(classifier):
    """Test that a direct factual question is classified as factual."""
    queries = [
        "What did Toni Morrison say about justice?",
        "When did Kazuo Ishiguro win the Nobel Prize?",
        "Where was Camilo José Cela born?",
        "Summarize the 1989 acceptance speech.",
        "Who won the Nobel Prize in 2001?",
        "Give me the speech by Seamus Heaney."
    ]
    for q in queries:
        assert classifier.classify(q) == "factual"

def test_thematic_query(classifier):
    """Test that a thematic/analytical question is classified as thematic."""
    queries = [
        "What are common themes in Nobel lectures?",
        "How have topics changed over time?",
        "Compare speeches from U.S. vs. European laureates.",
        "What motifs are recurring across decades?",
        "What patterns emerge in acceptance speeches?",
        "Are there typical themes in Peace Prize lectures?"
    ]
    for q in queries:
        assert classifier.classify(q) == "thematic"

def test_generative_query(classifier):
    """Test that a generative/stylistic request is classified as generative."""
    queries = [
        "Write a speech in the style of Toni Morrison.",
        "Compose a Nobel acceptance for a teacher.",
        "Paraphrase this text as if written by a laureate.",
        "Generate a motivational quote like a Nobel winner.",
        "Draft a letter as if you were a Nobel laureate.",
        "Rewrite this in the style of a laureate."
    ]
    for q in queries:
        assert classifier.classify(q) == "generative"

def test_precedence_generative_over_thematic(classifier):
    """Test that generative keywords take precedence over thematic."""
    query = "Write a speech about common themes in Nobel lectures."
    assert classifier.classify(query) == "generative"

def test_precedence_generative_over_factual(classifier):
    """Test that generative keywords take precedence over factual."""
    query = "Compose a summary of what Toni Morrison said about justice."
    assert classifier.classify(query) == "generative"

def test_precedence_thematic_over_factual(classifier):
    """Test that thematic keywords take precedence over factual."""
    query = "What are common themes in Toni Morrison's speeches?"
    assert classifier.classify(query) == "thematic"

def test_fallback_to_factual(classifier):
    """Test that queries with no keywords default to factual."""
    queries = [
        "Tell me about the Nobel Prize.",
        "Information on laureates.",
        "Details about the ceremony."
    ]
    for q in queries:
        assert classifier.classify(q) == "factual"

def test_case_insensitivity(classifier):
    """Test that classification is case-insensitive."""
    query = "WRITE ME a summary of themes in Nobel lectures."
    assert classifier.classify(query) == "generative"

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