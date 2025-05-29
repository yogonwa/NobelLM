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
from typing import Any, Dict, Optional, List
import logging
import re
from rag.metadata_handler import handle_metadata_query  # Import the metadata handler
from config.theme_reformulator import ThemeReformulator
import json
from rag.intent_classifier import IntentClassifier

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
    Result of routing a query, including intent, retrieval config, prompt template, logs, answer type, and optional metadata answer.
    """
    intent: str
    retrieval_config: RetrievalConfig
    prompt_template: str
    logs: Dict[str, Any]
    answer_type: str  # 'metadata', 'rag', etc.
    metadata_answer: Optional[Dict[str, Any]] = None  # Only for metadata answers

# --- PromptTemplateSelector ---
class PromptTemplateSelector:
    """
    Selects the appropriate prompt template based on query intent/type.
    Supports 'factual', 'thematic', and 'generative' intents.
    """
    FACTUAL_TEMPLATE = (
        "Answer the question using only the information in the context. "
        "If no answer is found, say \"I don't know.\"\n\n"
        "Context:\n"
        "{context}\n\n"
        "Question: {query}\n"
        "Answer:"
    )

    THEMATIC_TEMPLATE = (
        """
You are a literary analyst with expertise in thematic interpretation across historical texts.

The user has asked a high-level question about Nobel Prize lectures. Your task is to analyze the excerpts below and synthesize key ideas, values, or recurring motifs across authors, time periods, and genres.

User question:
{query}

Excerpts:
{context}

Instructions:
- Identify prominent or recurring themes that appear across multiple excerpts.
- Highlight contrasting ideas or how certain concepts evolve over time or differ by speaker.
- Reference the speaker and year when relevant, but do not quote directly.
- Write in clear, analytical prose — not a list or bullet points.
"""
    )

    GENERATIVE_TEMPLATE = (
        """
You are a Nobel laureate speech generator. Write a creative, original response in the style of a Nobel laureate, using the context below if relevant.

Context:
{context}

User request:
{query}

Response:
"""
    )

    def __init__(self):
        pass

    def select(self, intent: str) -> str:
        """
        Return the prompt template string for the given intent.
        """
        if intent == "factual":
            return self.FACTUAL_TEMPLATE
        elif intent == "thematic":
            return self.THEMATIC_TEMPLATE
        elif intent == "generative":
            return self.GENERATIVE_TEMPLATE
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

# --- Add ThemeReformulator for thematic queries ---
THEME_REFORMULATOR = ThemeReformulator("config/themes.json")

# --- QueryRouter ---
class QueryRouter:
    """
    Orchestrates query classification, retrieval config selection, prompt template selection, and metadata handler integration.
    For factual queries, attempts to answer using metadata before falling back to RAG.
    """
    def __init__(self, 
                 intent_classifier: Optional[IntentClassifier] = None,
                 prompt_template_selector: Optional[PromptTemplateSelector] = None,
                 metadata: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize the QueryRouter.
        Args:
            intent_classifier: Optional custom intent classifier.
            prompt_template_selector: Optional custom prompt template selector.
            metadata: List of laureate metadata dicts for direct factual QA.
        """
        self.intent_classifier = intent_classifier or IntentClassifier()
        self.prompt_template_selector = prompt_template_selector or PromptTemplateSelector()
        self.metadata = metadata  # Should be set to laureate metadata externally
        # Config sources, logging, etc. can be injected here

    def route_query(self, query: str) -> QueryRouteResult:
        """
        Classify the query, attempt metadata answer if factual, else route to RAG.
        Returns a QueryRouteResult with all routing decisions and answer type.
        """
        logs = {}
        classified = self.intent_classifier.classify(query)
        # Support both string and dict return from classifier
        if isinstance(classified, dict):
            intent = classified.get("intent")
            scoped_entity = classified.get("scoped_entity")
        else:
            intent = classified
            scoped_entity = None
        logs['intent'] = intent
        if scoped_entity:
            logs['scoped_entity'] = scoped_entity

        # --- Thematic query: extract canonical themes and expanded terms ---
        if intent == "thematic":
            canonical_themes = THEME_REFORMULATOR.extract_theme_keywords(query)
            expanded_terms = THEME_REFORMULATOR.expand_query_terms(query)
            logs['thematic_canonical_themes'] = list(canonical_themes)
            logs['thematic_expanded_terms'] = list(expanded_terms)

        # Factual: Try metadata handler first if metadata is available
        if intent == "factual" and self.metadata is not None:
            metadata_result = handle_metadata_query(query, self.metadata)
            if metadata_result is not None:
                logs['metadata_handler'] = 'matched'
                logs['metadata_rule'] = metadata_result.get('source', {}).get('rule', 'unknown')
                return QueryRouteResult(
                    intent=intent,
                    retrieval_config=RetrievalConfig(top_k=0),  # No retrieval needed
                    prompt_template="",  # Not used for metadata
                    logs=logs,
                    answer_type="metadata",
                    metadata_answer=metadata_result
                )
            else:
                logs['metadata_handler'] = 'no_match'

        # Fallback: RAG retrieval
        if intent == "factual":
            retrieval_config = RetrievalConfig(top_k=5, score_threshold=0.25)
        elif intent == "thematic":
            # If scoped_entity, filter by laureate
            filters = {"laureate": scoped_entity} if scoped_entity else None
            retrieval_config = RetrievalConfig(top_k=15, filters=filters, score_threshold=None)
        else:  # generative
            retrieval_config = RetrievalConfig(top_k=10, score_threshold=None)

        prompt_template = self.prompt_template_selector.select(intent)
        return QueryRouteResult(
            intent=intent,
            retrieval_config=retrieval_config,
            prompt_template=prompt_template,
            logs=logs,
            answer_type="rag"
        ) 