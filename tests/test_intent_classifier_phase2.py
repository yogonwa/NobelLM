"""
Tests for Phase 2 IntentClassifier with hybrid confidence scoring, lemmatization, and multiple laureate support.
"""
import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from rag.intent_classifier import IntentClassifier, IntentResult


class TestIntentClassifierPhase2:
    """Test the new Phase 2 IntentClassifier features."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing."""
        config = {
            "intents": {
                "factual": {
                    "keywords": {"what": 0.3, "when": 0.4, "who": 0.4, "quote": 0.9},
                    "phrases": {"who won": 0.8}
                },
                "thematic": {
                    "keywords": {"theme": 0.6, "compare": 0.7, "patterns": 0.8},
                    "phrases": {"what are": 0.5}
                },
                "generative": {
                    "keywords": {"write": 0.8, "compose": 0.9},
                    "phrases": {"in the style of": 0.95}
                }
            },
            "settings": {
                "min_confidence": 0.3,
                "ambiguity_threshold": 0.2,
                "fallback_intent": "factual",
                "max_laureate_matches": 3,
                "use_lemmatization": False,
                "lemmatization_fallback": True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        os.unlink(temp_path)
    
    @pytest.fixture
    def temp_laureate_file(self):
        """Create a temporary laureate data file for testing."""
        data = [
            {
                "year": 1993,
                "laureates": [
                    {"full_name": "Toni Morrison"}
                ]
            },
            {
                "year": 1982,
                "laureates": [
                    {"full_name": "Gabriel García Márquez"}
                ]
            },
            {
                "year": 2016,
                "laureates": [
                    {"full_name": "Bob Dylan"}
                ]
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        os.unlink(temp_path)
    
    def test_intent_result_structure(self, temp_config_file, temp_laureate_file):
        """Test that IntentResult has the correct structure."""
        classifier = IntentClassifier(
            laureate_names_path=temp_laureate_file,
            config_path=temp_config_file
        )
        
        result = classifier.classify("What are the main themes?")
        
        assert isinstance(result, IntentResult)
        assert hasattr(result, 'intent')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'matched_terms')
        assert hasattr(result, 'scoped_entities')
        assert hasattr(result, 'decision_trace')
        
        assert isinstance(result.intent, str)
        assert isinstance(result.confidence, float)
        assert isinstance(result.matched_terms, list)
        assert isinstance(result.scoped_entities, list)
        assert isinstance(result.decision_trace, dict)
    
    def test_hybrid_confidence_scoring(self, temp_config_file, temp_laureate_file):
        """Test hybrid confidence scoring with pattern strength and ambiguity penalty."""
        classifier = IntentClassifier(
            laureate_names_path=temp_laureate_file,
            config_path=temp_config_file
        )
        
        # Clear thematic query
        result = classifier.classify("Compare the themes of hope")
        assert result.intent == "thematic"
        assert result.confidence > 0.7  # Should be high confidence
        
        # Ambiguous query (could be factual or thematic)
        result = classifier.classify("What are themes")
        assert result.intent in ["factual", "thematic"]
        assert result.confidence < 0.8  # Should be lower due to ambiguity
    
    def test_matched_terms_reporting(self, temp_config_file, temp_laureate_file):
        """Test that matched terms are correctly reported."""
        classifier = IntentClassifier(
            laureate_names_path=temp_laureate_file,
            config_path=temp_config_file
        )
        
        result = classifier.classify("Compare the themes of hope")
        
        assert "compare" in result.matched_terms
        assert "theme" in result.matched_terms
        assert len(result.matched_terms) >= 2
    
    def test_multiple_laureate_detection(self, temp_config_file, temp_laureate_file):
        """Test detection of multiple laureates in a query."""
        classifier = IntentClassifier(
            laureate_names_path=temp_laureate_file,
            config_path=temp_config_file
        )
        
        result = classifier.classify("Compare Toni Morrison and Gabriel García Márquez")
        
        # Should find at least the two full names
        assert len(result.scoped_entities) >= 2
        assert "Toni Morrison" in result.scoped_entities
        assert "Gabriel García Márquez" in result.scoped_entities
        
        # May also find last names, which is fine
        # The important thing is that we find the full names
    
    def test_decision_trace_logging(self, temp_config_file, temp_laureate_file):
        """Test that decision trace is properly logged."""
        classifier = IntentClassifier(
            laureate_names_path=temp_laureate_file,
            config_path=temp_config_file
        )
        
        result = classifier.classify("What are the themes?")
        
        assert "pattern_scores" in result.decision_trace
        assert "matched_patterns" in result.decision_trace
        assert "ambiguity" in result.decision_trace
        assert "fallback_used" in result.decision_trace
        assert "laureate_matches" in result.decision_trace
        assert "lemmatization_used" in result.decision_trace
    
    def test_fallback_on_no_match(self, temp_config_file, temp_laureate_file):
        """Test fallback when no patterns match."""
        classifier = IntentClassifier(
            laureate_names_path=temp_laureate_file,
            config_path=temp_config_file
        )
        
        # Query with no clear intent patterns
        result = classifier.classify("xyzabc123")
        
        assert result.intent == "factual"  # Should use fallback
        assert result.confidence == 0.1  # Low confidence for fallback
        assert result.decision_trace["fallback_used"] is True
    
    def test_config_loading(self, temp_laureate_file):
        """Test loading configuration from JSON file."""
        # Test with valid config
        classifier = IntentClassifier(
            laureate_names_path=temp_laureate_file,
            config_path="data/intent_keywords.json"  # Use the real config
        )
        
        assert hasattr(classifier, 'config')
        assert "intents" in classifier.config
        assert "settings" in classifier.config
    
    def test_lemmatization_fallback(self, temp_config_file, temp_laureate_file):
        """Test lemmatization fallback when spaCy is not available."""
        with patch('config.theme_reformulator.ThemeReformulator') as mock_reformulator:
            mock_reformulator.side_effect = ImportError("spaCy not available")
            
            classifier = IntentClassifier(
                laureate_names_path=temp_laureate_file,
                config_path=temp_config_file
            )
            
            # Should still work without lemmatization
            result = classifier.classify("What are the themes?")
            assert result.intent == "thematic"
            assert result.decision_trace["lemmatization_used"] is False
    
    def test_ambiguity_penalty(self, temp_config_file, temp_laureate_file):
        """Test ambiguity penalty calculation."""
        classifier = IntentClassifier(
            laureate_names_path=temp_laureate_file,
            config_path=temp_config_file
        )
        
        # Test with clear winner
        scores = {"thematic": 1.0, "factual": 0.1}
        penalty = classifier.compute_ambiguity_penalty(scores)
        assert penalty == 0.0  # No ambiguity
        
        # Test with ambiguous scores
        scores = {"thematic": 0.6, "factual": 0.5}
        penalty = classifier.compute_ambiguity_penalty(scores)
        assert penalty > 0.0  # Some ambiguity
    
    def test_legacy_compatibility(self, temp_config_file, temp_laureate_file):
        """Test backward compatibility with legacy classify method."""
        classifier = IntentClassifier(
            laureate_names_path=temp_laureate_file,
            config_path=temp_config_file
        )
        
        # Test legacy method
        result = classifier.classify_legacy("What are the themes?")
        assert isinstance(result, str)
        assert result == "thematic"
        
        # Test with laureate
        result = classifier.classify_legacy("What did Toni Morrison say?")
        assert isinstance(result, dict)
        assert result["intent"] == "factual"
        assert result["scoped_entity"] == "Toni Morrison"
    
    def test_confidence_thresholds(self, temp_config_file, temp_laureate_file):
        """Test that confidence scores are within expected ranges."""
        classifier = IntentClassifier(
            laureate_names_path=temp_laureate_file,
            config_path=temp_config_file
        )
        
        # Test various queries
        queries = [
            "What are the themes?",
            "Compare Toni Morrison and Gabriel García Márquez",
            "Write a speech in the style of a laureate",
            "xyzabc123"  # No clear intent
        ]
        
        for query in queries:
            result = classifier.classify(query)
            assert 0.1 <= result.confidence <= 1.0
            assert result.intent in ["factual", "thematic", "generative"] 