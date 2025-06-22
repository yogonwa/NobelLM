import streamlit as st
from rag.metadata_utils import load_laureate_metadata
from sentence_transformers import SentenceTransformer
from typing import Tuple, List, Dict, Any
from rag.model_config import get_model_config, DEFAULT_MODEL_ID
import os
import json
import faiss

@st.cache_resource
def get_faiss_index_and_metadata(model_id: str = None) -> Tuple[object, List[Dict[str, Any]]]:
    """
    Load and cache the FAISS index and chunk metadata for fast retrieval for the specified model.
    Returns:
        (index, chunk_metadata): Tuple of FAISS index object and list of chunk metadata dicts.
    """
    model_id = model_id or DEFAULT_MODEL_ID
    config = get_model_config(model_id)
    index_path = config["index_path"]
    metadata_path = config["metadata_path"]

    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Index file not found: {index_path}")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    index = faiss.read_index(index_path)
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = [json.loads(line) for line in f]

    return index, metadata

@st.cache_resource
def get_flattened_metadata() -> List[Dict[str, Any]]:
    """
    Load and cache the flattened laureate metadata from the canonical JSON file.
    Returns:
        List of laureate metadata dicts.
    """
    return load_laureate_metadata("data/nobel_literature.json")

@st.cache_resource
def get_model(model_id: str = None) -> SentenceTransformer:
    """
    Load and cache the sentence-transformers model for embedding queries for the specified model.
    Returns:
        SentenceTransformer model instance.
    """
    config = get_model_config(model_id)
    return SentenceTransformer(config["model_name"]) 