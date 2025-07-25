"""
Unit tests for intent_utils module.

Tests the flexible subject+verb matching functionality for thematic synthesis detection.
"""

import pytest
from rag.intent_utils import matches_synthesis_frame, SUBJECT_ALIASES, VERB_CUES


@pytest.mark.unit
class TestIntentUtils:
    """Test the intent_utils module functionality."""
    
    def test_subject_aliases_defined(self):
        """Test that SUBJECT_ALIASES contains expected values."""
        expected_subjects = [
            "laureates", "winners", "recipients", "authors", 
            "they", "these voices", "nobelists"
        ]
        
        assert len(SUBJECT_ALIASES) == len(expected_subjects)
        for subject in expected_subjects:
            assert subject in SUBJECT_ALIASES
    
    def test_verb_cues_defined(self):
        """Test that VERB_CUES contains expected values."""
        expected_verbs = [
            "think", "feel", "say", "reflect", "talk about", 
            "treat", "explore", "approach", "address"
        ]
        
        assert len(VERB_CUES) == len(expected_verbs)
        for verb in expected_verbs:
            assert verb in VERB_CUES
    
    def test_matches_synthesis_frame_positive_cases(self):
        """Test that synthesis frame matching works for various combinations."""
        positive_queries = [
            "how do winners think about freedom",
            "what do laureates say about justice",
            "how have they reflected on memory",
            "what do recipients feel about peace",
            "how do authors talk about creativity",
            "what do these voices explore regarding identity",
            "how do nobelists approach the theme of love",
            "what do laureates treat when discussing war",
            "how do winners address the topic of hope"
        ]
        
        for query in positive_queries:
            assert matches_synthesis_frame(query), f"Should match: {query}"
    
    def test_matches_synthesis_frame_negative_cases(self):
        """Test that synthesis frame matching correctly rejects non-synthesis queries."""
        negative_queries = [
            "list speeches that discuss democracy",
            "compare early vs modern views",
            "what is the context for hope",
            "show me examples of justice",
            "find speeches about peace",
            "which laureates won in 1990",
            "when did Morrison win the prize",
            "give me the speech by Heaney",
            "summarize the 1989 acceptance speech"
        ]
        
        for query in negative_queries:
            assert not matches_synthesis_frame(query), f"Should not match: {query}"
    
    def test_matches_synthesis_frame_case_insensitive(self):
        """Test that synthesis frame matching is case insensitive."""
        mixed_case_queries = [
            "How Do Winners Think About Freedom",
            "WHAT DO LAUREATES SAY ABOUT JUSTICE",
            "how have They reflected on memory",
            "What Do Recipients Feel About Peace"
        ]
        
        for query in mixed_case_queries:
            assert matches_synthesis_frame(query.lower()), f"Should match: {query}"
    
    def test_matches_synthesis_frame_edge_cases(self):
        """Test edge cases for synthesis frame matching."""
        edge_cases = [
            "how do winners think about",  # Exact match
            "what do laureates say about",  # Exact match
            "how do they think about freedom and justice",  # Multiple themes
            "what do winners say about freedom, justice, and peace",  # Multiple themes
            "how do laureates think about freedom but not justice",  # Complex sentence
        ]
        
        for query in edge_cases:
            assert matches_synthesis_frame(query), f"Should match: {query}"
    
    def test_matches_synthesis_frame_partial_matches(self):
        """Test that partial matches are correctly rejected."""
        # The function matches any subject+verb combination, so these should NOT match
        non_matching_queries = [
            "how do winners about freedom",  # Missing verb
            "what do laureates about justice",  # Missing verb
            "how winners about freedom",  # Missing verb and "do"
            "what laureates about justice",  # Missing verb and "do"
            "how do about freedom",  # Missing subject and verb
            "what do about justice",  # Missing subject and verb
        ]
        
        for query in non_matching_queries:
            assert not matches_synthesis_frame(query), f"Should not match: {query}"
    
    def test_matches_synthesis_frame_empty_and_whitespace(self):
        """Test handling of empty strings and whitespace."""
        empty_cases = [
            "",
            "   ",
            "\n\t",
            "how do winners think about",  # Ends with space
            " what do laureates say about justice",  # Starts with space
        ]
        
        # Empty strings should not match
        assert not matches_synthesis_frame("")
        assert not matches_synthesis_frame("   ")
        assert not matches_synthesis_frame("\n\t")
        
        # Valid queries with whitespace should still match
        assert matches_synthesis_frame(" how do winners think about freedom")
        assert matches_synthesis_frame("what do laureates say about justice ")
    
    def test_matches_synthesis_frame_special_characters(self):
        """Test handling of special characters in queries."""
        special_char_queries = [
            "how do winners think about freedom?",
            "what do laureates say about justice!",
            "how have they reflected on memory...",
            "what do recipients feel about peace?",
            "how do authors talk about creativity?!",
        ]
        
        for query in special_char_queries:
            # Remove punctuation for matching
            clean_query = query.replace("?", "").replace("!", "").replace(".", "")
            assert matches_synthesis_frame(clean_query), f"Should match: {clean_query}"
    
    def test_matches_synthesis_frame_performance(self):
        """Test that synthesis frame matching is reasonably fast."""
        import time
        
        test_query = "how do winners think about freedom"
        iterations = 1000
        
        start_time = time.time()
        for _ in range(iterations):
            matches_synthesis_frame(test_query)
        end_time = time.time()
        
        # Should complete 1000 iterations in under 1 second
        assert (end_time - start_time) < 1.0, f"Performance test failed: {(end_time - start_time):.3f}s"
    
    def test_matches_synthesis_frame_all_combinations(self):
        """Test that all subject-verb combinations work correctly."""
        for subject in SUBJECT_ALIASES:
            for verb in VERB_CUES:
                query = f"how do {subject} {verb} about freedom"
                assert matches_synthesis_frame(query), f"Should match: {query}"
                
                # Test with "what do" pattern
                query = f"what do {subject} {verb} about justice"
                assert matches_synthesis_frame(query), f"Should match: {query}" 