"""
Intent Classifier for Nobel Laureate Speech Explorer

Classifies user queries as factual, thematic, or generative, and detects if a thematic query is scoped to a specific laureate (by full or last name).

- Modular, testable, and extensible.
- Loads laureate names from Nobel metadata JSON.
- Prioritizes full name matches, but supports last name fallback.
"""
import re
import json
import logging
from typing import List, Optional, Dict, Any

class IntentClassifier:
    """
    Classifies the intent of a user query (e.g., factual, thematic, generative).
    If a thematic query is scoped to a laureate (full or last name), returns a dict with 'intent' and 'scoped_entity'.
    """
    FACTUAL_KEYWORDS = [
        "what", "when", "who", "where", "how many", "quote", "summarize", "give me the speech"
    ]
    THEMATIC_KEYWORDS = [
        "theme", "themes", "pattern", "patterns", "motif", "motifs", "compare", "comparison",
        "differences", "similarities", "trend", "trends", "common", "typical", "recurring", "across", "evolution",
        "topic", "topics", "change", "changed", "changes", "over time", "what are", "what do",
        "say about", "talk about", "what does", "how does", "describe", "describe the"
    ]
    GENERATIVE_KEYWORDS = [
        "write", "compose", "mimic", "generate", "paraphrase", "rewrite", "draft", "emulate",
        "in the style of", "like a laureate", "write me", "as if you were", "as a nobel laureate"
    ]

    def __init__(self, laureate_names_path: str = "data/nobel_literature.json"):
        self.factual_patterns = [re.compile(rf'\b{kw}\b', re.IGNORECASE) for kw in self.FACTUAL_KEYWORDS if ' ' not in kw]
        self.factual_phrases = [kw.lower() for kw in self.FACTUAL_KEYWORDS if ' ' in kw]
        self.thematic_patterns = [re.compile(rf'\b{kw}\b', re.IGNORECASE) for kw in self.THEMATIC_KEYWORDS if ' ' not in kw]
        self.thematic_phrases = [kw.lower() for kw in self.THEMATIC_KEYWORDS if ' ' in kw]
        self.generative_patterns = [re.compile(rf'\b{kw}\b', re.IGNORECASE) for kw in self.GENERATIVE_KEYWORDS if ' ' not in kw]
        self.generative_phrases = [kw.lower() for kw in self.GENERATIVE_KEYWORDS if ' ' in kw]
        self.laureate_full_names, self.laureate_last_names = self._load_laureate_names(laureate_names_path)

    def _load_laureate_names(self, path: str):
        """Load all laureate full names and last names from the Nobel literature metadata JSON."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            full_names = set()
            last_names = set()
            for year in data:
                for laureate in year.get("laureates", []):
                    name = laureate.get("full_name")
                    if name:
                        full_names.add(name)
                        last = name.split()[-1]
                        last_names.add(last)
            # Sort by length descending for greedy match
            return (sorted(full_names, key=lambda n: -len(n)), sorted(last_names, key=lambda n: -len(n)))
        except Exception as e:
            logging.warning(f"Could not load laureate names: {e}")
            return [], []

    def _find_laureate_in_query(self, query: str) -> Optional[str]:
        """
        Return the first laureate full name or last name found in the query (case-insensitive).
        Prioritize full name match, else fall back to last name.
        Returns the matched name (full or last), or None.
        """
        q = query.lower()
        # Full name match
        for name in self.laureate_full_names:
            if name.lower() in q:
                return name
        # Last name match
        for last in self.laureate_last_names:
            # Require word boundary for last name
            if re.search(rf'\b{re.escape(last.lower())}\b', q):
                return last
        return None

    def _matches(self, query: str, patterns, phrases):
        for pat in patterns:
            if pat.search(query):
                return True
        for phrase in phrases:
            if phrase in query:
                return True
        return False

    def classify(self, query: str) -> Any:
        """
        Classify the query as 'generative', 'thematic', or 'factual', or a dict with 'intent' and 'scoped_entity'.
        Precedence: generative > thematic > factual.
        Raises ValueError if no intent can be determined.
        """
        q = query.lower()
        if self._matches(q, self.generative_patterns, self.generative_phrases):
            return "generative"
        if self._matches(q, self.thematic_patterns, self.thematic_phrases):
            laureate = self._find_laureate_in_query(query)
            if laureate:
                return {"intent": "thematic", "scoped_entity": laureate}
            return "thematic"
        if self._matches(q, self.factual_patterns, self.factual_phrases):
            return "factual"
        raise ValueError(f"Could not determine intent for query: {query}") 