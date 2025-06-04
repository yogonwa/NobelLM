"""
Query Engine for Nobel Laureate Speech Explorer

This module provides a modular, extensible, and testable interface for querying the Nobel Literature corpus using retrieval-augmented generation (RAG).

Features:
- Embeds user queries using MiniLM
- Retrieves top-k relevant chunks from FAISS index
- Supports metadata filtering (e.g., by country, source_type)
- Constructs prompts for GPT-3.5
- Calls OpenAI API (with dry run mode)
- Returns answer and source metadata

Author: NobelLM Team
"""
import os
import logging
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
import json
from rag.metadata_utils import flatten_laureate_metadata
from rag.thematic_retriever import ThematicRetriever
from rag.utils import format_chunks_for_prompt
from rag.cache import get_faiss_index_and_metadata, get_flattened_metadata, get_model
from rag.model_config import get_model_config, DEFAULT_MODEL_ID
from rag.retriever import query_index, load_index_and_metadata, is_invalid_vector, get_mode_aware_retriever, BaseRetriever

dotenv.load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USE_FAISS_SUBPROCESS = os.getenv("NOBELLM_USE_FAISS_SUBPROCESS", "0") == "1"

__all__ = ["query"]

_MODEL = None
_MODEL_LOCK = threading.Lock()
_INDEX = None
_METADATA = None
_INDEX_LOCK = threading.Lock()

KEYWORDS_TRIGGER_EXPANSION = [
    "theme", "themes", "pattern", "patterns", "typical", "common",
    "most", "across", "often", "generally", "usually", "style", "styles"
]

def get_model(model_id: str = None) -> SentenceTransformer:
    """
    Singleton loader for the embedding model specified by model_id.
    Uses centralized config for model name.
    """
    global _MODEL
    if _MODEL is None:
        with _MODEL_LOCK:
            if _MODEL is None:
                config = get_model_config(model_id)
                logger.info(f"Loading embedding model '{config['model_name']}'...")
                _MODEL = SentenceTransformer(config['model_name'])
    return _MODEL


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
                _INDEX, _METADATA = load_index_and_metadata(model_id)
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
    score_threshold: float = 0.25,
    min_k: int = 3,
    model_id: str = None
) -> List[Dict[str, Any]]:
    """
    Retrieve top-k most relevant chunks from the FAISS index for the specified model.
    Uses subprocess mode if USE_FAISS_SUBPROCESS is set (for Mac/Intel dev), else in-process (for Linux/prod).
    Passes filters to query_index for pre-retrieval metadata filtering.
    """
    if is_invalid_vector(query_embedding):
        raise ValueError("Cannot retrieve: embedding is invalid (zero vector).")
    if USE_FAISS_SUBPROCESS:
        # Subprocess mode: avoids PyTorch/FAISS segfaults on Mac/Intel
        from rag.dual_process_retriever import retrieve_chunks_dual_process
        # We need the original query string, not the embedding, for subprocess mode
        # (Assume query_embedding is actually the query string in this mode)
        return retrieve_chunks_dual_process(query_embedding, model_id=model_id, top_k=k, filters=filters)
    else:
        from rag.retriever import query_index
        return query_index(query_embedding, model_id=model_id, top_k=k, filters=filters)


# --- Filtering ---
def filter_chunks(chunks: List[Dict[str, Any]], filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Filter chunks by metadata fields (e.g., country, source_type).
    Returns a filtered list of chunks.
    """
    if not filters:
        return chunks
    filtered = []
    for chunk in chunks:
        match = True
        for key, value in filters.items():
            if chunk.get(key) != value:
                match = False
                break
        if match:
            filtered.append(chunk)
    return filtered


def filter_top_chunks(chunks, score_threshold=0.25, min_return=3):
    """
    Filter chunks by score threshold, but always return at least min_return chunks (by rank).
    """
    passing = [c for c in chunks if c.get("score", 0) >= score_threshold]
    if len(passing) >= min_return:
        return passing[:min_return]
    return chunks[:min_return]


# --- Prompt Construction ---
def build_prompt(chunks: List[Dict[str, Any]], query: str) -> str:
    """
    Build a prompt for GPT-3.5 using the retrieved chunks and user query.
    Includes chunk metadata for all query types.
    """
    context = format_chunks_for_prompt(chunks)
    prompt = (
        "Answer the question using only the content below. If the answer is not found, say so.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}\n"
        "Answer:"
    )
    return prompt


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
    filters: Optional[Dict[str, Any]] = None,
    dry_run: bool = False,
    k: Optional[int] = None,
    score_threshold: float = 0.25,
    model_id: str = None
) -> Dict[str, Any]:
    """
    Orchestrate the query pipeline: embed, retrieve, filter, prompt, and answer.
    Model-aware: uses the embedding model, index, and metadata for the specified model_id.
    Returns a dict with 'answer' and 'sources'.
    """
    logger.info(f"Received query: {query_string} | Filters: {filters} | Dry run: {dry_run} | Model: {model_id or DEFAULT_MODEL_ID}")
    try:
        # Use QueryRouter to classify and get template
        router = get_query_router()
        route_result = router.route_query(query_string)
        intent = route_result.intent
        prompt_template = route_result.prompt_template
        retrieval_config = route_result.retrieval_config
        # Factual: try metadata first
        if route_result.answer_type == "metadata":
            return {
                "answer": route_result.metadata_answer["answer"],
                "sources": [],
                "answer_type": "metadata",
                "metadata_answer": route_result.metadata_answer
            }
        # RAG retrieval
        top_k = k if k is not None else retrieval_config.top_k
        model_id = model_id or DEFAULT_MODEL_ID
        retriever = get_mode_aware_retriever(model_id)
        query_emb = embed_query(query_string, model_id)
        if is_invalid_vector(query_emb):
            raise ValueError("Invalid query vector: embedding appears to be all zeros.")
        chunks = retriever.retrieve(
            query_string,
            top_k=top_k,
            filters=filters or retrieval_config.filters
        )
        if not chunks:
            logger.warning("No relevant chunks found for query.")
            return {
                "answer": "No relevant information found in the corpus.",
                "sources": [],
                "answer_type": "rag",
                "metadata_answer": None
            }
        # --- Intent-aware prompt construction ---
        if intent == "factual":
            context = format_factual_context(chunks)
        else:
            from rag.utils import format_chunks_for_prompt
            context = format_chunks_for_prompt(chunks)
        prompt = prompt_template.format(context=context, query=query_string)
        def make_source(chunk):
            snippet = " ".join(chunk["text"].split()[:15]) + ("..." if len(chunk["text"].split()) > 15 else "")
            return {
                k: v for k, v in chunk.items() if k in ("laureate", "year_awarded", "source_type", "score", "chunk_id")
            } | {"text_snippet": snippet}
        chunk_count = len(chunks)
        model = "gpt-3.5-turbo"
        if dry_run:
            logger.info("Dry run mode: returning dummy answer.")
            prompt_tokens = 100
            completion_tokens = 20
            if tiktoken:
                try:
                    enc = tiktoken.encoding_for_model(model)
                    prompt_tokens = len(enc.encode(prompt))
                except Exception:
                    pass
            estimated_cost_usd = 0.0015 * (prompt_tokens + completion_tokens) / 1000
            log_cost_event(
                user_query=query_string,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                chunk_count=chunk_count,
                estimated_cost_usd=estimated_cost_usd,
                extra={"dry_run": True, "model_id": model_id}
            )
            return {
                "answer": "[DRY RUN] This is a simulated answer. Retrieved context:\n" + prompt,
                "sources": [make_source(chunk) for chunk in chunks],
                "answer_type": "rag",
                "metadata_answer": None
            }
        prompt_tokens = 0
        if tiktoken:
            try:
                enc = tiktoken.encoding_for_model(model)
                prompt_tokens = len(enc.encode(prompt))
            except Exception:
                pass
        result = call_openai(prompt, model=model)
        answer = result["answer"]
        completion_tokens = result.get("completion_tokens")
        if completion_tokens is None:
            completion_tokens = 20
        if prompt_tokens == 0:
            prompt_tokens = 100
        estimated_cost_usd = 0.0015 * (prompt_tokens + completion_tokens) / 1000
        log_cost_event(
            user_query=query_string,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            chunk_count=chunk_count,
            estimated_cost_usd=estimated_cost_usd,
            extra={"dry_run": False, "model_id": model_id}
        )
        logger.info(f"[RAG][ShapeCheck] Query intent: {intent}")
        logger.info(f"[RAG][ShapeCheck] Number of chunks returned: {len(chunks)}")
        return {
            "answer": answer,
            "sources": [make_source(chunk) for chunk in chunks],
            "answer_type": "rag",
            "metadata_answer": None
        }
    except Exception as e:
        logger.error(f"Query engine failed: {e}")
        return {
            "answer": f"An error occurred: {e}",
            "sources": [],
            "answer_type": "rag",
            "metadata_answer": None
        }


# --- QueryRouter Lazy Loader ---
_QUERY_ROUTER = None
def get_query_router():
    global _QUERY_ROUTER
    if _QUERY_ROUTER is None:
        metadata = get_flattened_metadata()
        if metadata is None:
            logger.warning("Laureate metadata file not found or could not be loaded. Factual queries will fall back to RAG.")
        elif not metadata:
            logger.warning("Laureate metadata file is empty. Factual queries will fall back to RAG.")
        else:
            logger.info(f"Loaded laureate metadata with {len(metadata)} records.")
        _QUERY_ROUTER = QueryRouter(metadata=metadata)
    return _QUERY_ROUTER


def answer_query(query_string: str) -> dict:
    """
    Unified entry point for the frontend. Routes query via QueryRouter.
    Returns a dict with 'answer_type', 'answer', 'metadata_answer', and 'sources'.
    """
    # Route the query
    route_result = get_query_router().route_query(query_string)
    if route_result.answer_type == "metadata":
        # Direct factual answer from metadata
        return {
            "answer_type": "metadata",
            "answer": route_result.metadata_answer["answer"],
            "metadata_answer": route_result.metadata_answer,
            "sources": []
        }
    # --- Modular Thematic Retrieval ---
    retrieval_config = route_result.retrieval_config
    if route_result.intent == "thematic":
        logger.info(f"[RAG][Thematic] Calling ThematicRetriever with expanded terms: {route_result.logs.get('thematic_expanded_terms', 'N/A')}")
        thematic_retriever = ThematicRetriever(
            retriever=get_mode_aware_retriever(model_id)
        )
        chunks = thematic_retriever.retrieve(query_string, top_k=retrieval_config.top_k, filters=retrieval_config.filters)
        logger.info(f"[RAG][Thematic] Final unique chunks returned: {len(chunks)}")
        logger.info(f"[RAG][Thematic] Final unique chunk IDs: {[c.get('chunk_id') for c in chunks]}")
    else:
        # Factual/generative: use retriever directly
        chunks = get_mode_aware_retriever(model_id).retrieve(
            query_string,
            top_k=retrieval_config.top_k,
            filters=retrieval_config.filters
        )
    if not chunks:
        return {
            "answer_type": "rag",
            "answer": "No relevant information found in the corpus.",
            "metadata_answer": None,
            "sources": []
        }
    prompt = build_prompt(chunks, query_string)
    result = call_openai(prompt, model="gpt-3.5-turbo")
    answer = result["answer"]
    def make_source(chunk):
        snippet = " ".join(chunk["text"].split()[:15]) + ("..." if len(chunk["text"].split()) > 15 else "")
        return {
            k: v for k, v in chunk.items() if k in ("laureate", "year_awarded", "source_type", "score", "chunk_id")
        } | {"text_snippet": snippet}
    return {
        "answer_type": "rag",
        "answer": answer,
        "metadata_answer": None,
        "sources": [make_source(chunk) for chunk in chunks]
    }


# ... existing code ... 