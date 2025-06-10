"""
Test failure cases and edge conditions for the NobelLM RAG pipeline.

This module tests how the pipeline handles various error conditions and edge cases,
ensuring graceful degradation and clear error messages.
"""

import os
import pytest
import numpy as np
import faiss
from typing import Dict, Any

from rag.query_engine import answer_query
from rag.retriever import query_index, is_supported_index
from rag.model_config import get_model_config
from rag.utils import filter_top_chunks

# Test fixtures
@pytest.fixture
def mock_ivf_index():
    """Create a mock IVF index for testing unsupported index types."""
    d = 384  # Standard embedding dimension
    quantizer = faiss.IndexFlatIP(d)
    index = faiss.IndexIVFFlat(quantizer, d, 10)  # 10 clusters
    index.train(np.random.rand(100, d).astype('float32'))
    return index

@pytest.fixture
def mock_chunks():
    """Create mock chunks with varying scores for testing filter_top_chunks."""
    return [
        {"chunk_id": f"chunk_{i}", "score": score, "text": f"Text {i}"}
        for i, score in enumerate([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05])
    ]

def test_empty_query():
    """Test handling of empty queries."""
    with pytest.raises(ValueError, match="Query string cannot be empty"):
        answer_query("")

def test_missing_index_file():
    """Test handling of missing FAISS index file."""
    # Temporarily rename index file to simulate missing file
    config = get_model_config()
    index_path = config["index_path"]
    backup_path = f"{index_path}.bak"
    
    try:
        if os.path.exists(index_path):
            os.rename(index_path, backup_path)
        
        with pytest.raises(FileNotFoundError, match="Index file not found"):
            answer_query("What do laureates say about justice?")
    finally:
        # Restore index file
        if os.path.exists(backup_path):
            os.rename(backup_path, index_path)

def test_zero_vector_handling():
    """Test handling of zero vectors in query_index."""
    zero_vector = np.zeros(384, dtype=np.float32)  # Standard embedding dimension
    
    with pytest.raises(ValueError, match="Invalid query embedding"):
        query_index(
            query_embedding=zero_vector,
            top_k=5,
            model_id="bge-large"
        )

def test_model_config_mismatch():
    """Test handling of mismatched model and index dimensions."""
    # Create a vector with wrong dimension
    wrong_dim_vector = np.random.rand(512).astype(np.float32)  # Wrong dimension
    
    with pytest.raises(ValueError, match="Model and index dimensions do not match"):
        query_index(
            query_embedding=wrong_dim_vector,
            top_k=5,
            model_id="bge-large"  # Expects 384 dimensions
        )

def test_unsupported_index_type(mock_ivf_index):
    """Test handling of unsupported index types (IVF, PQ, etc.)."""
    assert not is_supported_index(mock_ivf_index)
    
    # Create a mock query embedding
    query_embedding = np.random.rand(384).astype(np.float32)
    
    # Test that query_index raises ValueError for unsupported index
    with pytest.raises(ValueError, match="Index type not supported for metadata filtering"):
        # Mock the index loading to return our IVF index
        with pytest.MonkeyPatch.context() as m:
            m.setattr("faiss.read_index", lambda _: mock_ivf_index)
            query_index(
                query_embedding=query_embedding,
                top_k=5,
                filters={"source_type": "nobel_lecture"},
                model_id="bge-large"
            )

def test_score_threshold_edge_cases(mock_chunks):
    """Test filter_top_chunks with various edge cases."""
    # Test with no chunks
    assert filter_top_chunks([], score_threshold=0.2) == []
    
    # Test with all chunks below threshold
    filtered = filter_top_chunks(mock_chunks, score_threshold=0.95)
    assert len(filtered) == 0
    
    # Test with min_return fallback
    filtered = filter_top_chunks(
        mock_chunks,
        score_threshold=0.95,
        min_return=3
    )
    assert len(filtered) == 3
    assert all(chunk["score"] >= 0.9 for chunk in filtered)
    
    # Test with max_return limit
    filtered = filter_top_chunks(
        mock_chunks,
        score_threshold=0.2,
        max_return=3
    )
    assert len(filtered) == 3
    assert all(chunk["score"] >= 0.2 for chunk in filtered)
    
    # Test with both min_return and max_return
    filtered = filter_top_chunks(
        mock_chunks,
        score_threshold=0.95,
        min_return=2,
        max_return=3
    )
    assert len(filtered) == 2  # min_return takes precedence
    assert all(chunk["score"] >= 0.9 for chunk in filtered)

def test_large_query_handling():
    """Test handling of very large queries (>100KB)."""
    # Create a very large query string
    large_query = "x" * 150 * 1024  # 150KB
    
    # Should not raise an error, but should log a warning
    with pytest.LogCapture() as log:
        answer_query(large_query)
        assert "Query string is very large" in log.records[0].message

def test_invalid_score_handling(mock_chunks):
    """Test handling of chunks with invalid scores."""
    # Add a chunk with invalid score
    invalid_chunks = mock_chunks + [{"chunk_id": "invalid", "score": float('nan'), "text": "Invalid"}]
    
    # Should filter out invalid scores
    filtered = filter_top_chunks(invalid_chunks, score_threshold=0.2)
    assert len(filtered) == len(mock_chunks)
    assert all(not np.isnan(chunk["score"]) for chunk in filtered)
    
    # Test with negative scores
    negative_chunks = mock_chunks + [{"chunk_id": "negative", "score": -0.5, "text": "Negative"}]
    filtered = filter_top_chunks(negative_chunks, score_threshold=0.2)
    assert len(filtered) == len(mock_chunks)
    assert all(chunk["score"] >= 0 for chunk in filtered) 