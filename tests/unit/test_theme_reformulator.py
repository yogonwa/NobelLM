import pytest
from config.theme_reformulator import ThemeReformulator

# Use the correct path to themes.json
THEME_PATH = "config/themes.json"

def test_expansion():
    """Test that expansion includes canonical themes and related keywords for a sample query."""
    reformulator = ThemeReformulator(THEME_PATH)
    terms = reformulator.expand_query_terms("What do winners say about morality and truth?")
    # Should include all justice and truth keywords
    assert "justice" in terms
    assert "truth" in terms
    assert "law" in terms
    assert "deception" in terms

# Parametric test for each theme in themes.json
import json
import os

def test_theme_expansion_for_all_keywords():
    """Test that each theme keyword expands to its canonical theme and related terms."""
    with open(THEME_PATH, "r", encoding="utf-8") as f:
        theme_map = json.load(f)
    reformulator = ThemeReformulator(THEME_PATH)
    # Test with justice-fairness pair specifically
    query = "What do laureates say about fairness?"
    expanded = reformulator.expand_query_terms(query)
    # The canonical theme keyword should be in the expansion
    assert "justice" in expanded, f"Theme 'justice' not in expansion for keyword 'fairness'"
    # The original keyword should be in the expansion
    assert "fairness" in expanded, f"Keyword 'fairness' not in expansion for theme 'justice'"
    # Should include other justice-related terms
    assert "law" in expanded
    assert "morality" in expanded
    assert "rights" in expanded

def test_empty_query_returns_empty_set():
    """Test that a query with no matching keywords returns an empty set."""
    reformulator = ThemeReformulator(THEME_PATH)
    result = reformulator.expand_query_terms("This query has no theme keywords.")
    assert result == set(), f"Expected empty set, got {result}"

@pytest.mark.parametrize("query", [
    "What do laureates say about JUSTICE?",
    "what do laureates say about justice?",
    "WhAt Do LaUrEaTeS sAy AbOuT jUsTiCe?"
])
def test_case_insensitivity(query):
    """Test that queries with different casing yield the same expansion."""
    reformulator = ThemeReformulator(THEME_PATH)
    result = reformulator.expand_query_terms(query)
    # Should always include all justice theme keywords
    justice_keywords = {"justice", "fairness", "law", "morality", "rights", "equality", "injustice"}
    for kw in justice_keywords:
        assert kw in result, f"Expected '{kw}' in expansion for query: {query}" 