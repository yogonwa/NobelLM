import pytest
from rag.query_router import PromptTemplateSelector, QueryIntent

def test_get_factual_prompt_template():
    template = PromptTemplateSelector.get_template(QueryIntent.FACTUAL)
    assert "Answer the following factual question about Nobel Literature laureates" in template
    assert "{query}" in template
    assert "{context}" in template
    assert "literary analyst" not in template
    assert "creative, original response" not in template

def test_get_thematic_prompt_template():
    template = PromptTemplateSelector.get_template(QueryIntent.THEMATIC)
    assert "Analyze the following thematic question about Nobel Literature laureates" in template
    assert "{query}" in template
    assert "{context}" in template
    assert "literary analyst" not in template
    assert "creative, original response" not in template

def test_get_generative_prompt_template():
    template = PromptTemplateSelector.get_template(QueryIntent.GENERATIVE)
    assert "Generate a creative response to" in template
    assert "{query}" in template
    assert "{context}" in template
    assert "literary analyst" not in template
    assert "creative, original response" not in template

def test_prompt_template_selector_fallback():
    # Test that unknown intent falls back to factual template
    template = PromptTemplateSelector.get_template("unknown_intent")
    assert "Answer the following factual question about Nobel Literature laureates" in template
    assert "{query}" in template
    assert "{context}" in template 