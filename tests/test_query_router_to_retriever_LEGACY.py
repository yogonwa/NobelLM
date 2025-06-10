"""
Integration test: QueryRouter → Retriever (via query_engine)
Ensures that retrieval config from QueryRouter is correctly propagated to the retriever, and that the retriever returns the expected number and schema of chunks. Patches at the query_engine level for realistic integration.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from rag.query_router import QueryRouter
from rag.query_engine import answer_query as query_engine_query

@pytest.fixture
def factual_query() -> str:
    """Fixture for a factual query that doesn't match metadata rules and should fall back to RAG.
    Uses a query about a specific detail that isn't in metadata but is clearly factual."""
    return "What was the exact time of day when Toni Morrison received her Nobel Prize?"

@pytest.fixture
def mock_embedding() -> np.ndarray:
    """Fixture for a fixed-size embedding (matching bge-large, 1024-dim)."""
    return np.ones(1024, dtype=np.float32)

@pytest.fixture
def mock_chunks() -> list:
    """Fixture for mock retrieval results (schema: chunk_id, text, laureate, year_awarded, source_type, score)."""
    return [
        {
            "chunk_id": f"c{i}",
            "text": f"Sample text {i}",
            "laureate": "Toni Morrison",
            "year_awarded": 1993,
            "source_type": "acceptance_speech",
            "score": 0.95 - 0.01 * i
        }
        for i in range(5)
    ]

@pytest.fixture
def thematic_query() -> str:
    """Fixture for a sample thematic user query."""
    return "What themes are present in Nobel lectures?"

@pytest.fixture
def mock_thematic_chunks() -> list:
    """Fixture for mock thematic retrieval results (15 chunks)."""
    return [
        {
            "chunk_id": f"t{i}",
            "text": f"Theme text {i}",
            "laureate": f"Laureate {i%3}",
            "year_awarded": 1950 + i,
            "source_type": "lecture",
            "score": 0.9 - 0.01 * i
        }
        for i in range(15)
    ]

def test_query_router_to_retriever_factual_fallback_to_rag(factual_query: str, mock_embedding: np.ndarray, mock_chunks: list) -> None:
    """
    Integration test: Verifies that factual queries which don't match metadata rules correctly fall back to RAG.
    Specifically checks that:
    1. The query goes through the retriever (not metadata handler)
    2. QueryRouter's retrieval config is properly passed to the retriever
    3. The retriever returns chunks with correct schema and count
    
    This is a key test case for the factual-to-RAG fallback path, ensuring that queries
    which can't be answered from metadata still get proper retrieval treatment.
    """
    # Patch embed_query and query_index at the query_engine level
    with patch("rag.query_engine.embed_query", return_value=mock_embedding):
        with patch("rag.retriever.query_index", return_value=mock_chunks) as mock_query_index:
            # Call the full pipeline with explicit model_id
            result = query_engine_query(factual_query, model_id="bge-large")
            # Check that query_index was called once and with correct parameters
            mock_query_index.assert_called_once()
            args, kwargs = mock_query_index.call_args
            assert kwargs["top_k"] == 5, f"Expected top_k=5, got {kwargs['top_k']}"
            assert kwargs["model_id"] == "bge-large", f"Expected model_id 'bge-large', got {kwargs['model_id']}"
            assert kwargs.get("min_score", 0.2) == 0.2, f"Expected min_score=0.2, got {kwargs.get('min_score')}"
            # No filters for factual by default
            # Check returned result
            assert "sources" in result, "Result missing 'sources' key"
            chunks = result["sources"]
            assert len(chunks) == 5, f"Expected 5 chunks, got {len(chunks)}"
            required_fields = {"chunk_id", "text_snippet", "laureate", "year_awarded", "source_type", "score"}
            for chunk in chunks:
                assert required_fields.issubset(chunk.keys()), f"Chunk missing required fields: {chunk}"
                assert isinstance(chunk["score"], float)
                assert isinstance(chunk["year_awarded"], int)
                assert "Sample text" in chunk["text_snippet"]

def test_query_router_to_retriever_thematic(thematic_query: str, mock_embedding: np.ndarray, mock_thematic_chunks: list) -> None:
    """
    Integration test: Thematic query, checks top_k=15, correct schema, and filter propagation.
    """
    with patch("rag.query_engine.embed_query", return_value=mock_embedding):
        with patch("rag.retriever.query_index", return_value=mock_thematic_chunks) as mock_query_index:
            result = query_engine_query(thematic_query, model_id="bge-large")
            mock_query_index.assert_called_once()
            args, kwargs = mock_query_index.call_args
            assert kwargs["top_k"] == 15, f"Expected top_k=15, got {kwargs['top_k']}"
            assert kwargs["model_id"] == "bge-large"
            chunks = result["sources"]
            assert len(chunks) == 15, f"Expected 15 chunks, got {len(chunks)}"
            required_fields = {"chunk_id", "text_snippet", "laureate", "year_awarded", "source_type", "score"}
            for chunk in chunks:
                assert required_fields.issubset(chunk.keys())
                assert isinstance(chunk["score"], float)
                assert isinstance(chunk["year_awarded"], int)
                assert "Theme text" in chunk["text_snippet"]

def test_filter_propagation_to_retriever(mock_embedding: np.ndarray, mock_chunks: list) -> None:
    """
    Integration test: Checks that filters are propagated from router to retriever and all returned chunks match the filter.
    """
    query = "What do female laureates say about freedom?"
    filter_dict = {"gender": "female"}
    # Patch router to inject filter, patch query_index to check filter
    with patch("rag.query_engine.embed_query", return_value=mock_embedding):
        with patch("rag.retriever.query_index", return_value=mock_chunks) as mock_query_index:
            result = query_engine_query(query, filters=filter_dict, model_id="bge-large")
            mock_query_index.assert_called_once()
            args, kwargs = mock_query_index.call_args
            assert kwargs["filters"] == filter_dict
            for chunk in result["sources"]:
                # Simulate that all returned chunks should match the filter (if present in chunk)
                if "gender" in chunk:
                    assert chunk["gender"] == "female"

def test_topk_override_behavior(mock_embedding: np.ndarray, mock_chunks: list) -> None:
    """
    Integration test: Checks that top_k override is respected by the retriever and pipeline returns correct number of results.
    Uses a factual query that doesn't match metadata rules to ensure it goes through retriever.
    """
    query = "What was the exact time of day when Toni Morrison received her Nobel Prize?"
    with patch("rag.query_engine.embed_query", return_value=mock_embedding):
        with patch("rag.retriever.query_index", return_value=mock_chunks[:3]) as mock_query_index:
            result = query_engine_query(query, k=3, model_id="bge-large")
            mock_query_index.assert_called_once()
            args, kwargs = mock_query_index.call_args
            assert kwargs["top_k"] == 3, f"Expected top_k=3, got {kwargs['top_k']}"
            assert len(result["sources"]) == 3, f"Expected 3 chunks, got {len(result['sources'])}"

def test_no_results_returns_empty_list(mock_embedding: np.ndarray) -> None:
    """
    Integration test: Checks that pipeline handles no results gracefully (empty list returned).
    """
    query = "Query with no results"
    with patch("rag.query_engine.embed_query", return_value=mock_embedding):
        with patch("rag.retriever.query_index", return_value=[]) as mock_query_index:
            result = query_engine_query(query, model_id="bge-large")
            mock_query_index.assert_called_once()
            assert result["sources"] == []

def test_invalid_embedding_handling(factual_query: str) -> None:
    """
    Integration test: Checks that invalid embedding (all zeros) is handled gracefully by the retriever.
    """
    invalid_embedding = np.zeros(1024, dtype=np.float32)
    with patch("rag.query_engine.embed_query", return_value=invalid_embedding):
        with patch("rag.retriever.query_index") as mock_query_index:
            # query_index should not be called if embedding is invalid
            result = query_engine_query(factual_query, model_id="bge-large")
            assert not mock_query_index.called, "query_index should not be called with invalid embedding"
            assert "answer" in result
            assert "No relevant information" in result["answer"] or "error" in result["answer"]

def test_multi_field_filter_propagation(mock_embedding: np.ndarray) -> None:
    """
    Integration test: Checks that multiple filters are propagated and all returned chunks match all filter fields (as far as output schema allows).
    """
    query = "What do USA Nobel lecture winners say about peace?"
    filter_dict = {"country": "USA", "source_type": "nobel_lecture"}
    mock_chunks = [
        {"chunk_id": "c1", "text": "A", "country": "USA", "source_type": "nobel_lecture", "score": 0.9},
        {"chunk_id": "c2", "text": "B", "country": "USA", "source_type": "nobel_lecture", "score": 0.8},
    ]
    with patch("rag.query_engine.embed_query", return_value=mock_embedding):
        with patch("rag.retriever.query_index", return_value=mock_chunks) as mock_query_index:
            result = query_engine_query(query, filters=filter_dict, model_id="bge-large")
            mock_query_index.assert_called_once()
            args, kwargs = mock_query_index.call_args
            assert kwargs["filters"] == filter_dict
            for source in result["sources"]:
                assert "chunk_id" in source
                assert "text_snippet" in source
                assert source["chunk_id"].startswith("c") 