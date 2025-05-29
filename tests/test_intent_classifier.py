import pytest
from rag.intent_classifier import IntentClassifier

def is_thematic(result, expected_scoped=None):
    if isinstance(result, dict):
        if result["intent"] != "thematic":
            return False
        if expected_scoped is not None:
            return result["scoped_entity"] == expected_scoped
        return True
    return result == "thematic"

def is_factual(result):
    return result == "factual"

def is_generative(result):
    return result == "generative"

@pytest.fixture
def classifier():
    return IntentClassifier()

def test_factual_query(classifier):
    """Test that a direct factual question is classified as factual."""
    queries = [
        "When did Kazuo Ishiguro win the Nobel Prize?",
        "Where was Camilo José Cela born?",
        "Summarize the 1989 acceptance speech.",
        "Who won the Nobel Prize in 2001?",
        "Give me the speech by Seamus Heaney."
    ]
    for q in queries:
        assert is_factual(classifier.classify(q))
    # The following query is now thematic+scoped
    result = classifier.classify("What did Toni Morrison say about justice?")
    assert is_thematic(result, expected_scoped="Toni Morrison")

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
        assert is_thematic(classifier.classify(q))

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
        assert is_generative(classifier.classify(q))

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

def test_fallback_to_factual(classifier):
    """Test that queries with no keywords default to factual."""
    queries = [
        "Tell me about the Nobel Prize.",
        "Information on laureates.",
        "Details about the ceremony."
    ]
    for q in queries:
        assert is_factual(classifier.classify(q))

def test_case_insensitivity(classifier):
    """Test that classification is case-insensitive."""
    query = "WRITE ME a summary of themes in Nobel lectures."
    assert is_generative(classifier.classify(query))

def test_intent_classifier_factual():
    """
    Test that factual queries are classified as 'factual'.
    """
    clf = IntentClassifier()
    assert is_factual(clf.classify("When did Morrison win?"))
    assert is_factual(clf.classify("Who won in 1990?"))
    assert is_factual(clf.classify("Where was Camilo José Cela born?"))
    assert is_factual(clf.classify("Summarize the 1989 acceptance speech."))

def test_intent_classifier_thematic():
    """
    Test that thematic queries are classified as 'thematic'.
    """
    clf = IntentClassifier()
    assert is_thematic(clf.classify("What themes are present in Nobel lectures?"))
    assert is_thematic(clf.classify("How do laureates talk about justice?"))
    assert is_thematic(clf.classify("Compare motifs across laureates."))
    # This is now scoped to Morrison
    result = clf.classify("What does Morrison say about freedom?")
    assert is_thematic(result, expected_scoped="Morrison")

def test_intent_classifier_generative():
    """
    Test that generative queries are classified as 'generative'.
    """
    clf = IntentClassifier()
    assert is_generative(clf.classify("Write a speech in the style of Morrison"))
    assert is_generative(clf.classify("Compose a Nobel acceptance for a teacher."))
    assert is_generative(clf.classify("Paraphrase this text as if written by a laureate."))

def test_intent_classifier_precedence():
    """
    Test that generative > thematic > factual precedence is respected.
    """
    clf = IntentClassifier()
    assert is_generative(clf.classify("Write a thematic analysis of Nobel lectures"))
    # This is now scoped to Morrison
    result = clf.classify("What does Morrison say about justice?")
    assert is_thematic(result, expected_scoped="Morrison")

def test_intent_classifier_case_insensitivity():
    """
    Test that classification is case-insensitive.
    """
    clf = IntentClassifier()
    assert is_thematic(clf.classify("WHAT THEMES ARE PRESENT?"))
    assert is_generative(clf.classify("write a speech in the style of morrison"))
    assert is_factual(clf.classify("WHEN DID MORRISON WIN?"))

def test_intent_classifier_fallback():
    """
    Test that queries with no keywords fall back to 'factual'.
    """
    clf = IntentClassifier()
    assert is_factual(clf.classify("Tell me something interesting."))

def test_thematic_query_with_last_name_scoping():
    clf = IntentClassifier()
    result = clf.classify("What did Morrison say about justice?")
    assert is_thematic(result, expected_scoped="Morrison") 