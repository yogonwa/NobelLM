"""
Query Router for Nobel Laureate Speech Explorer

This module provides a modular, extensible routing system for classifying user queries and dispatching them to the appropriate retrieval and prompting logic.

Components:
- IntentClassifier: Determines the intent/type of a query (factual, thematic, generative, etc.)
- RetrievalConfig: Dataclass holding retrieval parameters (top_k, filters, thresholds)
- PromptTemplateSelector: Selects the prompt template based on intent/type
- QueryRouter: Main orchestrator
- QueryRouteResult: Result object containing routing decisions

All components are designed for unit and integration testing.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
import logging
import re

# --- RetrievalConfig ---
@dataclass
class RetrievalConfig:
    """
    Holds retrieval parameters for a query.
    """
    top_k: int
    filters: Optional[Dict[str, Any]] = None
    score_threshold: Optional[float] = None

# --- QueryRouteResult ---
@dataclass
class QueryRouteResult:
    """
    Result of routing a query, including intent, retrieval config, prompt template, and logs.
    """
    intent: str
    retrieval_config: RetrievalConfig
    prompt_template: str
    logs: Dict[str, Any]

# --- IntentClassifier ---
class IntentClassifier:
    """
    Classifies the intent of a user query (e.g., factual, thematic, generative).
    Rule-based logic with clear keyword triggers and routing notes for each type.
    Uses word-boundary matching for single-word keywords and substring for multi-word phrases.
    All matching is case-insensitive.
    """
    # Trigger keywords for each intent type
    FACTUAL_KEYWORDS = [
        "what", "when", "who", "where", "how many", "quote", "summarize", "give me the speech"
    ]
    THEMATIC_KEYWORDS = [
        # Single words
        "theme", "themes", "pattern", "patterns", "motif", "motifs", "compare", "comparison",
        "differences", "similarities", "trend", "trends", "common", "typical", "recurring", "across", "evolution",
        "topic", "topics", "change", "changed", "changes", "over time"
    ]
    GENERATIVE_KEYWORDS = [
        # Single words
        "write", "compose", "mimic", "generate", "paraphrase", "rewrite", "draft", "emulate",
        # Multi-word phrases
        "in the style of", "like a laureate", "write me", "as if you were", "as a nobel laureate"
    ]

    def __init__(self):
        # Precompile regex for single-word keywords (case-insensitive)
        self.factual_patterns = [re.compile(rf'\b{kw}\b', re.IGNORECASE) for kw in self.FACTUAL_KEYWORDS if ' ' not in kw]
        self.factual_phrases = [kw.lower() for kw in self.FACTUAL_KEYWORDS if ' ' in kw]
        self.thematic_patterns = [re.compile(rf'\b{kw}\b', re.IGNORECASE) for kw in self.THEMATIC_KEYWORDS if ' ' not in kw]
        self.thematic_phrases = [kw.lower() for kw in self.THEMATIC_KEYWORDS if ' ' in kw]
        self.generative_patterns = [re.compile(rf'\b{kw}\b', re.IGNORECASE) for kw in self.GENERATIVE_KEYWORDS if ' ' not in kw]
        self.generative_phrases = [kw.lower() for kw in self.GENERATIVE_KEYWORDS if ' ' in kw]

    def _matches(self, query: str, patterns, phrases):
        # Check regex patterns (single-word keywords)
        for pat in patterns:
            if pat.search(query):
                return True
        # Check multi-word phrases using simple case-insensitive substring
        for phrase in phrases:
            if phrase in query:
                return True
        return False

    def classify(self, query: str) -> str:
        """
        Classify the query as 'generative', 'thematic', or 'factual' based on keyword rules.
        Precedence: generative > thematic > factual.
        """
        q = query.lower()
        # Generative/stylistic takes precedence
        if self._matches(q, self.generative_patterns, self.generative_phrases):
            return "generative"
        # Thematic/analytical next
        if self._matches(q, self.thematic_patterns, self.thematic_phrases):
            return "thematic"
        # Factual (default if question words present and not thematic/generative)
        if self._matches(q, self.factual_patterns, self.factual_phrases):
            return "factual"
        # Fallback: treat as factual
        return "factual"

# --- PromptTemplateSelector ---
class PromptTemplateSelector:
    """
    Selects the appropriate prompt template based on query intent/type.
    Currently supports 'factual' intent. Scaffolded for future intents.
    """
    FACTUAL_TEMPLATE = (
        "Answer the question using only the information in the context. "
        "If no answer is found, say \"I don't know.\"\n\n"
        "Context:\n"
        "{context}\n\n"
        "Question: {query}\n"
        "Answer:"
    )

    def __init__(self):
        pass

    def select(self, intent: str) -> str:
        """
        Return the prompt template string for the given intent.
        """
        if intent == "factual":
            return self.FACTUAL_TEMPLATE
        # Scaffold for future intents
        # elif intent == "thematic":
        #     return self.THEMATIC_TEMPLATE
        # elif intent == "generative":
        #     return self.GENERATIVE_TEMPLATE
        raise ValueError(f"Unknown intent: {intent}")

# --- Context Formatting Helper ---
def format_factual_context(chunks):
    """
    Format context for factual prompts as a bulleted list with text, laureate, and year.
    """
    return '\n'.join(
        f"- {c['text']} ({c['laureate']}, {c['year_awarded']})"
        for c in chunks
    )

# --- QueryRouter ---
class QueryRouter:
    """
    Orchestrates query classification, retrieval config selection, and prompt template selection.
    """
    def __init__(self, 
                 intent_classifier: Optional[IntentClassifier] = None,
                 prompt_template_selector: Optional[PromptTemplateSelector] = None):
        self.intent_classifier = intent_classifier or IntentClassifier()
        self.prompt_template_selector = prompt_template_selector or PromptTemplateSelector()
        # Config sources, logging, etc. can be injected here

    def route_query(self, query: str) -> QueryRouteResult:
        """
        Classify the query, select retrieval config and prompt template, and return routing result.
        """
        raise NotImplementedError 