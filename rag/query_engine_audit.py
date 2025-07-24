"""
Enhanced Query Engine with Comprehensive Audit Logging

This module provides the same functionality as query_engine.py but with
comprehensive audit logging that captures the complete RAG pipeline trace.
"""

import os
import logging
import warnings
import gc
import time
from typing import List, Dict, Optional, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import threading
import dotenv
from utils.cost_logger import log_cost_event
from utils.audit_logger import get_audit_logger, start_query_audit, complete_query_audit

try:
    import tiktoken
except ImportError:
    tiktoken = None

from rag.query_router import QueryRouter, PromptTemplateSelector, format_factual_context
from rag.prompt_builder import PromptBuilder
import json
from rag.metadata_utils import flatten_laureate_metadata
from rag.thematic_retriever import ThematicRetriever
from rag.utils import format_chunks_for_prompt, filter_top_chunks
from rag.cache import get_faiss_index_and_metadata, get_flattened_metadata, get_model
from rag.model_config import get_model_config, DEFAULT_MODEL_ID
from rag.retriever import query_index, get_mode_aware_retriever, BaseRetriever
from rag.logging_utils import get_module_logger, log_with_context, QueryContext
from rag.validation import validate_query_string, validate_model_id, validate_retrieval_parameters, validate_embedding_vector, validate_filters, is_invalid_vector

dotenv.load_dotenv()

# Get module logger
logger = get_module_logger(__name__)

# Global variables for caching
_QUERY_ROUTER: Optional[QueryRouter] = None
_PROMPT_BUILDER: Optional[PromptBuilder] = None

def get_query_router() -> QueryRouter:
    """Get or create the global QueryRouter instance."""
    global _QUERY_ROUTER
    if _QUERY_ROUTER is None:
        _QUERY_ROUTER = QueryRouter()
    return _QUERY_ROUTER

def get_prompt_builder() -> PromptBuilder:
    """Get or create the global PromptBuilder instance."""
    global _PROMPT_BUILDER
    if _PROMPT_BUILDER is None:
        _PROMPT_BUILDER = PromptBuilder()
    return _PROMPT_BUILDER

def build_intent_aware_prompt(
    query: str, 
    chunks: List[Dict], 
    intent: str,
    route_result: Optional[Any] = None
) -> str:
    """
    Build an intent-aware prompt using the new PromptBuilder.
    
    Args:
        query: The user's query string
        chunks: List of retrieved chunks with metadata
        intent: Query intent (qa, generative, thematic, scoped)
        route_result: Optional route result from QueryRouter for additional context
        
    Returns:
        Formatted prompt string with metadata and citations
    """
    prompt_builder = get_prompt_builder()
    
    try:
        if intent == "generative":
            # Determine specific generative intent
            if "email" in query.lower() or "accept" in query.lower():
                return prompt_builder.build_generative_prompt(query, chunks, "email")
            elif "speech" in query.lower() or "inspirational" in query.lower():
                return prompt_builder.build_generative_prompt(query, chunks, "speech")
            elif "reflection" in query.lower() or "personal" in query.lower():
                return prompt_builder.build_generative_prompt(query, chunks, "reflection")
            else:
                return prompt_builder.build_generative_prompt(query, chunks, "generative")
        
        elif intent == "thematic":
            # Extract theme from query or route result
            theme = query
            if route_result and hasattr(route_result, 'theme'):
                theme = route_result.theme
            return prompt_builder.build_thematic_prompt(query, chunks, theme)
        
        elif intent == "scoped":
            # Extract laureate from route result or query
            laureate = "Unknown"
            if route_result and hasattr(route_result, 'scoped_entity'):
                laureate = route_result.scoped_entity
            return prompt_builder.build_scoped_prompt(query, chunks, laureate)
        
        else:
            # Default to QA prompt
            return prompt_builder.build_qa_prompt(query, chunks, intent)
            
    except Exception as e:
        logger.error(f"Error building intent-aware prompt: {e}")
        # Fallback to simple prompt
        context = format_chunks_for_prompt(chunks)
        return f"Answer the following question about Nobel Literature laureates: {query}\n\nContext: {context}"

def call_openai(prompt: str, model: str = "gpt-3.5-turbo") -> dict:
    """
    Call OpenAI's ChatCompletion endpoint using GPT-3.5. Returns the model's answer and token usage as a dict.
    Reads API key from .env or environment. Handles errors gracefully.
    Compatible with openai>=1.0.0.
    """
    try:
        import openai
    except ImportError:
        logger.error("openai package is not installed. Please install openai to use this feature.")
        raise
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment.")
    client = openai.OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant for Nobel Prize literature research."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=512,
        )
        answer = response.choices[0].message.content.strip()
        usage = getattr(response, 'usage', None)
        completion_tokens = usage.completion_tokens if usage else None
        prompt_tokens = usage.prompt_tokens if usage else None
        return {
            "answer": answer,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "model": model
        }
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        return {
            "answer": f"[OpenAI API error] {e}",
            "prompt_tokens": None,
            "completion_tokens": None,
            "model": model
        }

def infer_top_k_from_query(query: str) -> int:
    """Infer appropriate top_k value based on query characteristics."""
    query_lower = query.lower()
    
    # Thematic queries need more context
    if any(word in query_lower for word in ["theme", "thematic", "pattern", "trend", "overall", "generally"]):
        return 15
    
    # Generative queries need more context
    if any(word in query_lower for word in ["write", "create", "generate", "compose", "draft"]):
        return 10
    
    # Default for factual queries
    return 5

def answer_query_with_audit(
    query_string: str,
    model_id: Optional[str] = None,
    score_threshold: float = 0.2,
    min_return: Optional[int] = None,
    max_return: Optional[int] = None,
    source: str = "api"
) -> Dict[str, Any]:
    """
    Enhanced answer_query with comprehensive audit logging.
    
    This function provides the same functionality as answer_query() but with
    detailed audit logging that captures the complete RAG pipeline trace.
    """
    # Start audit logging
    audit_logger = get_audit_logger()
    query_id = start_query_audit(query_string, source)
    
    # Track timing
    start_time = time.time()
    
    try:
        # Early validation of all inputs
        validate_query_string(query_string, context="answer_query")
        if model_id is not None:
            validate_model_id(model_id, context="answer_query")
        
        # Infer top_k for validation based on query type
        inferred_top_k = infer_top_k_from_query(query_string)
        validate_retrieval_parameters(
            top_k=inferred_top_k,
            score_threshold=score_threshold,
            min_return=min_return or 3,
            max_return=max_return,
            context="answer_query"
        )
        
        with QueryContext(model_id) as ctx:
            log_with_context(
                logger,
                logging.INFO,
                "QueryEngine",
                "Starting query processing",
                {
                    "query": query_string,
                    "model_id": model_id,
                    "score_threshold": score_threshold
                }
            )
            
            # Route the query
            route_start_time = time.time()
            route_result = get_query_router().route_query(query_string)
            route_time = (time.time() - route_start_time) * 1000
            
            # Log intent classification
            audit_logger.log_intent_classification(
                query_id=query_id,
                intent=route_result.intent,
                confidence=getattr(route_result, 'confidence', 0.0),
                matched_terms=getattr(route_result, 'matched_terms', None),
                scoped_entity=getattr(route_result, 'scoped_entity', None),
                decision_trace=getattr(route_result, 'decision_trace', None)
            )
            
            if route_result.answer_type == "metadata":
                log_with_context(
                    logger,
                    logging.INFO,
                    "QueryEngine",
                    "Using metadata answer",
                    {"intent": route_result.intent}
                )
                
                # Log final result for metadata queries
                audit_logger.log_final_result(
                    query_id=query_id,
                    answer_type="metadata",
                    final_answer=route_result.answer,
                    total_processing_time_ms=(time.time() - start_time) * 1000
                )
                
                # Complete audit
                complete_query_audit(query_id)
                
                return {
                    "answer_type": "metadata",
                    "answer": route_result.answer,
                    "metadata_answer": route_result.metadata_answer,
                    "sources": []  # No chunks for metadata answers
                }
            
            # Get the appropriate retriever based on intent
            retrieval_start_time = time.time()
            
            if route_result.intent == "thematic":
                retriever = ThematicRetriever(model_id=model_id)
                
                # Log keyword expansion for thematic queries
                if hasattr(retriever, 'reformulator') and hasattr(retriever.reformulator, 'expand_query'):
                    try:
                        expanded_terms = retriever.reformulator.expand_query(query_string)
                        audit_logger.log_keyword_expansion(
                            query_id=query_id,
                            expanded_terms=expanded_terms,
                            expansion_method="thematic"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to log keyword expansion: {e}")
                
                # Thematic queries use a larger top_k (15) and need more diverse context
                effective_score_threshold = route_result.retrieval_config.score_threshold or score_threshold
                chunks = retriever.retrieve(
                    query_string,
                    top_k=15,
                    filters=route_result.retrieval_config.filters,
                    score_threshold=effective_score_threshold,
                    min_return=min_return or 5,
                    max_return=max_return or 12
                )
            else:
                # Factual or generative query
                retriever = get_mode_aware_retriever(model_id)
                effective_score_threshold = route_result.retrieval_config.score_threshold or score_threshold
                chunks = retriever.retrieve(
                    query_string,
                    top_k=route_result.retrieval_config.top_k,
                    filters=route_result.retrieval_config.filters,
                    score_threshold=effective_score_threshold,
                    min_return=min_return or 3,
                    max_return=max_return or 10
                )
            
            retrieval_time = (time.time() - retrieval_start_time) * 1000
            
            # Log retrieval process
            audit_logger.log_retrieval_process(
                query_id=query_id,
                retrieval_method="qdrant" if "qdrant" in str(type(retriever)).lower() else "faiss",
                top_k=route_result.retrieval_config.top_k,
                score_threshold=effective_score_threshold,
                filters_applied=route_result.retrieval_config.filters,
                chunks_retrieved=chunks,
                retrieval_scores=[c.get("score", 0) for c in chunks] if chunks else None,
                processing_time_ms=retrieval_time
            )
            
            log_with_context(
                logger,
                logging.INFO,
                "QueryEngine",
                "Retrieved chunks",
                {
                    "count": len(chunks),
                    "intent": route_result.intent,
                    "mean_score": np.mean([c["score"] for c in chunks]) if chunks else 0
                }
            )
            
            # Format chunks for prompt
            context = format_chunks_for_prompt(chunks)
            
            # Build and call LLM
            prompt = build_intent_aware_prompt(
                query_string,
                chunks,
                route_result.intent,
                route_result
            )
            
            # Log prompt construction
            audit_logger.log_prompt_construction(
                query_id=query_id,
                prompt_template=f"intent_aware_{route_result.intent}",
                final_prompt=prompt,
                context_length=len(context)
            )
            
            log_with_context(
                logger,
                logging.INFO,
                "QueryEngine",
                "Calling LLM",
                {"prompt_length": len(prompt)}
            )
            
            # Call LLM with timing
            llm_start_time = time.time()
            response = call_openai(prompt)
            llm_time = (time.time() - llm_start_time) * 1000
            
            # Calculate estimated cost
            estimated_cost = 0.0
            if response.get("prompt_tokens") and response.get("completion_tokens"):
                # Rough estimate: $0.0015 per 1K tokens for GPT-3.5-turbo
                total_tokens = response["prompt_tokens"] + response["completion_tokens"]
                estimated_cost = (total_tokens / 1000) * 0.0015
            
            # Log LLM interaction
            audit_logger.log_llm_interaction(
                query_id=query_id,
                llm_model=response.get("model", "gpt-3.5-turbo"),
                llm_response=response.get("answer", ""),
                prompt_tokens=response.get("prompt_tokens", 0),
                completion_tokens=response.get("completion_tokens", 0),
                total_tokens=response.get("prompt_tokens", 0) + response.get("completion_tokens", 0),
                estimated_cost_usd=estimated_cost,
                llm_temperature=0.2,
                processing_time_ms=llm_time
            )
            
            # Compile final answer
            result = {
                "answer_type": "rag",
                "answer": response["answer"],
                "metadata_answer": None,
                "sources": chunks
            }
            
            # Log final result
            audit_logger.log_final_result(
                query_id=query_id,
                answer_type="rag",
                final_answer=response["answer"],
                sources_used=chunks,
                total_processing_time_ms=(time.time() - start_time) * 1000
            )
            
            log_with_context(
                logger,
                logging.INFO,
                "QueryEngine",
                "Query completed successfully",
                {
                    "intent": route_result.intent,
                    "chunk_count": len(chunks),
                    "completion_tokens": response.get("completion_tokens", 0)
                }
            )
            
            # Memory cleanup after heavy operations
            gc.collect()
            
            return result
            
    except Exception as e:
        # Log error
        audit_logger.log_error(
            query_id=query_id,
            error_message=str(e),
            error_type=type(e).__name__
        )
        
        log_with_context(
            logger,
            logging.ERROR,
            "QueryEngine",
            "Query failed",
            {
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        raise
    finally:
        # Always complete the audit
        complete_query_audit(query_id)

# Backward compatibility - use the audit version by default
def answer_query(*args, **kwargs):
    """Backward compatibility wrapper for answer_query_with_audit."""
    return answer_query_with_audit(*args, **kwargs) 