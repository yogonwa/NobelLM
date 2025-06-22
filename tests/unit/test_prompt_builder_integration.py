"""
Unit tests for PromptBuilder integration with query engine.

Tests the integration of the new PromptBuilder with the query engine,
ensuring that intent-aware prompt building works correctly.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rag.prompt_builder import PromptBuilder
from rag.query_engine import get_prompt_builder, build_intent_aware_prompt


class TestPromptBuilderIntegration:
    """Test the integration of PromptBuilder with query engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock chunks with metadata
        self.mock_chunks = [
            {
                "text": "Language can never pin down slavery, genocide, war.",
                "score": 0.85,
                "metadata": {
                    "laureate": "Toni Morrison",
                    "year": "1993",
                    "speech_type": "lecture",
                    "category": "Literature"
                }
            },
            {
                "text": "The solitude of Latin America has a long history.",
                "score": 0.82,
                "metadata": {
                    "laureate": "Gabriel García Márquez",
                    "year": "1982",
                    "speech_type": "ceremony",
                    "category": "Literature"
                }
            }
        ]
    
    def test_get_prompt_builder_singleton(self):
        """Test that get_prompt_builder returns a singleton instance."""
        builder1 = get_prompt_builder()
        builder2 = get_prompt_builder()
        
        assert builder1 is builder2
        assert isinstance(builder1, PromptBuilder)
    
    def test_build_intent_aware_prompt_qa(self):
        """Test building QA prompts with intent awareness."""
        query = "What did Toni Morrison say about language?"
        
        prompt = build_intent_aware_prompt(
            query=query,
            chunks=self.mock_chunks,
            intent="qa"
        )
        
        # Should contain the query and formatted chunks
        assert query in prompt
        assert "Toni Morrison" in prompt
        assert "Gabriel García Márquez" in prompt
        assert "🎓" in prompt  # Lecture marker
        assert "🏅" in prompt  # Ceremony marker
    
    def test_build_intent_aware_prompt_generative_email(self):
        """Test building generative email prompts."""
        query = "Draft a job acceptance email in the style of a Nobel Prize winner"
        
        prompt = build_intent_aware_prompt(
            query=query,
            chunks=self.mock_chunks,
            intent="generative"
        )
        
        # Should contain generative template elements
        assert "You are a Nobel laureate" in prompt
        assert "email" in prompt.lower() or "accept" in query.lower()
        assert "humility" in prompt.lower() or "gratitude" in prompt.lower()
    
    def test_build_intent_aware_prompt_thematic(self):
        """Test building thematic prompts."""
        query = "How do Nobel laureates discuss creativity?"
        
        prompt = build_intent_aware_prompt(
            query=query,
            chunks=self.mock_chunks,
            intent="thematic"
        )
        
        # Should contain thematic template elements
        assert "theme" in prompt.lower() or "perspectives" in prompt.lower()
        assert "comprehensive analysis" in prompt.lower() or "diverse viewpoints" in prompt.lower()
    
    def test_build_intent_aware_prompt_scoped(self):
        """Test building scoped prompts."""
        query = "What did Toni Morrison say about writing?"
        
        # Mock route result with scoped entity
        mock_route_result = Mock()
        mock_route_result.scoped_entity = "Toni Morrison"
        
        prompt = build_intent_aware_prompt(
            query=query,
            chunks=self.mock_chunks,
            intent="scoped",
            route_result=mock_route_result
        )
        
        # Should contain scoped template elements
        assert "Toni Morrison" in prompt
        assert "specifically" in prompt.lower() or "focus" in prompt.lower()
    
    def test_build_intent_aware_prompt_fallback(self):
        """Test that fallback works when PromptBuilder fails."""
        query = "Test query"
        
        # Mock PromptBuilder to raise an exception
        with patch('rag.query_engine.get_prompt_builder') as mock_get_builder:
            mock_builder = Mock()
            mock_builder.build_qa_prompt.side_effect = Exception("Test error")
            mock_get_builder.return_value = mock_builder
            
            prompt = build_intent_aware_prompt(
                query=query,
                chunks=self.mock_chunks,
                intent="qa"
            )
            
            # Should fall back to basic prompt
            assert query in prompt
            assert "Context:" in prompt
    
    def test_prompt_builder_template_loading(self):
        """Test that PromptBuilder loads templates correctly."""
        builder = get_prompt_builder()
        
        # Should have loaded templates
        templates = builder.list_templates()
        assert len(templates) > 0
        
        # Should have expected template types
        template_names = [t.lower() for t in templates]
        assert any("qa" in name for name in template_names)
        assert any("generative" in name for name in template_names)
        assert any("thematic" in name for name in template_names)
    
    def test_prompt_builder_metadata_formatting(self):
        """Test that chunk metadata is formatted correctly."""
        builder = get_prompt_builder()
        
        # Test different citation styles
        inline_prompt = builder.build_qa_prompt("Test", self.mock_chunks, "qa")
        assert "🎓" in inline_prompt  # Lecture marker
        assert "🏅" in inline_prompt  # Ceremony marker
        assert "(Toni Morrison, 1993)" in inline_prompt  # Inline citation
    
    def test_prompt_builder_intent_detection(self):
        """Test that intent detection works correctly."""
        builder = get_prompt_builder()
        
        # Test email detection
        email_prompt = builder.build_generative_prompt(
            "Write an email accepting a job offer", 
            self.mock_chunks, 
            "email"
        )
        assert "email" in email_prompt.lower()
        
        # Test speech detection
        speech_prompt = builder.build_generative_prompt(
            "Give an inspirational speech", 
            self.mock_chunks, 
            "speech"
        )
        assert "speech" in speech_prompt.lower()


if __name__ == "__main__":
    pytest.main([__file__]) 