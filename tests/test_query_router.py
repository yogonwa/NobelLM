import pytest
from rag.query_router import IntentClassifier

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