import pytest
from rag.query_router import PromptTemplateSelector

def test_select_factual_prompt_template():
    selector = PromptTemplateSelector()
    template = selector.select('factual')
    assert "Answer the question using only the information in the context" in template
    assert "Context:" in template
    assert "Question:" in template
    assert "Answer:" in template
    assert "literary analyst" not in template
    assert "creative, original response" not in template

def test_select_thematic_prompt_template():
    selector = PromptTemplateSelector()
    template = selector.select('thematic')
    assert "literary analyst" in template
    assert "User question:" in template
    assert "Excerpts:" in template
    assert "Instructions:" in template
    assert "Identify prominent or recurring themes" in template
    assert "Reference the speaker and year when relevant" in template
    assert "Answer the question using only the information in the context" not in template

def test_select_generative_prompt_template():
    selector = PromptTemplateSelector()
    template = selector.select('generative')
    assert "Nobel laureate speech generator" in template
    assert "creative, original response" in template
    assert "Context:" in template
    assert "User request:" in template
    assert "Response:" in template
    assert "literary analyst" not in template
    assert "Answer the question using only the information in the context" not in template

def test_prompt_template_selector_error():
    selector = PromptTemplateSelector()
    with pytest.raises(ValueError):
        selector.select('unknown_intent') 