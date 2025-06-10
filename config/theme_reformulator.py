"""
ThemeReformulator: Utility for mapping user queries to canonical themes and expanded keyword sets.

This module loads a theme-to-keywords mapping, lemmatizes both the keywords and user queries using spaCy,
and provides methods to extract canonical themes and expand queries for robust thematic search.
"""
import json
import re
import spacy
from pathlib import Path
from typing import Set

class ThemeReformulator:
    """
    Maps user queries to canonical themes and expanded keyword sets using lemmatization.
    Use this for robust thematic search and query normalization.
    """
    def __init__(self, theme_file: str = "themes.json"):
        """
        Initialize the ThemeReformulator.
        Args:
            theme_file: Path to the JSON file mapping themes to keywords.
        Loads and lemmatizes all keywords for robust matching.
        """
        self.nlp = spacy.load("en_core_web_sm")

        # Load theme → keywords
        theme_path = Path(theme_file)
        if not theme_path.exists():
            raise FileNotFoundError(f"Theme file not found: {theme_file}")
        with theme_path.open("r", encoding="utf-8") as f:
            self.theme_map_raw = json.load(f)

        # Lemmatize all keywords into normalized map
        self.theme_map = {}
        self.keyword_to_themes = {}

        for theme, keywords in self.theme_map_raw.items():
            lemmatized_keywords = {self.lemmatize_word(kw) for kw in keywords}
            # Store both original and lemmatized keywords
            all_keywords = set(keywords) | lemmatized_keywords
            self.theme_map[theme] = list(all_keywords)
            for lemma_kw in lemmatized_keywords:
                self.keyword_to_themes.setdefault(lemma_kw, set()).add(theme)
            for orig_kw in keywords:
                self.keyword_to_themes.setdefault(self.lemmatize_word(orig_kw), set()).add(theme)

    def lemmatize_word(self, word: str) -> str:
        """
        Lemmatize a single word using spaCy.
        Args:
            word: The word to lemmatize.
        Returns:
            The lemmatized form of the word.
        """
        return self.nlp(word.lower())[0].lemma_

    def lemmatize_query(self, query: str) -> Set[str]:
        """
        Lemmatize all tokens in a user query.
        Args:
            query: The user query string.
        Returns:
            Set of lemmatized tokens.
        """
        return {token.lemma_ for token in self.nlp(query.lower())}

    def extract_theme_keywords(self, query: str) -> Set[str]:
        """
        Lemmatize user query and match against lemmatized keywords.
        Args:
            query: The user query string.
        Returns:
            Set of matched lemmatized keywords present in the query.
        """
        lemmatized_tokens = self.lemmatize_query(query)
        return {
            kw for kw in self.keyword_to_themes
            if kw in lemmatized_tokens
        }

    def expand_query_terms(self, query: str) -> Set[str]:
        """
        Return full set of keywords from any matched themes.
        Args:
            query: The user query string.
        Returns:
            Set of all lemmatized keywords from matched themes.
        """
        matched_keywords = self.extract_theme_keywords(query)
        expanded = set()
        for kw in matched_keywords:
            for theme in self.keyword_to_themes[kw]:
                expanded.update(self.theme_map[theme])
        return expanded

    def extract_themes(self, query: str) -> Set[str]:
        """
        Extract canonical themes from a query by matching against theme keywords.
        Args:
            query: The user query string.
        Returns:
            Set of matched canonical theme names.
        """
        matched_keywords = self.extract_theme_keywords(query)
        themes = set()
        for kw in matched_keywords:
            themes.update(self.keyword_to_themes[kw])
        return themes 