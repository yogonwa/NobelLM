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


def retrieve_chunks(query_embedding: np.ndarray, k: int = 3, filters: Optional[Dict[str, Any]] = None, score_threshold: float = 0.25) -> List[Dict[str, Any]]:
    """
    Retrieve top-k most relevant chunks from the FAISS index, optionally filtered by metadata and score threshold.
    Returns a list of chunk dicts with metadata and similarity scores.
    """
    index, metadata = get_index_and_metadata()
    results = faiss_query(index, metadata, query_embedding, top_k=k, min_score=score_threshold)
    # Remove results with note (no strong matches)
    results = [r for r in results if "note" not in r]
    # Apply metadata filtering
    filtered = filter_chunks(results, filters)
    # Apply score threshold again in case
    filtered = [c for c in filtered if c.get("score", 0) >= score_threshold]
    return filtered


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
def call_openai(prompt: str) -> str:
    """
    Call OpenAI's ChatCompletion endpoint using GPT-3.5. Returns the model's answer as a string.
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
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for Nobel Prize literature research."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=512,
        )
        answer = response.choices[0].message.content.strip()
        return answer
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        return f"[OpenAI API error] {e}"


# --- Main Orchestration ---
def query(
    query_string: str,
    filters: Optional[Dict[str, Any]] = None,
    dry_run: bool = False,
    k: int = 3,
    score_threshold: float = 0.25
) -> Dict[str, Any]:
    """
    Orchestrate the query pipeline: embed, retrieve, filter, prompt, and answer.
    Returns a dict with 'answer' and 'sources'.
    """
    logger.info(f"Received query: {query_string} | Filters: {filters} | Dry run: {dry_run}")
    try:
        query_emb = embed_query(query_string)
        chunks = retrieve_chunks(query_emb, k=k, filters=filters, score_threshold=score_threshold)
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
        if dry_run:
            logger.info("Dry run mode: returning dummy answer.")
            return {
                "answer": "[DRY RUN] This is a simulated answer. Retrieved context:\n" + prompt,
                "sources": [make_source(chunk) for chunk in chunks]
            }
        answer = call_openai(prompt)
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