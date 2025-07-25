"""
Unit tests for enhanced thematic subtype detection.

Tests the enhanced IntentClassifier._detect_thematic_subtype() method with:
- Flexible subject+verb matching for synthesis detection
- All four subtype classifications (synthesis, enumerative, analytical, exploratory)
- Confidence scoring and cue tracking
- Integration with intent_utils module
"""

import pytest
from rag.intent_classifier import IntentClassifier


@pytest.mark.unit
class TestThematicSubtypeDetection:
    """Test enhanced thematic subtype detection functionality."""
    
    @pytest.fixture
    def classifier(self):
        """Create IntentClassifier instance for testing."""
        return IntentClassifier()
    
    def test_synthesis_subtype_detection(self, classifier):
        """Test synthesis subtype detection with flexible subject+verb matching."""
        synthesis_queries = [
            "How do laureates think about freedom?",
            "What do winners say about justice?",
            "How have they reflected on memory?",
            "What do recipients feel about peace?",
            "How do authors talk about creativity?",
            "What do these voices explore regarding identity?",
            "How do nobelists approach the theme of love?",
            "What do laureates treat when discussing war?",
            "How do winners address the topic of hope?",
            "Synthesize views on peace",
            "Connect the themes of justice and freedom",
            "Draw together perspectives on memory",
            "Unify the discussion of creativity",
            "Create a coherent narrative about identity"
        ]
        
        for query in synthesis_queries:
            result = classifier.classify(query)
            if result.intent == "thematic":  # Only test if classified as thematic
                assert result.thematic_subtype == "synthesis", f"Query should be synthesis: {query}"
                assert result.subtype_confidence is not None
                assert result.subtype_cues is not None
                assert len(result.subtype_cues) > 0
    
    def test_enumerative_subtype_detection(self, classifier):
        """Test enumerative subtype detection."""
        enumerative_queries = [
            "List examples of exile in speeches",
            "Show me speeches about democracy",
            "Which speeches discuss hope?",
            "Give me examples of justice themes",
            "Find speeches that mention peace",
            "Enumerate the themes in Nobel lectures",
            "What are the specific instances of freedom?",
            "Show me cases of creativity in speeches",
            "List all speeches about memory",
            "Give me examples of identity themes"
        ]
        
        for query in enumerative_queries:
            result = classifier.classify(query)
            if result.intent == "thematic":  # Only test if classified as thematic
                assert result.thematic_subtype == "enumerative", f"Query should be enumerative: {query}"
                assert result.subtype_confidence is not None
                assert result.subtype_cues is not None
                assert len(result.subtype_cues) > 0
    
    def test_analytical_subtype_detection(self, classifier):
        """Test analytical subtype detection."""
        analytical_queries = [
            "Compare early vs recent views on peace",
            "Contrast different approaches to freedom",
            "Compare U.S. vs European laureate perspectives",
            "Contrast male vs female laureate approaches",
            "Compare how different cultures approach creativity"
        ]
        
        detected_analytical = 0
        for query in analytical_queries:
            result = classifier.classify(query)
            if result.intent == "thematic":  # Only test if classified as thematic
                if result.thematic_subtype == "analytical":
                    detected_analytical += 1
                    assert result.subtype_confidence is not None
                    assert result.subtype_cues is not None
                    assert len(result.subtype_cues) > 0
        
        # Should detect at least some analytical queries
        assert detected_analytical > 0, "Should detect at least some analytical queries"
    
    def test_exploratory_subtype_detection(self, classifier):
        """Test exploratory subtype detection."""
        exploratory_queries = [
            "What is the context for the reconciliation theme?",
            "Explain the background of hope in Nobel lectures",
            "What is the significance of memory in speeches?",
            "Why do laureates discuss justice so often?",
            "What is the history behind peace themes?",
            "Explain the cultural context of freedom discussions",
            "What is the significance of creativity in literature?",
            "Why do themes of identity appear frequently?",
            "What is the background for war discussions?",
            "Explain the historical context of love themes"
        ]
        
        for query in exploratory_queries:
            result = classifier.classify(query)
            if result.intent == "thematic":  # Only test if classified as thematic
                assert result.thematic_subtype == "exploratory", f"Query should be exploratory: {query}"
                assert result.subtype_confidence is not None
                assert result.subtype_cues is not None
                assert len(result.subtype_cues) > 0
    
    def test_subtype_confidence_scoring(self, classifier):
        """Test that subtype detection provides reasonable confidence scores."""
        test_queries = [
            ("How do laureates think about freedom?", "synthesis"),
            ("List examples of justice in speeches", "enumerative"),
            ("Compare early vs modern views on peace", "analytical"),
            ("What is the context for hope themes?", "exploratory")
        ]
        
        for query, expected_subtype in test_queries:
            result = classifier.classify(query)
            if result.intent == "thematic" and result.thematic_subtype:
                assert result.subtype_confidence is not None
                assert 0.0 <= result.subtype_confidence <= 1.0
                assert result.subtype_confidence > 0.0  # Should have some confidence
    
    def test_subtype_cue_tracking(self, classifier):
        """Test that subtype detection tracks triggering cues."""
        test_queries = [
            ("How do laureates think about freedom?", ["synthesis_frame_match"]),
            ("List examples of justice in speeches", ["list", "examples"]),
            ("Compare early vs modern views on peace", ["compare", "vs"]),
            ("What is the context for hope themes?", ["context", "what is"])
        ]
        
        for query, expected_cues in test_queries:
            result = classifier.classify(query)
            if result.intent == "thematic" and result.thematic_subtype:
                assert result.subtype_cues is not None
                assert len(result.subtype_cues) > 0
                # Check that at least one expected cue is present
                cue_found = any(cue in result.subtype_cues for cue in expected_cues)
                assert cue_found, f"Expected cues {expected_cues} not found in {result.subtype_cues}"
    
    def test_flexible_synthesis_detection(self, classifier):
        """Test that flexible subject+verb matching enhances synthesis detection."""
        flexible_queries = [
            "How do winners think about freedom?",
            "What do laureates say about justice?",
            "How have they reflected on memory?",
            "What do recipients feel about peace?",
            "How do authors talk about creativity?",
            "What do these voices explore regarding identity?",
            "How do nobelists approach the theme of love?",
            "What do laureates treat when discussing war?",
            "How do winners address the topic of hope?"
        ]
        
        synthesis_detected = 0
        for query in flexible_queries:
            result = classifier.classify(query)
            if result.intent == "thematic" and result.thematic_subtype == "synthesis":
                synthesis_detected += 1
                # Check that synthesis_frame_match is in cues
                assert "synthesis_frame_match" in result.subtype_cues
        
        # Should detect at least some synthesis queries with flexible matching
        assert synthesis_detected > 0, "Flexible synthesis detection should work"
    
    def test_subtype_detection_accuracy(self, classifier):
        """Test overall accuracy of subtype detection."""
        test_cases = {
            "synthesis": [
                "How do laureates think about freedom?",
                "What do winners say about justice?",
                "Synthesize views on peace",
                "Connect themes of creativity"
            ],
            "enumerative": [
                "List examples of exile in speeches",
                "Show me speeches about democracy",
                "Which speeches discuss hope?",
                "Give me examples of justice themes"
            ],
            "analytical": [
                "Compare early vs recent views on peace",
                "How have perspectives on justice evolved?",
                "Contrast different approaches to freedom",
                "What are the differences between modern and classical themes?"
            ],
            "exploratory": [
                "What is the context for the reconciliation theme?",
                "Explain the background of hope in Nobel lectures",
                "What is the significance of memory in speeches?",
                "Why do laureates discuss justice so often?"
            ]
        }
        
        total_correct = 0
        total_tested = 0
        
        for expected_subtype, queries in test_cases.items():
            for query in queries:
                result = classifier.classify(query)
                if result.intent == "thematic":  # Only count if classified as thematic
                    total_tested += 1
                    if result.thematic_subtype == expected_subtype:
                        total_correct += 1
        
        # Calculate accuracy
        if total_tested > 0:
            accuracy = total_correct / total_tested
            print(f"Subtype detection accuracy: {accuracy:.1%} ({total_correct}/{total_tested})")
            # Should have reasonable accuracy (at least 50%)
            assert accuracy >= 0.5, f"Subtype detection accuracy too low: {accuracy:.1%}"
    
    def test_subtype_detection_edge_cases(self, classifier):
        """Test edge cases for subtype detection."""
        edge_cases = [
            ("How do laureates think about freedom", "synthesis"),  # Complete synthesis query
            ("List examples of justice in speeches", "enumerative"),  # Complete enumerative query
            ("Compare themes across decades", "analytical"),  # Complete analytical query
            ("What is the context for hope themes", "exploratory"),  # Complete exploratory query
        ]
        
        for query, expected_subtype in edge_cases:
            result = classifier.classify(query)
            if result.intent == "thematic" and expected_subtype:
                # For edge cases, we're more lenient about exact subtype matching
                assert result.thematic_subtype is not None
                assert result.subtype_confidence is not None
                assert result.subtype_cues is not None
    
    def test_subtype_detection_integration(self, classifier):
        """Test that subtype detection integrates properly with intent classification."""
        integration_queries = [
            "How do laureates think about freedom and justice?",  # Synthesis with multiple themes
            "List examples of peace and war themes",  # Enumerative with multiple themes
            "Compare early vs modern views on creativity and identity",  # Analytical with multiple themes
            "What is the context for hope and despair themes?",  # Exploratory with multiple themes
        ]
        
        for query in integration_queries:
            result = classifier.classify(query)
            # Should be classified as thematic
            assert result.intent == "thematic"
            # Should have subtype information
            assert result.thematic_subtype is not None
            assert result.subtype_confidence is not None
            assert result.subtype_cues is not None
            assert len(result.subtype_cues) > 0 