import pytest
from rag.intent_classifier import IntentClassifier
from tests.test_utils_intent import is_factual, is_thematic, is_generative

@pytest.fixture
def classifier():
    return IntentClassifier()

@pytest.mark.parametrize("query", [
    "When did Kazuo Ishiguro win the Nobel Prize?",
    "Where was Camilo José Cela born?",
    "Summarize the 1989 acceptance speech.",
    "Who won the Nobel Prize in 2001?",
    "Give me the speech by Seamus Heaney.",
    "When did Morrison win?",
    "Who won in 1990?",
    "What years did Americans win the prize?"
])
def test_factual_queries(classifier, query):
    """Test that direct factual questions are classified as factual."""
    assert is_factual(classifier.classify(query))

@pytest.mark.parametrize("query", [
    "What are common themes in Nobel lectures?",
    "How have topics changed over time?",
    "Compare speeches from U.S. vs. European laureates.",
    "What motifs are recurring across decades?",
    "What patterns emerge in acceptance speeches?",
    "Are there typical themes in Peace Prize lectures?",
    "What themes are present in Nobel lectures?",
    "How do laureates talk about justice?",
    "Compare motifs across laureates."
])
def test_thematic_queries(classifier, query):
    """Test that thematic/analytical questions are classified as thematic."""
    assert is_thematic(classifier.classify(query))

@pytest.mark.parametrize("query", [
    "Write a speech in the style of Toni Morrison.",
    "Compose a Nobel acceptance for a teacher.",
    "Paraphrase this text as if written by a laureate.",
    "Generate a motivational quote like a Nobel winner.",
    "Draft a letter as if you were a Nobel laureate.",
    "Rewrite this in the style of a laureate.",
    "Write a speech in the style of Morrison",
    "Compose a Nobel acceptance for a teacher.",
    "Paraphrase this text as if written by a laureate."
])
def test_generative_queries(classifier, query):
    """Test that generative/stylistic requests are classified as generative."""
    assert is_generative(classifier.classify(query))

def test_thematic_scoping_full_vs_last_name(classifier):
    """Test that scoping works consistently for both full names and last names."""
    result_full = classifier.classify("What did Toni Morrison say about justice?")
    assert is_thematic(result_full, expected_scoped="Toni Morrison")

    result_last = classifier.classify("What did Morrison say about justice?")
    assert is_thematic(result_last, expected_scoped="Morrison")

def test_thematic_unknown_laureate_scoping(classifier):
    """Test handling of thematic queries with unknown laureate names."""
    result = classifier.classify("What did John Doe say about justice?")
    assert is_thematic(result)  # Should still be thematic, scoped entity may vary

def test_precedence_generative_over_thematic(classifier):
    """Test that generative keywords take precedence over thematic."""
    query = "Write a speech about common themes in Nobel lectures."
    assert is_generative(classifier.classify(query))

def test_precedence_generative_over_factual(classifier):
    """Test that generative keywords take precedence over factual."""
    query = "Compose a summary of what Toni Morrison said about justice."
    assert is_generative(classifier.classify(query))

def test_precedence_thematic_over_factual(classifier):
    """Test that thematic keywords take precedence over factual."""
    query = "What are common themes in Toni Morrison's speeches?"
    result = classifier.classify(query)
    assert is_thematic(result, expected_scoped="Toni Morrison")

def test_case_insensitivity(classifier):
    """Test that classification is case-insensitive."""
    queries = [
        ("WRITE ME a summary of themes in Nobel lectures.", is_generative),
        ("WHAT THEMES ARE PRESENT?", is_thematic),
        ("WHEN DID MORRISON WIN?", is_factual)
    ]
    for query, check_func in queries:
        assert check_func(classifier.classify(query))

def test_unknown_intent_raises_value_error(classifier):
    """Test that queries with no clear intent raise ValueError."""
    unknown_queries = [
        "Tell me about the Nobel Prize.",  # Too vague
        "Information on laureates.",       # No clear intent
        "Details about the ceremony.",     # No clear intent
        "",                               # Empty string
        "   ",                            # Whitespace only
        "asdfghjkl",                      # Nonsense
        "?!@#$%",                         # Punctuation only
        "wha"                             # Partial keywords
    ]
    for query in unknown_queries:
        with pytest.raises(ValueError, match="Could not determine intent"):
            classifier.classify(query)

def test_hybrid_phrasing_intent(classifier):
    """Test queries that mix factual and thematic/generative language."""
    # Should prefer generative over thematic/factual
    assert is_generative(classifier.classify("Write a summary of themes in Morrison's lectures."))
    # Should prefer thematic over factual
    result = classifier.classify("What are the recurring themes in Toni Morrison's speeches?")
    assert is_thematic(result, expected_scoped="Toni Morrison")
    # Should raise ValueError for unclear intent
    with pytest.raises(ValueError, match="Could not determine intent"):
        classifier.classify("Tell me something about the prize ceremony")  # Too vague, no clear intent

