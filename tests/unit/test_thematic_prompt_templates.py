"""
Unit tests for new thematic prompt templates.

Tests the new thematic prompt templates and subtype-aware template selection:
- thematic_synthesis_clean
- thematic_enumerative  
- thematic_comparative
- thematic_contextual
- Subtype-aware template selection in PromptBuilder
"""

import pytest
from rag.prompt_builder import PromptBuilder


@pytest.mark.unit
class TestThematicPromptTemplates:
    """Test new thematic prompt templates and subtype-aware selection."""
    
    @pytest.fixture
    def builder(self):
        """Create PromptBuilder instance for testing."""
        return PromptBuilder()
    
    def test_thematic_synthesis_clean_template_exists(self, builder):
        """Test that thematic_synthesis_clean template exists and is properly configured."""
        template = builder.get_template_info("thematic_synthesis_clean")
        
        assert template is not None
        assert template.name == "thematic_synthesis_clean"
        assert template.intent == "thematic"
        assert "synthesis" in template.tags
        assert "non-referential" in template.tags
        assert "cohesive" in template.tags
        assert template.chunk_count == 12
        assert template.citation_style == "inline"
        assert template.tone_preference == "reflective"
        
        # Check template content
        assert "cultural historian" in template.template
        assert "synthesize" in template.template
        assert "coherent narrative" in template.template
        assert "Do not reference the excerpts" in template.template
    
    def test_thematic_enumerative_template_exists(self, builder):
        """Test that thematic_enumerative template exists and is properly configured."""
        template = builder.get_template_info("thematic_enumerative")
        
        assert template is not None
        assert template.name == "thematic_enumerative"
        assert template.intent == "thematic"
        assert "enumerative" in template.tags
        assert "examples" in template.tags
        assert "referential" in template.tags
        assert template.chunk_count == 10
        assert template.citation_style == "inline"
        
        # Check template content
        assert "List specific examples" in template.template
        assert "speaker name and year" in template.template
        assert "Examples:" in template.template
    
    def test_thematic_comparative_template_exists(self, builder):
        """Test that thematic_comparative template exists and is properly configured."""
        template = builder.get_template_info("thematic_comparative")
        
        assert template is not None
        assert template.name == "thematic_comparative"
        assert template.intent == "thematic"
        assert "analytical" in template.tags
        assert "contrast" in template.tags
        assert template.chunk_count == 12
        assert template.citation_style == "inline"
        
        # Check template content
        assert "Compare and contrast" in template.template
        assert "similarities and differences" in template.template
        assert "Passages:" in template.template
    
    def test_thematic_contextual_template_exists(self, builder):
        """Test that thematic_contextual template exists and is properly configured."""
        template = builder.get_template_info("thematic_contextual")
        
        assert template is not None
        assert template.name == "thematic_contextual"
        assert template.intent == "thematic"
        assert "exploratory" in template.tags
        assert "contextual" in template.tags
        assert template.chunk_count == 10
        assert template.citation_style == "inline"
        
        # Check template content
        assert "historical and cultural context" in template.template
        assert "background factors" in template.template
        assert "Passages:" in template.template
    
    def test_subtype_aware_template_selection_synthesis(self, builder):
        """Test that synthesis subtype selects thematic_synthesis_clean template."""
        template = builder._get_template_for_intent("thematic", "thematic", "synthesis")
        
        assert template is not None
        assert template.name == "thematic_synthesis_clean"
        assert template.intent == "thematic"
    
    def test_subtype_aware_template_selection_enumerative(self, builder):
        """Test that enumerative subtype selects thematic_enumerative template."""
        template = builder._get_template_for_intent("thematic", "thematic", "enumerative")
        
        assert template is not None
        assert template.name == "thematic_enumerative"
        assert template.intent == "thematic"
    
    def test_subtype_aware_template_selection_analytical(self, builder):
        """Test that analytical subtype selects thematic_comparative template."""
        template = builder._get_template_for_intent("thematic", "thematic", "analytical")
        
        assert template is not None
        assert template.name == "thematic_comparative"
        assert template.intent == "thematic"
    
    def test_subtype_aware_template_selection_exploratory(self, builder):
        """Test that exploratory subtype selects thematic_contextual template."""
        template = builder._get_template_for_intent("thematic", "thematic", "exploratory")
        
        assert template is not None
        assert template.name == "thematic_contextual"
        assert template.intent == "thematic"
    
    def test_subtype_aware_template_selection_fallback(self, builder):
        """Test that unknown subtypes fall back to synthesis template."""
        template = builder._get_template_for_intent("thematic", "thematic", "unknown_subtype")
        
        assert template is not None
        # Should fall back to synthesis template
        assert template.name == "thematic_synthesis_clean"
        assert template.intent == "thematic"
    
    def test_subtype_aware_template_selection_no_subtype(self, builder):
        """Test that no subtype parameter falls back to synthesis template."""
        template = builder._get_template_for_intent("thematic", "thematic", None)
        
        assert template is not None
        # Should fall back to synthesis template
        assert template.name == "thematic_synthesis_clean"
        assert template.intent == "thematic"
    
    def test_template_formatting_with_metadata(self, builder):
        """Test that templates format correctly with chunk metadata."""
        mock_chunks = [
            {
                "text": "Language can never pin down slavery, genocide, war.",
                "metadata": {
                    "laureate": "Toni Morrison",
                    "year": "1993",
                    "speech_type": "lecture",
                    "category": "Literature"
                }
            },
            {
                "text": "The solitude of Latin America has a long history.",
                "metadata": {
                    "laureate": "Gabriel García Márquez", 
                    "year": "1982",
                    "speech_type": "ceremony",
                    "category": "Literature"
                }
            }
        ]
        
        # Test synthesis template formatting
        synthesis_template = builder.get_template_info("thematic_synthesis_clean")
        formatted_chunks = builder._format_chunks_with_metadata(mock_chunks, synthesis_template.citation_style)
        
        assert "Toni Morrison" in formatted_chunks
        assert "Gabriel García Márquez" in formatted_chunks
        assert "1993" in formatted_chunks
        assert "1982" in formatted_chunks
        assert "🎓" in formatted_chunks  # Lecture marker
        assert "🏅" in formatted_chunks  # Ceremony marker
    
    def test_all_thematic_templates_loaded(self, builder):
        """Test that all thematic templates are properly loaded."""
        expected_templates = [
            "thematic_synthesis_clean",
            "thematic_enumerative", 
            "thematic_comparative",
            "thematic_contextual"
        ]
        
        for template_name in expected_templates:
            template = builder.get_template_info(template_name)
            assert template is not None, f"Template {template_name} not found"
            assert template.intent == "thematic", f"Template {template_name} should have thematic intent"
    
    def test_template_validation(self, builder):
        """Test that all thematic templates pass validation."""
        expected_templates = [
            "thematic_synthesis_clean",
            "thematic_enumerative",
            "thematic_comparative", 
            "thematic_contextual"
        ]
        
        for template_name in expected_templates:
            assert builder.validate_template(template_name), f"Template {template_name} failed validation"
    
    def test_template_content_quality(self, builder):
        """Test that template content meets quality standards."""
        templates_to_check = [
            ("thematic_synthesis_clean", ["cultural historian", "synthesize", "coherent narrative"]),
            ("thematic_enumerative", ["List specific examples", "speaker name and year"]),
            ("thematic_comparative", ["Compare and contrast", "similarities and differences"]),
            ("thematic_contextual", ["historical and cultural context", "background factors"])
        ]
        
        for template_name, required_phrases in templates_to_check:
            template = builder.get_template_info(template_name)
            assert template is not None
            
            for phrase in required_phrases:
                assert phrase in template.template, f"Template {template_name} missing phrase: {phrase}"
    
    def test_template_parameter_substitution(self, builder):
        """Test that template parameters are properly substituted."""
        # Test synthesis template parameter substitution
        synthesis_template = builder.get_template_info("thematic_synthesis_clean")
        test_query = "justice and freedom"
        
        # The template should contain {query} placeholder
        assert "{query}" in synthesis_template.template
        
        # Test that substitution would work (basic check)
        substituted = synthesis_template.template.replace("{query}", test_query)
        assert test_query in substituted
        assert "{query}" not in substituted
    
    def test_template_metadata_completeness(self, builder):
        """Test that all templates have complete metadata."""
        expected_templates = [
            "thematic_synthesis_clean",
            "thematic_enumerative",
            "thematic_comparative",
            "thematic_contextual"
        ]
        
        for template_name in expected_templates:
            template = builder.get_template_info(template_name)
            assert template is not None
            
            # Check required metadata fields
            assert hasattr(template, 'name')
            assert hasattr(template, 'template')
            assert hasattr(template, 'intent')
            assert hasattr(template, 'tags')
            assert hasattr(template, 'chunk_count')
            assert hasattr(template, 'citation_style')
            assert hasattr(template, 'version')
            
            # Check that metadata is properly set
            assert template.name == template_name
            assert template.intent == "thematic"
            assert isinstance(template.tags, list)
            assert len(template.tags) > 0
            assert template.chunk_count > 0
            assert template.citation_style in ["inline", "footnote", "full"]
            assert template.version == "1.0" 