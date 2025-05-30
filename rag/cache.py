import streamlit as st
from embeddings.build_index import load_index
from rag.metadata_utils import load_laureate_metadata
from sentence_transformers import SentenceTransformer
from typing import Tuple, List, Dict, Any

@st.cache_resource
def get_faiss_index_and_metadata() -> Tuple[object, List[Dict[str, Any]]]:
    """
    Load and cache the FAISS index and chunk metadata for fast retrieval.
    Returns:
        (index, chunk_metadata): Tuple of FAISS index object and list of chunk metadata dicts.
    """
    return load_index("data/faiss_index/")

@st.cache_resource
def get_flattened_metadata() -> List[Dict[str, Any]]:
    """
    Load and cache the flattened laureate metadata from the canonical JSON file.
    Returns:
        List of laureate metadata dicts.
    """
    return load_laureate_metadata("data/nobel_literature.json")

@st.cache_resource
def get_model() -> SentenceTransformer:
    """
    Load and cache the sentence-transformers model for embedding queries.
    Returns:
        SentenceTransformer model instance.
    """
    return SentenceTransformer("all-MiniLM-L6-v2") 