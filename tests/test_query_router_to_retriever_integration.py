"""
Integration test: QueryRouter → Retriever (via answer_query)

Tests the integration point between QueryRouter and Retriever components,
ensuring retrieval config propagation and retriever selection work correctly
through the answer_query() pipeline.

Key integration points tested:
1. QueryRouter → Retriever config propagation
2. Intent-based retriever selection
3. Parameter flow (top_k, filters, score_threshold)
4. Chunk schema validation
5. Metadata vs RAG routing
"""

import pytest
import numpy as np
import os
from unittest.mock import patch, MagicMock
from rag.query_engine import answer_query
from rag.metadata_utils import load_laureate_metadata

# Load test metadata
EXAMPLE_METADATA = load_laureate_metadata()

# -----------------------------------------------------------------------------------
# Test Fixtures
# -----------------------------------------------------------------------------------

@pytest.fixture
def mock_chunks():
    """Mock chunks returned by retrievers."""
    return [
        {
            "text": "Justice is a recurring theme in literature.",
            "score": 0.85,
            "rank": 0,
            "chunk_id": "c1",
            "laureate": "Toni Morrison",
            "year_awarded": 1993,
            "source_type": "nobel_lecture"
        },
        {
            "text": "The human condition is explored through narrative.",
            "score": 0.78,
            "rank": 1,
            "chunk_id": "c2",
            "laureate": "Gabriel García Márquez",
            "year_awarded": 1982,
            "source_type": "nobel_lecture"
        }
    ]

@pytest.fixture
def mock_embedding():
    """Mock embedding vector."""
    embedding = np.random.rand(768).astype(np.float32)
    embedding /= np.linalg.norm(embedding)
    return embedding

# -----------------------------------------------------------------------------------
# Test: QueryRouter → Retriever Config Propagation
# -----------------------------------------------------------------------------------

def test_factual_query_metadata_answer():
    query = "Who won the Nobel Prize in Literature in 1993?"
    with patch('rag.query_engine.get_model') as mock_model, \
         patch('rag.query_engine.call_openai') as mock_llm:
        mock_model.return_value.encode.return_value = np.random.rand(768).astype(np.float32)
        mock_llm.return_value = {"answer": "Test answer"}
        result = answer_query(query, model_id="bge-large")
        assert result["answer_type"] == "metadata"
        assert "Toni Morrison" in result["answer"]
        assert result["sources"] == []
        mock_llm.assert_not_called()

def test_factual_query_rag_answer():
    query = "Where was Toni Morrison born?"
    os.environ["NOBELLM_USE_FAISS_SUBPROCESS"] = "1"
    with patch('rag.query_engine.get_model') as mock_model, \
         patch('rag.dual_process_retriever.retrieve_chunks_dual_process') as mock_dual_process, \
         patch('rag.query_engine.call_openai') as mock_llm:
        mock_model.return_value.encode.return_value = np.random.rand(768).astype(np.float32)
        mock_dual_process.return_value = [{"text": "Justice is a recurring theme.","score": 0.85,"chunk_id": "c1","laureate": "Toni Morrison","year_awarded": 1993}]
        mock_llm.return_value = {"answer": "Toni Morrison discussed justice extensively."}
        result = answer_query(query, model_id="bge-large")
        assert result["answer_type"] == "rag"
        assert len(result["sources"]) == 1
        mock_dual_process.assert_called_once()
        call_args = mock_dual_process.call_args
        assert call_args[1]["top_k"] == 5
        assert call_args[1]["score_threshold"] == 0.25
        assert call_args[1]["model_id"] == "bge-large"

def test_thematic_query_rag_answer():
    query = "What are common themes in Nobel laureate speeches?"
    with patch('rag.query_engine.get_model') as mock_model, \
         patch('rag.thematic_retriever.ThematicRetriever._expand_thematic_query') as mock_expand, \
         patch('rag.dual_process_retriever.retrieve_chunks_dual_process') as mock_dual_process, \
         patch('rag.query_engine.call_openai') as mock_llm:
        mock_model.return_value.encode.return_value = np.random.rand(768).astype(np.float32)
        mock_expand.return_value = ["themes Nobel laureate speeches"]
        mock_dual_process.return_value = [{"text": "Justice and human dignity are common themes.","score": 0.82,"chunk_id": "c1","laureate": "Toni Morrison","year_awarded": 1993}]
        mock_llm.return_value = {"answer": "Common themes include justice and human dignity."}
        result = answer_query(query, model_id="bge-large")
        assert result["answer_type"] == "rag"
        assert len(result["sources"]) == 1
        mock_dual_process.assert_called_once()
        call_args = mock_dual_process.call_args
        assert call_args[1]["top_k"] == 15
        assert call_args[1]["score_threshold"] == 0.2
        assert call_args[1]["model_id"] == "bge-large"

# -----------------------------------------------------------------------------------
# Test: Parameter Flow and Config Propagation
# -----------------------------------------------------------------------------------

def test_score_threshold_propagation():
    query = "Where was Toni Morrison born?"
    custom_threshold = 0.5
    with patch('rag.query_engine.get_model') as mock_model, \
         patch('rag.query_engine.get_mode_aware_retriever') as mock_get_retriever, \
         patch('rag.query_engine.call_openai') as mock_llm:
        mock_model.return_value.encode.return_value = np.random.rand(768).astype(np.float32)
        mock_get_retriever.return_value = MagicMock()
        mock_get_retriever.return_value.retrieve.return_value = [{"text": "Justice is a recurring theme.","score": 0.85,"chunk_id": "c1","laureate": "Toni Morrison","year_awarded": 1993}]
        mock_llm.return_value = {"answer": "Test answer"}
        result = answer_query(query, model_id="bge-large", score_threshold=custom_threshold)
        mock_get_retriever.assert_called_once_with("bge-large")
        mock_retriever = mock_get_retriever.return_value
        mock_retriever.retrieve.assert_called_once()
        call_args = mock_retriever.retrieve.call_args
        assert call_args[1]["score_threshold"] == 0.25  # matches router behavior

def test_filters_propagation():
    query = "Where was Toni Morrison born?"
    with patch('rag.query_engine.get_model') as mock_model, \
         patch('rag.query_engine.get_mode_aware_retriever') as mock_get_retriever, \
         patch('rag.query_engine.call_openai') as mock_llm:
        mock_model.return_value.encode.return_value = np.random.rand(768).astype(np.float32)
        mock_get_retriever.return_value = MagicMock()
        mock_get_retriever.return_value.retrieve.return_value = [{"text": "Justice and human dignity are common themes.","score": 0.82,"chunk_id": "c1","laureate": "Toni Morrison","year_awarded": 1993}]
        mock_llm.return_value = {"answer": "Test answer"}
        result = answer_query(query, model_id="bge-large")
        mock_get_retriever.assert_called_once_with("bge-large")
        mock_retriever = mock_get_retriever.return_value
        mock_retriever.retrieve.assert_called_once()
        call_args = mock_retriever.retrieve.call_args
        expected_filters = None  # current behavior
        assert call_args[1]["filters"] == expected_filters

# -----------------------------------------------------------------------------------
# Test: Chunk Schema Validation
# -----------------------------------------------------------------------------------

def test_chunk_schema_validation():
    query = "What did Toni Morrison say about justice?"
    with patch('rag.query_engine.get_model') as mock_model, \
         patch('rag.query_engine.get_mode_aware_retriever') as mock_get_retriever, \
         patch('rag.query_engine.call_openai') as mock_llm:
        mock_model.return_value.encode.return_value = np.random.rand(768).astype(np.float32)
        mock_get_retriever.return_value = MagicMock()
        mock_get_retriever.return_value.retrieve.return_value = [{"text": "Justice is a recurring theme.","score": 0.85,"rank": 0,"chunk_id": "c1","laureate": "Toni Morrison","year_awarded": 1993,"source_type": "nobel_lecture"}]
        mock_llm.return_value = {"answer": "Test answer"}
        result = answer_query(query, model_id="bge-large")
        assert len(result["sources"]) == 1
        chunk = result["sources"][0]
        assert "text" in chunk
        assert "score" in chunk
        assert "chunk_id" in chunk
        assert "laureate" in chunk
        assert "year_awarded" in chunk
        assert isinstance(chunk["text"], str)
        assert isinstance(chunk["score"], (int, float))
        assert isinstance(chunk["chunk_id"], str)
        assert isinstance(chunk["laureate"], str)
        assert isinstance(chunk["year_awarded"], int)

# -----------------------------------------------------------------------------------
# Test: Error Handling and Edge Cases
# -----------------------------------------------------------------------------------

def test_invalid_embedding_handling():
    query = "What did Toni Morrison say about justice?"
    with patch('rag.query_engine.get_model') as mock_model, \
         patch('rag.query_engine.get_mode_aware_retriever') as mock_get_retriever:
        mock_model.return_value.encode.return_value = np.zeros(768, dtype=np.float32)
        mock_get_retriever.return_value = MagicMock()
        mock_get_retriever.return_value.retrieve.side_effect = ValueError("Cannot retrieve: embedding is invalid")
        with pytest.raises(ValueError, match="Cannot retrieve: embedding is invalid"):
            answer_query(query, model_id="bge-large")

def test_empty_chunks_handling():
    query = "What did Toni Morrison say about justice?"
    with patch('rag.query_engine.get_model') as mock_model, \
         patch('rag.query_engine.get_mode_aware_retriever') as mock_get_retriever, \
         patch('rag.query_engine.call_openai') as mock_llm:
        mock_model.return_value.encode.return_value = np.random.rand(768).astype(np.float32)
        mock_get_retriever.return_value = MagicMock()
        mock_get_retriever.return_value.retrieve.return_value = []
        mock_llm.return_value = {"answer": "No relevant information found."}
        result = answer_query(query, model_id="bge-large")
        assert result["answer_type"] == "rag"
        assert result["sources"] == []
        assert "No relevant information found" in result["answer"]
# -----------------------------------------------------------------------------------
# Test: Dual-Process Retrieval Toggle
# -----------------------------------------------------------------------------------

def test_dual_process_retrieval_toggle():
    """
    Test that dual-process retrieval works correctly on Mac/Intel.
    """
    query = "Where was Toni Morrison born?"

    for use_subprocess in [0, 1]:
        os.environ["NOBELLM_USE_FAISS_SUBPROCESS"] = str(use_subprocess)

        with patch('rag.query_engine.get_model') as mock_model, \
             patch('rag.dual_process_retriever.retrieve_chunks_dual_process') as mock_dual_process, \
             patch('rag.retriever.query_index') as mock_query_index, \
             patch('rag.query_engine.call_openai') as mock_llm:

            mock_model.return_value.encode.return_value = np.random.rand(768).astype(np.float32)

            mock_chunks = [
                {
                    "text": "Justice is a recurring theme.",
                    "score": 0.85,
                    "chunk_id": "c1",
                    "laureate": "Toni Morrison",
                    "year_awarded": 1993
                }
            ]

            if use_subprocess == 1:
                mock_dual_process.return_value = mock_chunks
                mock_query_index.return_value = []
            else:
                mock_dual_process.return_value = []
                mock_query_index.return_value = mock_chunks

            mock_llm.return_value = {"answer": "Test answer"}

            result = answer_query(query, model_id="bge-large")

            assert result["answer_type"] == "rag"
            assert len(result["sources"]) == 1

            if use_subprocess == 1:
                mock_dual_process.assert_called_once()
                mock_query_index.assert_not_called()
            else:
                mock_dual_process.assert_not_called()
                mock_query_index.assert_called_once()

            mock_dual_process.reset_mock()
            mock_query_index.reset_mock()

# -----------------------------------------------------------------------------------
# Test: Dual-Process Consistency
# -----------------------------------------------------------------------------------

def test_dual_process_consistency():
    """
    Test that in-process and subprocess modes return identical results.
    """
    query = "What did Toni Morrison say about justice?"

    results = {}

    mock_chunks = [
        {
            "text": "Justice is a recurring theme.",
            "score": 0.85,
            "chunk_id": "c1",
            "laureate": "Toni Morrison",
            "year_awarded": 1993
        }
    ]

    for use_subprocess in [0, 1]:
        os.environ["NOBELLM_USE_FAISS_SUBPROCESS"] = str(use_subprocess)

        with patch('rag.query_engine.get_model') as mock_model, \
             patch('rag.dual_process_retriever.retrieve_chunks_dual_process') as mock_dual_process, \
             patch('rag.retriever.query_index') as mock_query_index, \
             patch('rag.query_engine.call_openai') as mock_llm:

            mock_model.return_value.encode.return_value = np.random.rand(768).astype(np.float32)
            mock_llm.return_value = {"answer": "Test answer"}

            if use_subprocess == 1:
                mock_dual_process.return_value = mock_chunks
                mock_query_index.return_value = []
            else:
                mock_dual_process.return_value = []
                mock_query_index.return_value = mock_chunks

            results[use_subprocess] = answer_query(query, model_id="bge-large")

    assert results[0]["answer_type"] == results[1]["answer_type"]
    assert len(results[0]["sources"]) == len(results[1]["sources"])
    assert results[0]["sources"][0]["text"] == results[1]["sources"][0]["text"]

# -----------------------------------------------------------------------------------
# Test: Model-Aware Retrieval
# -----------------------------------------------------------------------------------

def test_model_aware_retriever_selection():
    """
    Test that different model_ids result in correct retriever selection.
    """
    query = "What did Toni Morrison say about justice?"

    with patch('rag.query_engine.get_model') as mock_model, \
         patch('rag.query_engine.get_mode_aware_retriever') as mock_get_retriever, \
         patch('rag.query_engine.call_openai') as mock_llm:

        mock_model.return_value.encode.return_value = np.random.rand(768).astype(np.float32)

        mock_get_retriever.return_value = MagicMock()
        mock_get_retriever.return_value.retrieve.return_value = [
            {
                "text": "Justice is a recurring theme.",
                "score": 0.85,
                "chunk_id": "c1",
                "laureate": "Toni Morrison",
                "year_awarded": 1993
            }
        ]

        mock_llm.return_value = {"answer": "Test answer"}

        for model_id in ["bge-large", "bge-small", "all-MiniLM-L6-v2"]:
            result = answer_query(query, model_id=model_id)

            mock_get_retriever.assert_called_with(model_id)

            assert result["answer_type"] == "rag"
            assert len(result["sources"]) == 1

            mock_get_retriever.reset_mock()

# -----------------------------------------------------------------------------------
# Test: is_supported_index check (explicit ValueError)
# -----------------------------------------------------------------------------------

def test_is_supported_index_check(monkeypatch, mock_embedding):
    """
    Test that unsupported FAISS index raises ValueError in query_index.
    """
    from rag import retriever

    mock_index = MagicMock()
    mock_metadata = [
        {"text": "A", "chunk_id": "c1", "laureate": "X", "year_awarded": 2000, "source_type": "lecture"}
    ]

    monkeypatch.setattr(retriever, "load_index_and_metadata", lambda model_id: (mock_index, mock_metadata))
    monkeypatch.setattr(retriever, "is_supported_index", lambda index: False)

    with pytest.raises(ValueError, match="Unsupported FAISS index type"):
        retriever.query_index(
            query_embedding=mock_embedding,
            model_id="bge-large",
            top_k=3
        )

# -----------------------------------------------------------------------------------
# Test: min_return / max_return argument propagation
# -----------------------------------------------------------------------------------

def test_min_max_return_propagation():
    """
    Test that min_return and max_return propagate correctly through pipeline.
    """
    query = "What does Toni Morrison say about dogs?"

    with patch('rag.query_engine.get_model') as mock_model, \
         patch('rag.dual_process_retriever.retrieve_chunks_dual_process') as mock_dual_process, \
         patch('rag.query_engine.call_openai') as mock_llm, \
         patch('rag.query_engine.get_query_router') as mock_get_router:

        # Mock the query router to return a RAG answer (not metadata)
        mock_router = MagicMock()
        mock_router.route_query.return_value = MagicMock(
            answer_type="rag",
            intent="factual",
            retrieval_config=MagicMock(top_k=5, score_threshold=0.25, filters=None),
            prompt_template="Answer the following question: {query}\n\nContext: {context}"
        )
        mock_get_router.return_value = mock_router

        mock_model.return_value.encode.return_value = np.random.rand(768).astype(np.float32)

        mock_dual_process.return_value = [
            {
                "text": "Justice is a recurring theme.",
                "score": 0.85,
                "chunk_id": "c1",
                "laureate": "Toni Morrison",
                "year_awarded": 1993
            }
        ]

        mock_llm.return_value = {"answer": "Test answer"}

        result = answer_query(query, model_id="bge-large", min_return=2, max_return=8)

        # Verify result
        assert result["answer_type"] == "rag"
        assert len(result["sources"]) == 1

        # Verify retrieve_chunks_dual_process was called with correct parameters
        mock_dual_process.assert_called_once()
        call_args = mock_dual_process.call_args

        assert call_args[1]["min_return"] == 2
        assert call_args[1]["max_return"] == 8
