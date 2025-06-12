"""
Query router module for NobelLM RAG pipeline.

This module provides query classification and routing logic to determine
the appropriate retrieval strategy and prompt template for each query.
"""
import logging
from typing import Dict, Any, Optional, List, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from rag.logging_utils import get_module_logger, log_with_context, QueryContext
from rag.metadata_handler import handle_metadata_query
from config.theme_reformulator import ThemeReformulator
import json
from rag.intent_classifier import IntentClassifier

# --- Module-level setup ---
logger = get_module_logger(__name__)
_router = None  # Global router instance

# --- Constants ---
THEME_REFORMULATOR = ThemeReformulator("config/themes.json")

# --- Data Classes and Enums ---
class QueryIntent(str, Enum):
    """Enum for query intent classification."""
    FACTUAL = "factual"
    THEMATIC = "thematic"
    GENERATIVE = "generative"
    METADATA = "metadata"

@dataclass
class RetrievalConfig:
    """Configuration for chunk retrieval based on query intent."""
    top_k: int
    filters: Optional[Dict[str, Any]] = None
    score_threshold: Optional[float] = None
    min_score: float = 0.2

@dataclass
class QueryRouteResult:
    """Result of query routing including intent and retrieval config."""
    intent: QueryIntent
    answer_type: str  # "rag" or "metadata"
    answer: Optional[str] = None
    metadata_answer: Optional[Dict[str, Any]] = None
    retrieval_config: RetrievalConfig = None
    prompt_template: Optional[str] = None
    logs: Dict[str, Any] = field(default_factory=dict)

# --- Helper Classes ---
class PromptTemplateSelector:
    """Manages prompt templates for different query intents."""
    
    @staticmethod
    def get_template(intent: QueryIntent) -> str:
        """Get the appropriate prompt template for the query intent."""
        templates = {
            QueryIntent.FACTUAL: "Answer the following factual question about Nobel Literature laureates: {query}\n\nContext: {context}",
            QueryIntent.THEMATIC: "Analyze the following thematic question about Nobel Literature laureates: {query}\n\nContext: {context}",
            QueryIntent.GENERATIVE: "Generate a creative response to: {query}\n\nContext: {context}"
        }
        return templates.get(intent, templates[QueryIntent.FACTUAL])

# --- Helper Functions ---
def format_factual_context(chunks):
    """
    Format context for factual prompts as a bulleted list with text, laureate, and year.
    """
    return '\n'.join(
        f"- {c['text']} ({c['laureate']}, {c['year_awarded']})"
        for c in chunks
    )

# --- Main QueryRouter Class ---
class QueryRouter:
    """Routes queries to appropriate retrieval strategies."""
    
    def __init__(self, metadata: Optional[Dict[str, Any]] = None):
        """Initialize the query router with intent classification thresholds."""
        self.intent_thresholds = {
            QueryIntent.THEMATIC: 0.7,
            QueryIntent.GENERATIVE: 0.6,
            QueryIntent.METADATA: 0.8
        }
        self.metadata = metadata
        self.intent_classifier = IntentClassifier()
        
        log_with_context(
            logger,
            logging.INFO,
            "QueryRouter",
            "Initialized router",
            {"thresholds": self.intent_thresholds}
        )
    
    def route_query(self, query: str) -> QueryRouteResult:
        """
        Route a query to the appropriate retrieval strategy.
        
        Args:
            query: The user's query string
            
        Returns:
            QueryRouteResult with intent and retrieval configuration
        """
        logs = {}  # Initialize logs dict
        with QueryContext() as ctx:
            log_with_context(
                logger,
                logging.INFO,
                "QueryRouter",
                "Routing query",
                {"query": query}
            )
            
            try:
                # Get intent from classifier (now returns IntentResult)
                intent_result = self.intent_classifier.classify(query)
                
                # Extract information from IntentResult
                intent_str = intent_result.intent
                confidence = intent_result.confidence
                matched_terms = intent_result.matched_terms
                scoped_entities = intent_result.scoped_entities
                decision_trace = intent_result.decision_trace
                
                # Convert string intent to enum and validate
                try:
                    intent = QueryIntent(intent_str)
                except ValueError:
                    error_msg = f"Invalid intent from classifier: {intent_str}"
                    log_with_context(
                        logger,
                        logging.ERROR,
                        "QueryRouter",
                        "Invalid intent from classifier",
                        {"intent": intent_str}
                    )
                    raise ValueError(error_msg)
                
                # Log detailed intent information
                logs.update({
                    'intent': intent_str,
                    'confidence': confidence,
                    'matched_terms': matched_terms,
                    'scoped_entities': scoped_entities,
                    'decision_trace': decision_trace
                })
                
                log_with_context(
                    logger,
                    logging.INFO,
                    "QueryRouter",
                    "Intent classified",
                    {
                        "query": query,
                        "intent": intent,
                        "confidence": confidence,
                        "matched_terms": matched_terms,
                        "scoped_entities": scoped_entities
                    }
                )
                
                # Handle low confidence cases
                if confidence < 0.5:
                    log_with_context(
                        logger,
                        logging.WARNING,
                        "QueryRouter",
                        "Low confidence intent classification",
                        {
                            "query": query,
                            "intent": intent,
                            "confidence": confidence,
                            "decision_trace": decision_trace
                        }
                    )
                
                # First check if this is a metadata query
                if intent == QueryIntent.FACTUAL and self.metadata is not None:
                    metadata_result = handle_metadata_query(query, self.metadata)
                    if metadata_result is not None:
                        logs['metadata_handler'] = 'matched'
                        logs['metadata_rule'] = metadata_result.get('source', {}).get('rule', 'unknown')
                        log_with_context(
                            logger,
                            logging.INFO,
                            "QueryRouter",
                            "Using metadata answer",
                            {
                                "query": query,
                                "rule": metadata_result.get("source", {}).get("rule", "unknown")
                            }
                        )
                        return QueryRouteResult(
                            intent=intent,
                            answer_type="metadata",
                            answer=metadata_result.get("answer"),
                            metadata_answer=metadata_result,
                            retrieval_config=RetrievalConfig(top_k=0),  # No retrieval needed
                            prompt_template="",  # Not used for metadata
                            logs=logs
                        )
                    else:
                        logs['metadata_handler'] = 'no_match'
                        log_with_context(
                            logger,
                            logging.INFO,
                            "QueryRouter",
                            "No metadata match, falling back to RAG",
                            {"query": query}
                        )
                
                # Get retrieval config based on intent
                if intent == QueryIntent.FACTUAL:
                    config = RetrievalConfig(top_k=5, score_threshold=0.25)
                elif intent == QueryIntent.THEMATIC:
                    # Extract themes using theme reformulator
                    themes = THEME_REFORMULATOR.extract_themes(query)
                    expanded_terms = THEME_REFORMULATOR.expand_query_terms(query)
                    logs.update({
                        'thematic_canonical_themes': themes,
                        'thematic_expanded_terms': expanded_terms
                    })
                    # Handle multiple scoped entities
                    filters = None
                    if scoped_entities:
                        if len(scoped_entities) == 1:
                            # Single entity - use direct filter
                            filters = {"laureate": scoped_entities[0]}
                        else:
                            # Multiple entities - will be handled by ThematicRetriever
                            logs['multiple_laureates'] = scoped_entities
                    config = RetrievalConfig(top_k=15, filters=filters, score_threshold=None)
                else:  # generative
                    config = RetrievalConfig(top_k=10, score_threshold=None)
                
                # Get prompt template
                template = PromptTemplateSelector.get_template(intent)
                
                return QueryRouteResult(
                    intent=intent,
                    answer_type="rag",
                    answer=None,  # Will be filled by query engine
                    metadata_answer=None,
                    retrieval_config=config,
                    prompt_template=template,
                    logs=logs
                )
                
            except Exception as e:
                logs['error'] = str(e)
                logs['error_type'] = type(e).__name__
                log_with_context(
                    logger,
                    logging.ERROR,
                    "QueryRouter",
                    "Query routing failed",
                    {
                        "query": query,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                # Fall back to factual query on error
                return QueryRouteResult(
                    intent=QueryIntent.FACTUAL,
                    answer_type="rag",
                    answer=None,
                    metadata_answer=None,
                    retrieval_config=RetrievalConfig(top_k=5),
                    prompt_template=PromptTemplateSelector.get_template(QueryIntent.FACTUAL),
                    logs=logs
                )

# --- Module-level Functions ---
def get_query_router() -> QueryRouter:
    """Get or create the global query router instance."""
    global _router
    if _router is None:
        _router = QueryRouter()
    return _router 