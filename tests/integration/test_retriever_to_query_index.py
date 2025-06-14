"""
Integration test: retrieve_chunks → query_index
Ensures that retrieve_chunks calls query_index with correct arguments, propagates filters, and returns the expected output schema.
"""
import pytest
import numpy as np
from unittest.mock import patch
from rag.query_engine import retrieve_chunks

@pytest.fixture(autouse=True)
def force_inprocess(monkeypatch):
    # Force in-process mode so tests are consistent unless explicitly testing subprocess
    monkeypatch.setenv("NOBELLM_USE_FAISS_SUBPROCESS", "0")

@pytest.mark.integration
def test_retrieve_chunks_dual_process_path(monkeypatch):
    # Patch the module-level variable directly, not just the environment
    with patch("rag.query_engine.USE_FAISS_SUBPROCESS", True), \
         patch("rag.dual_process_retriever.retrieve_chunks_dual_process", return_value=[{"chunk_id": "dummy", "score": 0.9}]) as mock_dual:
        # In subprocess mode, we pass a query string, not an embedding
        query_string = "test query"
        result = retrieve_chunks(query_string, k=1, filters=None, score_threshold=0.2, min_k=1, model_id="bge-large")
        mock_dual.assert_called_once()
        assert result == [{"chunk_id": "dummy", "score": 0.9}]

@pytest.mark.integration
def test_retrieve_chunks_calls_query_index_with_correct_args():
    embedding = np.ones(1024, dtype=np.float32)
    mock_chunks = [
        {"chunk_id": "c1", "text": "A", "score": 0.9, "laureate": "Test", "year_awarded": 2000, "source_type": "lecture"},
        {"chunk_id": "c2", "text": "B", "score": 0.8, "laureate": "Test", "year_awarded": 2001, "source_type": "lecture"},
    ]
    with patch("rag.retriever.query_index", return_value=mock_chunks) as mock_query_index:
        result = retrieve_chunks(embedding, k=2, filters=None, score_threshold=0.0, min_k=2, model_id="bge-large")
        mock_query_index.assert_called_once()
        args, kwargs = mock_query_index.call_args
        assert kwargs["model_id"] == "bge-large"
        assert kwargs["top_k"] == 2
        assert kwargs["filters"] is None
        assert result == mock_chunks

@pytest.mark.integration
def test_retrieve_chunks_propagates_filters():
    embedding = np.ones(1024, dtype=np.float32)
    filters = {"country": "USA", "source_type": "nobel_lecture"}
    mock_chunks = [
        {"chunk_id": "c1", "text": "A", "score": 0.9, "country": "USA", "source_type": "nobel_lecture"},
    ]
    with patch("rag.retriever.query_index", return_value=mock_chunks) as mock_query_index:
        result = retrieve_chunks(embedding, k=1, filters=filters, score_threshold=0.0, min_k=1, model_id="bge-large")
        mock_query_index.assert_called_once()
        args, kwargs = mock_query_index.call_args
        assert kwargs["filters"] == filters
        assert result == mock_chunks

@pytest.mark.integration
def test_retrieve_chunks_handles_no_results():
    embedding = np.ones(1024, dtype=np.float32)
    with patch("rag.retriever.query_index", return_value=[]) as mock_query_index:
        result = retrieve_chunks(embedding, k=3, filters=None, score_threshold=0.0, min_k=3, model_id="bge-large")
        mock_query_index.assert_called_once()
        assert result == []

@pytest.mark.integration
def test_retrieve_chunks_output_schema():
    embedding = np.ones(1024, dtype=np.float32)
    mock_chunks = [
        {"chunk_id": "c1", "text": "A", "score": 0.9, "laureate": "Test", "year_awarded": 2000, "source_type": "lecture"},
    ]
    with patch("rag.retriever.query_index", return_value=mock_chunks):
        result = retrieve_chunks(embedding, k=1, filters=None, score_threshold=0.0, min_k=1, model_id="bge-large")
        required_fields = {"chunk_id", "text", "score", "laureate", "year_awarded", "source_type"}
        for chunk in result:
            assert required_fields.issubset(chunk.keys())

# Note: retrieve_chunks does not apply post-filtering by score_threshold. That logic is only in the main query function.
@pytest.mark.integration
def test_retrieve_chunks_respects_score_threshold():
    embedding = np.ones(1024, dtype=np.float32)
    mock_chunks = [
        {"chunk_id": "c1", "text": "High", "score": 0.95},
        {"chunk_id": "c2", "text": "Low", "score": 0.2},
    ]
    with patch("rag.retriever.query_index", return_value=mock_chunks):
        result = retrieve_chunks(
            embedding, k=2, filters=None, score_threshold=0.5, min_k=1, model_id="bge-large"
        )
        # retrieve_chunks does not filter by score_threshold; both chunks are returned
        assert result == mock_chunks
    # To test post-filtering, use the main query() function instead.

@pytest.mark.integration
def test_retrieve_chunks_fallbacks_to_min_k_when_needed():
    embedding = np.ones(1024, dtype=np.float32)
    mock_chunks = [
        {"chunk_id": "c1", "text": "Barely 1", "score": 0.3},
        {"chunk_id": "c2", "text": "Barely 2", "score": 0.25},
    ]
    with patch("rag.retriever.query_index", return_value=mock_chunks):
        result = retrieve_chunks(
            embedding, k=2, filters=None, score_threshold=0.9, min_k=2, model_id="bge-large"
        )
        # Even though no chunk passes score threshold, min_k fallback should return original
        assert len(result) == 2

@pytest.mark.integration
def test_retrieve_chunks_rejects_invalid_embedding():
    embedding = np.zeros(1024, dtype=np.float32)  # Invalid vector
    with pytest.raises(ValueError, match="zero vector"):
        retrieve_chunks(embedding, k=3, filters=None, score_threshold=0.0, min_k=3, model_id="bge-large") 