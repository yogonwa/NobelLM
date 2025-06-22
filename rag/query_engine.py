"""
Query engine module for NobelLM RAG pipeline.

This module provides the main entry points for querying the Nobel Literature corpus
using retrieval-augmented generation (RAG). The canonical entry point is answer_query(),
which provides consistent score threshold handling and model-aware retrieval across
all query types.

The legacy query() function is deprecated and will be removed in a future version.
Use answer_query() instead for a fully consistent and robust retrieval + prompting
pipeline.

Key features:
- Consistent score threshold filtering across all paths
- Model-aware retrieval configuration
- Query type-specific min/max return counts
- Proper error handling and logging
- Intent-specific prompt building with metadata awareness
"""
import os
import logging
import warnings
from typing import List, Dict, Optional, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import threading
import dotenv
from utils.cost_logger import log_cost_event
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

USE_FAISS_SUBPROCESS = os.getenv("NOBELLM_USE_FAISS_SUBPROCESS", "0") == "1"

__all__ = ["answer_query"]  # Only export answer_query as the canonical entry point

# Remove local model caching - use cached version from rag.cache
# _MODEL = None
# _MODEL_LOCK = threading.Lock()
_INDEX = None
_METADATA = None
_INDEX_LOCK = threading.Lock()

# PromptBuilder singleton
_PROMPT_BUILDER = None
_PROMPT_BUILDER_LOCK = threading.Lock()

KEYWORDS_TRIGGER_EXPANSION = [
    "theme", "themes", "pattern", "patterns", "typical", "common",
    "most", "across", "often", "generally", "usually", "style", "styles"
]

# Remove local get_model function - use cached version from rag.cache
# def get_model(model_id: str = None) -> SentenceTransformer:
#     """
#     Singleton loader for the embedding model specified by model_id.
#     Uses centralized config for model name.
#     """
#     global _MODEL
#     if _MODEL is None:
#         with _MODEL_LOCK:
#             if _MODEL is None:
#                 config = get_model_config(model_id)
#                 logger.info(f"Loading embedding model '{config['model_name']}'...")
#                 _MODEL = SentenceTransformer(config['model_name'])
#     return _MODEL


def get_index_and_metadata(model_id: str = None):
    """
    Singleton loader for the FAISS index and chunk metadata for the specified model.
    Uses centralized config for index and metadata paths.
    Checks embedding dimension consistency.
    """
    global _INDEX, _METADATA
    if _INDEX is None or _METADATA is None:
        with _INDEX_LOCK:
            if _INDEX is None or _METADATA is None:
                model_id = model_id or DEFAULT_MODEL_ID
                _INDEX, _METADATA = get_faiss_index_and_metadata(model_id)
                config = get_model_config(model_id)
                # Consistency check
                if hasattr(_INDEX, 'd') and _INDEX.d != config['embedding_dim']:
                    raise ValueError(f"Index dimension ({_INDEX.d}) does not match model config ({config['embedding_dim']}) for model '{model_id or DEFAULT_MODEL_ID}'")
    return _INDEX, _METADATA


def embed_query(query: str, model_id: str = None) -> np.ndarray:
    """
    Embed the user query using the embedding model specified by model_id.
    Returns a numpy array embedding.
    """
    model = get_model(model_id)
    emb = model.encode(query, show_progress_bar=False, normalize_embeddings=True)
    return np.array(emb, dtype=np.float32)


def retrieve_chunks(
    query_embedding: np.ndarray,
    k: int = 3,
    filters: Optional[Dict[str, Any]] = None,
    score_threshold: float = 0.2,
    min_k: int = 3,
    model_id: str = None
) -> List[Dict[str, Any]]:
    """
    Retrieve top-k most relevant chunks from the FAISS index for the specified model.
    Uses subprocess mode if USE_FAISS_SUBPROCESS is set (for Mac/Intel dev), else in-process (for Linux/prod).
    Passes filters to query_index for pre-retrieval metadata filtering.
    
    Args:
        query_embedding: Normalized query vector
        k: Number of results to return
        filters: Optional metadata filters
        score_threshold: Minimum similarity score threshold (default: 0.2)
        min_k: Minimum number of results to return (unused, kept for backward compatibility)
        model_id: Model identifier (e.g., "bge-large")
        
    Returns:
        List of top-k chunks with metadata and scores
    """
    # Early validation of all inputs
    # For subprocess mode, query_embedding is actually a string
    if USE_FAISS_SUBPROCESS:
        if not isinstance(query_embedding, str):
            raise ValueError("In subprocess mode, query_embedding must be a string")
        validate_query_string(query_embedding, context="retrieve_chunks")
    else:
        validate_embedding_vector(query_embedding, context="retrieve_chunks")
    
    validate_retrieval_parameters(
        top_k=k,
        score_threshold=score_threshold,
        min_return=min_k,
        context="retrieve_chunks"
    )
    
    validate_filters(filters, context="retrieve_chunks")
    
    if model_id is not None:
        validate_model_id(model_id, context="retrieve_chunks")
    
    if not USE_FAISS_SUBPROCESS and is_invalid_vector(query_embedding):
        raise ValueError("Cannot retrieve: embedding is invalid (zero vector).")
    
    if USE_FAISS_SUBPROCESS:
        # Subprocess mode: avoids PyTorch/FAISS segfaults on Mac/Intel
        from rag.dual_process_retriever import retrieve_chunks_dual_process
        # We need the original query string, not the embedding, for subprocess mode
        # (Assume query_embedding is actually the query string in this mode)
        return retrieve_chunks_dual_process(
            query_embedding, 
            model_id=model_id, 
            top_k=k, 
            score_threshold=score_threshold,
            filters=filters
        )
    else:
        from rag.retriever import query_index
        return query_index(
            query_embedding, 
            model_id=model_id, 
            top_k=k, 
            score_threshold=score_threshold,
            filters=filters
        )


# --- Filtering ---
def filter_chunks(chunks: List[Dict[str, Any]], filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Filter chunks by metadata filters.
    
    Args:
        chunks: List of chunk dictionaries
        filters: Optional metadata filters to apply
        
    Returns:
        Filtered list of chunks
    """
    if not filters:
        return chunks
    
    filtered = []
    for chunk in chunks:
        if all(chunk.get(k) == v for k, v in filters.items()):
            filtered.append(chunk)
    
    return filtered


# --- PromptBuilder Singleton ---
def get_prompt_builder() -> PromptBuilder:
    """
    Singleton loader for the PromptBuilder.
    """
    global _PROMPT_BUILDER
    if _PROMPT_BUILDER is None:
        with _PROMPT_BUILDER_LOCK:
            if _PROMPT_BUILDER is None:
                logger.info("Initializing PromptBuilder...")
                _PROMPT_BUILDER = PromptBuilder()
                logger.info(f"PromptBuilder initialized with {len(_PROMPT_BUILDER.list_templates())} templates")
    return _PROMPT_BUILDER


# --- Prompt Construction ---
def build_prompt(query: str, context: str, prompt_template: Optional[str] = None) -> str:
    """
    Build a prompt for GPT-3.5 using retrieved chunks and the user query.
    
    Args:
        query: The user's query string
        context: Formatted context from retrieved chunks
        prompt_template: Optional custom prompt template. If None, uses default template.
        
    Returns:
        Formatted prompt string
    """
    if prompt_template is None:
        prompt_template = "Answer the following question about Nobel Literature laureates: {query}\n\nContext: {context}"
    
    return prompt_template.format(query=query, context=context)


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
        logger.warning(f"Failed to build intent-aware prompt: {e}, falling back to basic prompt")
        # Fallback to basic prompt building
        context = format_chunks_for_prompt(chunks)
        return build_prompt(query, context)


# --- OpenAI Call ---
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
    """
    Infer the appropriate top_k value for retrieval based on query intent.
    Returns 15 if the query contains any broad/thematic keywords, else 5.
    """
    lowered = query.lower()
    if any(word in lowered for word in KEYWORDS_TRIGGER_EXPANSION):
        return 15
    return 5


# --- Main Orchestration ---
def query(
    query_string: str,
    model_id: str = "bge-large",
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Legacy entry point for the RAG pipeline (DEPRECATED).
    
    This function is deprecated and will be removed in a future version.
    It has known issues:
    1. Inconsistent score threshold handling
    2. Subprocess mode (USE_FAISS_SUBPROCESS=1) passes embeddings instead of query strings
    3. No support for min/max return counts
    
    Use answer_query() instead for a fully consistent and robust retrieval +
    prompting pipeline.
    
    Args:
        query_string: The user's query
        model_id: Model identifier (default: "bge-large")
        dry_run: If True, skip LLM call and return mock answer
        
    Returns:
        dict with answer and sources
        
    Deprecated:
        This function will be removed in a future version. Use answer_query() instead.
    """
    logger.warning(
        "query() is deprecated and will be removed in a future version. "
        "Use answer_query() instead for consistent score threshold handling "
        "and model-aware retrieval."
    )
    # For backward compatibility, delegate to answer_query but preserve dry_run behavior
    result = answer_query(query_string, model_id=model_id)
    if dry_run:
        # Modify the result to match the old dry_run behavior
        result["answer"] = "[DRY RUN] This is a simulated answer. Retrieved context:\n" + result.get("answer", "")
    return result


# --- QueryRouter Lazy Loader ---
_QUERY_ROUTER = None
def get_query_router():
    """
    Singleton loader for the QueryRouter.
    """
    global _QUERY_ROUTER
    if _QUERY_ROUTER is None:
        metadata = get_flattened_metadata()
        if metadata is None:
            logger.warning("Could not load laureate metadata. Factual queries will fall back to RAG.")
        elif not metadata:
            logger.warning("Laureate metadata file is empty. Factual queries will fall back to RAG.")
        else:
            logger.info(f"Loaded laureate metadata with {len(metadata)} records.")
        _QUERY_ROUTER = QueryRouter(metadata=metadata)
    return _QUERY_ROUTER


def answer_query(
    query_string: str,
    model_id: Optional[str] = None,
    score_threshold: float = 0.2,
    min_return: Optional[int] = None,
    max_return: Optional[int] = None
) -> Dict[str, Any]:
    """
    Canonical entry point for the RAG pipeline.
    
    This function provides a unified interface for all query types (factual,
    thematic, generative) with consistent score threshold handling and model-aware
    retrieval. It:
    1. Routes the query via QueryRouter
    2. Retrieves chunks using the appropriate retriever
    3. Applies score threshold filtering
    4. Formats the prompt and calls the LLM
    5. Compiles the final answer with sources
    
    Args:
        query_string: The user's query
        model_id: Optional model identifier used only to get the appropriate retriever.
                 If None, uses DEFAULT_MODEL_ID from model_config.
        score_threshold: Minimum similarity score for chunks (default: 0.2)
        min_return: Minimum number of chunks to return (query-type specific)
        max_return: Maximum number of chunks to return (query-type specific)
    
    Returns:
        dict with:
            answer_type: 'rag' or 'metadata'
            answer: The generated answer
            metadata_answer: Dict for metadata answers, None for RAG
            sources: List of source chunks with metadata
    """
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
        
        try:
            # Route the query
            route_result = get_query_router().route_query(query_string)
            
            if route_result.answer_type == "metadata":
                log_with_context(
                    logger,
                    logging.INFO,
                    "QueryEngine",
                    "Using metadata answer",
                    {"intent": route_result.intent}
                )
                return {
                    "answer_type": "metadata",
                    "answer": route_result.answer,
                    "metadata_answer": route_result.metadata_answer,
                    "sources": []  # No chunks for metadata answers
                }
            
            # Get the appropriate retriever based on intent
            if route_result.intent == "thematic":
                retriever = ThematicRetriever(model_id=model_id)
                # Thematic queries use a larger top_k (15) and need more diverse context
                # Use router's score_threshold if provided, otherwise use function parameter
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
                # Use router's score_threshold if provided, otherwise use function parameter
                effective_score_threshold = route_result.retrieval_config.score_threshold or score_threshold
                chunks = retriever.retrieve(
                    query_string,
                    top_k=route_result.retrieval_config.top_k,
                    filters=route_result.retrieval_config.filters,
                    score_threshold=effective_score_threshold,
                    min_return=min_return or 3,
                    max_return=max_return or 10
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
            
            log_with_context(
                logger,
                logging.INFO,
                "QueryEngine",
                "Calling LLM",
                {"prompt_length": len(prompt)}
            )
            
            response = call_openai(prompt)
            
            # Compile final answer
            result = {
                "answer_type": "rag",
                "answer": response["answer"],
                "metadata_answer": None,
                "sources": chunks
            }
            
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


# ... existing code ... 