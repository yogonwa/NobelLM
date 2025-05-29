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
    for theme, keywords in theme_map.items():
        for kw in keywords:
            query = f"What do laureates say about {kw}?"
            expanded = reformulator.expand_query_terms(query)
            # The canonical theme keyword should be in the expansion
            assert theme in expanded, f"Theme '{theme}' not in expansion for keyword '{kw}'"
            # The original keyword should be in the expansion
            assert kw in expanded, f"Keyword '{kw}' not in expansion for theme '{theme}'" 