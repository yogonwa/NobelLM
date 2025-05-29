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
from embeddings.build_index import load_index, query_index as faiss_query
import threading
import dotenv
from utils.cost_logger import log_cost_event
try:
    import tiktoken
except ImportError:
    tiktoken = None
from rag.query_router import QueryRouter
import json
from rag.metadata_utils import flatten_laureate_metadata, load_laureate_metadata

dotenv.load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

__all__ = ["query"]

_MODEL_NAME = 'all-MiniLM-L6-v2'
_MODEL = None
_MODEL_LOCK = threading.Lock()
_INDEX = None
_METADATA = None
_INDEX_LOCK = threading.Lock()

KEYWORDS_TRIGGER_EXPANSION = [
    "theme", "themes", "pattern", "patterns", "typical", "common",
    "most", "across", "often", "generally", "usually", "style", "styles"
]

def get_model() -> SentenceTransformer:
    """
    Singleton loader for the MiniLM embedding model.
    """
    global _MODEL
    if _MODEL is None:
        with _MODEL_LOCK:
            if _MODEL is None:
                logger.info(f"Loading embedding model '{_MODEL_NAME}'...")
                _MODEL = SentenceTransformer(_MODEL_NAME)
    return _MODEL


def get_index_and_metadata(index_dir: str = "data/faiss_index/"):
    """
    Singleton loader for the FAISS index and chunk metadata.
    """
    global _INDEX, _METADATA
    if _INDEX is None or _METADATA is None:
        with _INDEX_LOCK:
            if _INDEX is None or _METADATA is None:
                logger.info(f"Loading FAISS index and metadata from '{index_dir}'...")
                _INDEX, _METADATA = load_index(index_dir)
    return _INDEX, _METADATA


def embed_query(query: str) -> np.ndarray:
    """
    Embed the user query using the same MiniLM model as document chunks.
    Returns a numpy array embedding.
    """
    model = get_model()
    emb = model.encode(query, show_progress_bar=False, normalize_embeddings=True)
    return np.array(emb, dtype=np.float32)


def retrieve_chunks(
    query_embedding: np.ndarray,
    k: int = 3,
    filters: Optional[Dict[str, Any]] = None,
    score_threshold: float = 0.25,
    min_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Retrieve top-k most relevant chunks from the FAISS index, with conditional filtering:
    - For thematic queries (k > min_k): ignore score_threshold, return top_k.
    - For factual queries (k == min_k): apply score_threshold, but if fewer than min_k pass, return top min_k regardless of score.
    Returns a list of chunk dicts with metadata and similarity scores.
    """
    index, metadata = get_index_and_metadata()
    results = faiss_query(index, metadata, query_embedding, top_k=k, min_score=0.0)  # always get top_k, ignore min_score here
    # Remove results with note (no strong matches)
    results = [r for r in results if "note" not in r]
    # Apply metadata filtering
    filtered = filter_chunks(results, filters)
    # Thematic: k > min_k, return top_k
    if k > min_k:
        return filtered[:k]
    # Factual: k == min_k, apply score threshold
    passing = [c for c in filtered if c.get("score", 0) >= score_threshold]
    if len(passing) >= min_k:
        return passing[:min_k]
    # Fallback: return top min_k regardless of score
    return filtered[:min_k]


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
    """
    context = "\n\n".join(chunk["text"] for chunk in chunks)
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
    score_threshold: float = 0.25
) -> Dict[str, Any]:
    """
    Orchestrate the query pipeline: embed, retrieve, filter, prompt, and answer.
    If k is not provided, it is inferred from the query intent using infer_top_k_from_query().
    Returns a dict with 'answer' and 'sources'.
    """
    logger.info(f"Received query: {query_string} | Filters: {filters} | Dry run: {dry_run}")
    try:
        top_k = k if k is not None else infer_top_k_from_query(query_string)
        logger.info(f"Using top_k={top_k} for query.")
        query_emb = embed_query(query_string)
        # Always retrieve top_k chunks, no score filtering at this stage
        chunks = retrieve_chunks(query_emb, k=top_k, filters=filters, score_threshold=0.0, min_k=5)
        # Thematic: if top_k > 10, return top_k by rank (no score threshold)
        if top_k > 10:
            chunks = chunks[:top_k]
        else:
            # Factual: apply score threshold, ensure at least min_return=5
            chunks = filter_top_chunks(chunks, score_threshold=score_threshold, min_return=5)
        if not chunks:
            logger.warning("No relevant chunks found for query.")
            return {
                "answer": "No relevant information found in the corpus.",
                "sources": []
            }
        prompt = build_prompt(chunks, query_string)
        def make_source(chunk):
            snippet = " ".join(chunk["text"].split()[:15]) + ("..." if len(chunk["text"].split()) > 15 else "")
            return {
                k: v for k, v in chunk.items() if k in ("laureate", "year_awarded", "source_type", "score", "chunk_id")
            } | {"text_snippet": snippet}
        chunk_count = len(chunks)
        model = "gpt-3.5-turbo"
        if dry_run:
            logger.info("Dry run mode: returning dummy answer.")
            # Estimate prompt tokens if tiktoken is available
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
                extra={"dry_run": True}
            )
            return {
                "answer": "[DRY RUN] This is a simulated answer. Retrieved context:\n" + prompt,
                "sources": [make_source(chunk) for chunk in chunks]
            }
        # Real OpenAI call
        # Estimate prompt tokens before call
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
        # If OpenAI usage is available, use it; else fallback to estimate
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
            extra={"dry_run": False}
        )
        return {
            "answer": answer,
            "sources": [make_source(chunk) for chunk in chunks]
        }
    except Exception as e:
        logger.error(f"Query engine failed: {e}")
        return {
            "answer": f"An error occurred: {e}",
            "sources": []
        }


# --- QueryRouter Lazy Loader ---
_QUERY_ROUTER = None
def get_query_router():
    global _QUERY_ROUTER
    if _QUERY_ROUTER is None:
        metadata = load_laureate_metadata()
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
    # Otherwise, run RAG pipeline as before
    # (You may want to refactor this logic into a function)
    # --- RAG retrieval ---
    # Use retrieval_config from route_result
    retrieval_config = route_result.retrieval_config
    query_emb = embed_query(query_string)
    chunks = retrieve_chunks(
        query_emb,
        k=retrieval_config.top_k,
        filters=retrieval_config.filters,
        score_threshold=retrieval_config.score_threshold or 0.0,
        min_k=5
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