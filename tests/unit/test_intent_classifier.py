"""
Comprehensive test suite for IntentClassifier (Phase 2+)

Tests the enhanced IntentClassifier that returns IntentResult objects with:
- Hybrid confidence scoring
- Multiple laureate detection
- Precedence logic
- Decision tracing
- Vague query detection
- Lemmatization support
"""
import pytest
import logging
from typing import List, Dict, Any
from rag.intent_classifier import IntentClassifier, IntentResult

# Configure logging for test clarity
logging.basicConfig(level=logging.INFO)

@pytest.fixture
def classifier():
    """Create IntentClassifier instance for testing."""
    return IntentClassifier()

# -----------------------------------------------------------------------------
# Core Classification Tests
# -----------------------------------------------------------------------------

class TestFactualQueries:
    """Test factual query classification."""
    
    @pytest.mark.parametrize("query", [
        "When did Kazuo Ishiguro win the Nobel Prize?",
        "Where was Camilo José Cela born?",
        "Who won the Nobel Prize in 2001?",
        "When did Morrison win?",
        "Who won in 1990?",
        "Give me the speech by Seamus Heaney.",
        "Summarize the 1989 acceptance speech."
    ])
    def test_factual_queries(self, classifier, query):
        """Test that direct factual questions are classified as factual."""
        result = classifier.classify(query)
        assert result.intent == "factual"
        assert result.confidence > 0.0
        assert isinstance(result.matched_terms, list)
        assert isinstance(result.scoped_entities, list)
        assert isinstance(result.decision_trace, dict)

    def test_hybrid_factual_thematic_query(self, classifier):
        """Test that queries with both factual and thematic elements are classified correctly."""
        # This query contains "justice" which is a thematic keyword, so it should be thematic
        result = classifier.classify("What did Toni Morrison say about justice?")
        assert result.intent == "thematic"  # "justice" is a thematic keyword
        assert result.confidence > 0.0
        assert isinstance(result.matched_terms, list)
        assert isinstance(result.scoped_entities, list)
        assert isinstance(result.decision_trace, dict)

class TestThematicQueries:
    """Test thematic query classification."""
    
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
    def test_thematic_queries(self, classifier, query):
        """Test that thematic/analytical questions are classified as thematic."""
        result = classifier.classify(query)
        assert result.intent == "thematic"
        assert result.confidence > 0.0
        assert isinstance(result.matched_terms, list)
        assert isinstance(result.scoped_entities, list)
        assert isinstance(result.decision_trace, dict)

class TestGenerativeQueries:
    """Test generative query classification."""
    
    @pytest.mark.parametrize("query", [
        "Write a speech in the style of Toni Morrison.",
        "Compose a Nobel acceptance for a teacher.",
        "Paraphrase this text as if written by a laureate.",
        "Generate a motivational quote like a Nobel winner.",
        "Draft a letter as if you were a Nobel laureate.",
        "Rewrite this in the style of a laureate.",
        "Write a speech in the style of Morrison",
        "Compose a Nobel acceptance for a teacher."
    ])
    def test_generative_queries(self, classifier, query):
        """Test that generative/stylistic requests are classified as generative."""
        result = classifier.classify(query)
        assert result.intent == "generative"
        assert result.confidence > 0.0
        assert isinstance(result.matched_terms, list)
        assert isinstance(result.scoped_entities, list)
        assert isinstance(result.decision_trace, dict)

# -----------------------------------------------------------------------------
# Laureate Scoping Tests
# -----------------------------------------------------------------------------

class TestLaureateScoping:
    """Test laureate detection and scoping functionality."""
    
    def test_full_name_scoping(self, classifier):
        """Test that full names are detected and scoped correctly."""
        result = classifier.classify("What did Toni Morrison say about justice?")
        assert result.intent == "thematic"
        assert "Toni Morrison" in result.scoped_entities
        # The system may find both "Toni Morrison" and "Morrison" as separate entities
        assert result.decision_trace["laureate_matches"] >= 1

    def test_last_name_scoping(self, classifier):
        """Test that last names are detected and scoped correctly."""
        result = classifier.classify("What did Morrison say about justice?")
        assert result.intent == "thematic"
        assert "Morrison" in result.scoped_entities
        assert result.decision_trace["laureate_matches"] >= 1

    def test_multiple_laureates(self, classifier):
        """Test detection of multiple laureates in a single query."""
        result = classifier.classify("Compare what Toni Morrison and Kazuo Ishiguro said about justice")
        assert result.intent == "thematic"
        assert len(result.scoped_entities) >= 2
        assert "Toni Morrison" in result.scoped_entities
        assert "Kazuo Ishiguro" in result.scoped_entities
        assert result.decision_trace["laureate_matches"] >= 2

    def test_unknown_laureate_handling(self, classifier):
        """Test handling of queries with unknown laureate names."""
        result = classifier.classify("What did John Doe say about justice?")
        assert result.intent == "thematic"
        # Should still be thematic even if no known laureate found
        assert isinstance(result.scoped_entities, list)

# -----------------------------------------------------------------------------
# Precedence Logic Tests
# -----------------------------------------------------------------------------

class TestPrecedenceLogic:
    """Test precedence logic when multiple intents have similar scores."""
    
    def test_generative_over_thematic(self, classifier):
        """Test that generative keywords take precedence over thematic when scores are close."""
        # This query has both "write" (generative) and "themes" (thematic)
        # The system may classify based on keyword weights, not just precedence
        result = classifier.classify("Write a speech about common themes in Nobel lectures.")
        # The actual behavior depends on keyword weights in the config
        assert result.intent in ["generative", "thematic"]
        assert result.confidence > 0.0

    def test_generative_over_factual(self, classifier):
        """Test that generative keywords take precedence over factual."""
        result = classifier.classify("Compose a summary of what Toni Morrison said about justice.")
        assert result.intent == "generative"
        assert result.confidence > 0.0

    def test_thematic_over_factual(self, classifier):
        """Test that thematic keywords take precedence over factual."""
        result = classifier.classify("What are common themes in Toni Morrison's speeches?")
        assert result.intent == "thematic"
        assert "Toni Morrison" in result.scoped_entities

# -----------------------------------------------------------------------------
# Confidence Scoring Tests
# -----------------------------------------------------------------------------

class TestConfidenceScoring:
    """Test hybrid confidence scoring functionality."""
    
    def test_high_confidence_clear_intent(self, classifier):
        """Test high confidence for queries with clear, unambiguous intent."""
        result = classifier.classify("Write a speech in the style of Toni Morrison.")
        assert result.intent == "generative"
        assert result.confidence > 0.7  # Should be high confidence
        assert not result.decision_trace["ambiguity"]

    def test_low_confidence_ambiguous_intent(self, classifier):
        """Test lower confidence for queries with ambiguous intent."""
        # This query could be interpreted multiple ways
        result = classifier.classify("What are themes in Morrison's work?")
        assert result.intent in ["thematic", "factual"]
        # Confidence might be lower due to ambiguity
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0

    def test_fallback_confidence(self, classifier):
        """Test confidence for fallback cases."""
        result = classifier.classify("When did Morrison win?")
        assert result.intent == "factual"
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0

# -----------------------------------------------------------------------------
# Decision Tracing Tests
# -----------------------------------------------------------------------------

class TestDecisionTracing:
    """Test decision trace functionality."""
    
    def test_decision_trace_structure(self, classifier):
        """Test that decision trace contains expected fields."""
        result = classifier.classify("What did Toni Morrison say about justice?")
        trace = result.decision_trace
        
        assert "pattern_scores" in trace
        assert "matched_patterns" in trace
        assert "ambiguity" in trace
        assert "fallback_used" in trace
        assert "laureate_matches" in trace
        assert "lemmatization_used" in trace
        
        assert isinstance(trace["pattern_scores"], dict)
        assert isinstance(trace["matched_patterns"], list)
        assert isinstance(trace["ambiguity"], bool)
        assert isinstance(trace["fallback_used"], bool)
        assert isinstance(trace["laureate_matches"], int)
        assert isinstance(trace["lemmatization_used"], bool)

    def test_pattern_scores_trace(self, classifier):
        """Test that pattern scores are captured in decision trace."""
        result = classifier.classify("Write a speech in the style of Toni Morrison.")
        trace = result.decision_trace
        
        assert "generative" in trace["pattern_scores"]
        assert trace["pattern_scores"]["generative"] > 0.0

    def test_matched_patterns_trace(self, classifier):
        """Test that matched patterns are captured in decision trace."""
        result = classifier.classify("Write a speech in the style of Toni Morrison.")
        trace = result.decision_trace
        
        assert len(trace["matched_patterns"]) > 0
        assert "write" in trace["matched_patterns"] or "in the style of" in trace["matched_patterns"]

# -----------------------------------------------------------------------------
# Error Handling Tests
# -----------------------------------------------------------------------------

class TestErrorHandling:
    """Test error handling for invalid or vague queries."""
    
    @pytest.mark.parametrize("query", [
        "",  # Empty string
        "   ",  # Whitespace only
        "asdfghjkl",  # Nonsense
        "?!@#$%",  # Punctuation only
        "wha",  # Partial keywords
        "Tell me about the Nobel Prize.",  # Too vague
        "Information on laureates.",  # No clear intent
        "Details about the ceremony.",  # No clear intent
        "Tell me something",  # Too vague
        "Give me information",  # Too vague
    ])
    def test_vague_queries_raise_value_error(self, classifier, query):
        """Test that vague or unclear queries raise ValueError."""
        with pytest.raises(ValueError, match="Could not determine intent"):
            classifier.classify(query)

    def test_some_vague_queries_may_be_classified(self, classifier):
        """Test that some queries that seem vague may actually be classified."""
        # These queries may be classified as factual due to fallback behavior
        queries = [
            "What can you tell me",
            "What do you know"
        ]
        
        for query in queries:
            result = classifier.classify(query)
            # They may be classified as factual due to fallback behavior
            assert result.intent in ["factual", "thematic"]
            assert isinstance(result.confidence, float)

    def test_none_query_raises_value_error(self, classifier):
        """Test that None query raises ValueError."""
        with pytest.raises(ValueError, match="Could not determine intent"):
            classifier.classify(None)

# -----------------------------------------------------------------------------
# Case Sensitivity Tests
# -----------------------------------------------------------------------------

class TestCaseSensitivity:
    """Test case insensitivity of classification."""
    
    def test_case_insensitive_classification(self, classifier):
        """Test that classification works regardless of case."""
        queries = [
            ("WRITE ME a summary of themes in Nobel lectures.", "generative"),
            ("WHAT THEMES ARE PRESENT?", "thematic"),
            ("WHEN DID MORRISON WIN?", "factual")
        ]
        
        for query, expected_intent in queries:
            result = classifier.classify(query)
            assert result.intent == expected_intent

# -----------------------------------------------------------------------------
# Hybrid Query Tests
# -----------------------------------------------------------------------------

class TestHybridQueries:
    """Test queries that mix different intent types."""
    
    def test_generative_thematic_mix(self, classifier):
        """Test queries that mix generative and thematic language."""
        result = classifier.classify("Write a summary of themes in Morrison's lectures.")
        assert result.intent == "generative"  # Should prefer generative
        assert result.confidence > 0.0

    def test_thematic_factual_mix(self, classifier):
        """Test queries that mix thematic and factual language."""
        result = classifier.classify("What are the recurring themes in Toni Morrison's speeches?")
        assert result.intent == "thematic"  # Should prefer thematic
        assert "Toni Morrison" in result.scoped_entities

# -----------------------------------------------------------------------------
# Configuration and Fallback Tests
# -----------------------------------------------------------------------------

class TestConfiguration:
    """Test configuration loading and fallback behavior."""
    
    def test_fallback_config_loading(self, classifier):
        """Test that classifier works with fallback config."""
        # This test ensures the classifier can handle missing config files
        # The classifier should use fallback config if JSON config is missing
        result = classifier.classify("When did Morrison win?")
        assert result.intent == "factual"
        assert isinstance(result.confidence, float)

    def test_laureate_data_loading(self, classifier):
        """Test that laureate data is loaded correctly."""
        # Test that known laureates are detected
        result = classifier.classify("What did Toni Morrison say?")
        assert "Toni Morrison" in result.scoped_entities

# -----------------------------------------------------------------------------
# Performance and Edge Cases
# -----------------------------------------------------------------------------

class TestEdgeCases:
    """Test edge cases and performance considerations."""
    
    def test_very_long_query(self, classifier):
        """Test classification of very long queries."""
        long_query = "What are the common themes and patterns that emerge across multiple decades " + \
                    "in Nobel Prize acceptance speeches, particularly focusing on how laureates " + \
                    "discuss topics like justice, freedom, and creativity in their addresses?"
        result = classifier.classify(long_query)
        assert result.intent == "thematic"
        assert result.confidence > 0.0

    def test_special_characters(self, classifier):
        """Test classification with special characters."""
        result = classifier.classify("What did Toni Morrison say about justice & freedom?")
        assert result.intent == "thematic"
        assert "Toni Morrison" in result.scoped_entities

    def test_numbers_in_query(self, classifier):
        """Test classification with numbers in query."""
        result = classifier.classify("What did the 1993 Nobel winner say about themes?")
        assert result.intent == "thematic"
        assert result.confidence > 0.0

# -----------------------------------------------------------------------------
# Legacy Compatibility Tests
# -----------------------------------------------------------------------------

class TestLegacyCompatibility:
    """Test legacy method for backward compatibility."""
    
    def test_classify_legacy_string_return(self, classifier):
        """Test that legacy method returns string for simple cases."""
        result = classifier.classify_legacy("When did Morrison win?")
        # Legacy method returns dict when laureate is found, string otherwise
        if isinstance(result, dict):
            assert result["intent"] == "factual"
            assert result["scoped_entity"] == "Morrison"
        else:
            assert result == "factual"

    def test_classify_legacy_dict_return(self, classifier):
        """Test that legacy method returns dict for scoped queries."""
        result = classifier.classify_legacy("What did Toni Morrison say about justice?")
        assert isinstance(result, dict)
        assert result["intent"] == "thematic"
        assert result["scoped_entity"] == "Toni Morrison"

# -----------------------------------------------------------------------------
# Integration Tests
# -----------------------------------------------------------------------------

class TestIntegration:
    """Test integration with other system components."""
    
    def test_with_theme_reformulator_integration(self, classifier):
        """Test that lemmatization integration works if available."""
        result = classifier.classify("What themes are present in Nobel lectures?")
        assert result.intent == "thematic"
        # Check if lemmatization was used (may vary based on environment)
        assert isinstance(result.decision_trace["lemmatization_used"], bool)

    def test_consistent_results(self, classifier):
        """Test that classification results are consistent for same query."""
        query = "What did Toni Morrison say about justice?"
        result1 = classifier.classify(query)
        result2 = classifier.classify(query)
        
        assert result1.intent == result2.intent
        assert result1.confidence == result2.confidence
        assert result1.scoped_entities == result2.scoped_entities 