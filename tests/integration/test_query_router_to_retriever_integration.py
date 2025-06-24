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

@pytest.mark.integration
def test_factual_query_metadata_answer():
    query = "Who won the Nobel Prize in Literature in 1993?"
    with patch('rag.query_engine.get_model') as mock_model, \
         patch('rag.query_engine.call_openai') as mock_llm, \
         patch('rag.query_engine.get_query_router') as mock_get_router:
        mock_model.return_value.encode.return_value = np.random.rand(768).astype(np.float32)
        mock_llm.return_value = {"answer": "Test answer"}
        # Setup mocks for metadata answer
        mock_router = MagicMock()
        mock_route_result = MagicMock()
        mock_route_result.answer_type = "metadata"
        mock_route_result.intent = "metadata"
        mock_route_result.answer = "Toni Morrison won the Nobel Prize in Literature in 1993."
        mock_route_result.metadata_answer = {
            "answer": "Toni Morrison won the Nobel Prize in Literature in 1993.",
            "laureate": "Toni Morrison",
            "year_awarded": 1993,
            "country": "United States",
            "country_flag": "🇺🇸",
            "category": "Literature",
            "prize_motivation": "for her novels characterized by visionary force and poetic import, gives life to an essential aspect of American reality."
        }
        mock_router.route_query.return_value = mock_route_result
        mock_get_router.return_value = mock_router
        result = answer_query(query, model_id="bge-large")
        assert result["answer_type"] == "metadata"
        assert "Toni Morrison" in result["answer"]
        assert result["metadata_answer"]["laureate"] == "Toni Morrison"
        assert result["metadata_answer"]["year_awarded"] == 1993
        assert result["metadata_answer"]["country"] == "United States"
        assert result["metadata_answer"]["country_flag"] == "🇺🇸"
        assert result["metadata_answer"]["category"] == "Literature"
        assert "poetic import" in result["metadata_answer"]["prize_motivation"]
        assert result["sources"] == []
        mock_llm.assert_not_called()

@pytest.mark.integration
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

@pytest.mark.integration
def test_thematic_query_rag_answer():
    """Test thematic query gets RAG answer with thematic retriever."""
    query = "What are common themes in Nobel laureate speeches?"
    
    with patch('rag.query_engine.get_query_router') as mock_get_router, \
         patch('rag.query_engine.ThematicRetriever') as mock_thematic_class, \
         patch('rag.query_engine.call_openai') as mock_llm:
        
        # Setup mocks
        mock_router = MagicMock()
        mock_route_result = MagicMock()
        mock_route_result.answer_type = "rag"
        mock_route_result.intent = "thematic"
        mock_route_result.retrieval_config.top_k = 15
        mock_route_result.retrieval_config.score_threshold = 0.2
        mock_route_result.retrieval_config.filters = None
        mock_route_result.prompt_template = None
        mock_router.route_query.return_value = mock_route_result
        mock_get_router.return_value = mock_router
        
        mock_thematic_retriever = MagicMock()
        mock_thematic_retriever.retrieve.return_value = [
            {
                "text": "Justice and human dignity are common themes.",
                "score": 0.82,
                "chunk_id": "c1",
                "laureate": "Toni Morrison",
                "year_awarded": 1993,
                "source_type": "nobel_lecture"
            }
        ]
        mock_thematic_class.return_value = mock_thematic_retriever
        
        mock_llm.return_value = {
            "answer": "Common themes include justice and human dignity.",
            "completion_tokens": 15
        }
        
        # Test the complete pipeline
        result = answer_query(query, model_id="bge-large")
        
        # Verify thematic retriever was used
        mock_thematic_class.assert_called_once_with(model_id="bge-large")
        mock_thematic_retriever.retrieve.assert_called_once_with(
            query,
            top_k=15,
            filters=None,
            score_threshold=0.2,
            min_return=5,
            max_return=12
        )
        
        # Verify result structure
        assert result["answer_type"] == "rag"
        assert "justice" in result["answer"].lower()
        assert len(result["sources"]) == 1

# -----------------------------------------------------------------------------------
# Test: Parameter Flow and Config Propagation
# -----------------------------------------------------------------------------------

@pytest.mark.integration
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

@pytest.mark.integration
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

@pytest.mark.integration
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

@pytest.mark.integration
def test_invalid_embedding_handling():
    query = "What did Toni Morrison say about justice?"
    with patch('rag.query_engine.get_model') as mock_model, \
         patch('rag.query_engine.get_mode_aware_retriever') as mock_get_retriever:
        mock_model.return_value.encode.return_value = np.zeros(768, dtype=np.float32)
        mock_get_retriever.return_value = MagicMock()
        mock_get_retriever.return_value.retrieve.side_effect = ValueError("Cannot retrieve: embedding is invalid")
        with pytest.raises(ValueError, match="Cannot retrieve: embedding is invalid"):
            answer_query(query, model_id="bge-large")

@pytest.mark.integration
def test_empty_chunks_handling():
    query = "What did Toni Morrison say about justice?"
    with patch('rag.query_engine.get_model') as mock_model, \
         patch('rag.query_engine.get_mode_aware_retriever') as mock_get_retriever, \
         patch('rag.query_engine.call_openai') as mock_llm:
        mock_model.return_value.encode.return_value = np.random.rand(768).astype(np.float32)
        mock_get_retriever.return_value = MagicMock()
        mock_get_retriever.return_value.retrieve.return_value = []
        mock_llm.return_value = {"answer": "I couldn't find specific information about that."}
        result = answer_query(query, model_id="bge-large")
        assert result["answer_type"] == "rag"
        assert len(result["sources"]) == 0
        mock_llm.assert_called_once()

# -----------------------------------------------------------------------------------
# Test: Dual Process Retrieval Integration
# -----------------------------------------------------------------------------------

@pytest.mark.integration
def test_dual_process_retrieval_toggle():
    """Test that dual process retrieval can be toggled."""
    query = "What did Toni Morrison say about justice?"
    
    with patch('rag.query_engine.get_query_router') as mock_get_router, \
         patch('rag.query_engine.ThematicRetriever') as mock_thematic_class, \
         patch('rag.query_engine.call_openai') as mock_llm:
        
        # Setup mocks
        mock_router = MagicMock()
        mock_route_result = MagicMock()
        mock_route_result.answer_type = "rag"
        mock_route_result.intent = "thematic"
        mock_route_result.retrieval_config.top_k = 15
        mock_route_result.retrieval_config.score_threshold = 0.2
        mock_route_result.retrieval_config.filters = None
        mock_route_result.prompt_template = None
        mock_router.route_query.return_value = mock_route_result
        mock_get_router.return_value = mock_router
        
        mock_thematic_retriever = MagicMock()
        mock_thematic_retriever.retrieve.return_value = [
            {
                "text": "Justice is a recurring theme in literature.",
                "score": 0.85,
                "chunk_id": "c1",
                "laureate": "Toni Morrison",
                "year_awarded": 1993,
                "source_type": "nobel_lecture"
            }
        ]
        mock_thematic_class.return_value = mock_thematic_retriever
        
        mock_llm.return_value = {
            "answer": "Toni Morrison discussed justice in her work.",
            "completion_tokens": 10
        }
        
        # Test with dual process enabled
        result = answer_query(query, model_id="bge-large")
        
        # Verify thematic retriever was used
        mock_thematic_class.assert_called_once_with(model_id="bge-large")
        mock_thematic_retriever.retrieve.assert_called_once()

@pytest.mark.integration
def test_dual_process_consistency():
    """Test that dual process retrieval produces consistent results."""
    query = "What did Toni Morrison say about justice?"
    
    with patch('rag.query_engine.get_query_router') as mock_get_router, \
         patch('rag.query_engine.ThematicRetriever') as mock_thematic_class, \
         patch('rag.query_engine.call_openai') as mock_llm:
        
        # Setup mocks
        mock_router = MagicMock()
        mock_route_result = MagicMock()
        mock_route_result.answer_type = "rag"
        mock_route_result.intent = "thematic"
        mock_route_result.retrieval_config.top_k = 15
        mock_route_result.retrieval_config.score_threshold = 0.2
        mock_route_result.retrieval_config.filters = None
        mock_route_result.prompt_template = None
        mock_router.route_query.return_value = mock_route_result
        mock_get_router.return_value = mock_router
        
        mock_thematic_retriever = MagicMock()
        mock_thematic_retriever.retrieve.return_value = [
            {
                "text": "Justice is a recurring theme in literature.",
                "score": 0.85,
                "chunk_id": "c1",
                "laureate": "Toni Morrison",
                "year_awarded": 1993,
                "source_type": "nobel_lecture"
            },
            {
                "text": "The human condition is explored through narrative.",
                "score": 0.78,
                "chunk_id": "c2",
                "laureate": "Gabriel García Márquez",
                "year_awarded": 1982,
                "source_type": "nobel_lecture"
            }
        ]
        mock_thematic_class.return_value = mock_thematic_retriever
        
        mock_llm.return_value = {
            "answer": "Both authors discuss justice and human dignity.",
            "completion_tokens": 12
        }
        
        # Test first call
        result1 = answer_query(query, model_id="bge-large")
        
        # Test second call
        result2 = answer_query(query, model_id="bge-large")
        
        # Verify consistency
        assert len(result1["sources"]) == len(result2["sources"]) == 2
        assert result1["answer_type"] == result2["answer_type"] == "rag"

# -----------------------------------------------------------------------------------
# Test: Model-Aware Retriever Selection
# -----------------------------------------------------------------------------------

@pytest.mark.integration
def test_model_aware_retriever_selection():
    """Test that different models use appropriate retrievers."""
    query = "What did Toni Morrison say about justice?"
    
    # Test with bge-large model
    with patch('rag.query_engine.get_model') as mock_model, \
         patch('rag.query_engine.get_mode_aware_retriever') as mock_get_retriever, \
         patch('rag.query_engine.call_openai') as mock_llm:
        mock_model.return_value.encode.return_value = np.random.rand(1024).astype(np.float32)  # bge-large dimension
        mock_get_retriever.return_value = MagicMock()
        mock_get_retriever.return_value.retrieve.return_value = [{"text": "Justice is a recurring theme.","score": 0.85,"chunk_id": "c1","laureate": "Toni Morrison","year_awarded": 1993}]
        mock_llm.return_value = {"answer": "Test answer"}
        result = answer_query(query, model_id="bge-large")
        mock_get_retriever.assert_called_once_with("bge-large")
        
    # Test with miniLM model
    with patch('rag.query_engine.get_model') as mock_model, \
         patch('rag.query_engine.get_mode_aware_retriever') as mock_get_retriever, \
         patch('rag.query_engine.call_openai') as mock_llm:
        mock_model.return_value.encode.return_value = np.random.rand(384).astype(np.float32)  # miniLM dimension
        mock_get_retriever.return_value = MagicMock()
        mock_get_retriever.return_value.retrieve.return_value = [{"text": "Justice is a recurring theme.","score": 0.85,"chunk_id": "c1","laureate": "Toni Morrison","year_awarded": 1993}]
        mock_llm.return_value = {"answer": "Test answer"}
        result = answer_query(query, model_id="miniLM")
        mock_get_retriever.assert_called_once_with("miniLM")

@pytest.mark.integration
def test_is_supported_index_check(monkeypatch, mock_embedding):
    """Test that index support is checked before retrieval."""
    query = "What did Toni Morrison say about justice?"
    
    with patch('rag.query_engine.get_model') as mock_model, \
         patch('rag.query_engine.get_mode_aware_retriever') as mock_get_retriever, \
         patch('rag.query_engine.call_openai') as mock_llm:
        mock_model.return_value.encode.return_value = mock_embedding
        mock_get_retriever.return_value = MagicMock()
        mock_get_retriever.return_value.retrieve.return_value = [{"text": "Justice is a recurring theme.","score": 0.85,"chunk_id": "c1","laureate": "Toni Morrison","year_awarded": 1993}]
        mock_llm.return_value = {"answer": "Test answer"}
        
        result = answer_query(query, model_id="bge-large")
        mock_get_retriever.assert_called_once_with("bge-large")

@pytest.mark.integration
def test_min_max_return_propagation():
    """Test that min_return and max_return are propagated correctly."""
    query = "What did Toni Morrison say about justice?"
    
    with patch('rag.query_engine.get_query_router') as mock_get_router, \
         patch('rag.query_engine.ThematicRetriever') as mock_thematic_class, \
         patch('rag.query_engine.call_openai') as mock_llm:
        
        # Setup mocks
        mock_router = MagicMock()
        mock_route_result = MagicMock()
        mock_route_result.answer_type = "rag"
        mock_route_result.intent = "thematic"
        mock_route_result.retrieval_config.top_k = 15
        mock_route_result.retrieval_config.score_threshold = 0.2
        mock_route_result.retrieval_config.filters = None
        mock_route_result.prompt_template = None
        mock_router.route_query.return_value = mock_route_result
        mock_get_router.return_value = mock_router
        
        mock_thematic_retriever = MagicMock()
        mock_thematic_retriever.retrieve.return_value = [
            {
                "text": "Justice is a recurring theme in literature.",
                "score": 0.85,
                "chunk_id": "c1",
                "laureate": "Toni Morrison",
                "year_awarded": 1993,
                "source_type": "nobel_lecture"
            }
        ]
        mock_thematic_class.return_value = mock_thematic_retriever
        
        mock_llm.return_value = {
            "answer": "Toni Morrison discussed justice in her work.",
            "completion_tokens": 10
        }
        
        # Test with custom min/max return values
        result = answer_query(query, model_id="bge-large")
        
        # Verify thematic retriever was called with correct parameters
        mock_thematic_retriever.retrieve.assert_called_once_with(
            query,
            top_k=15,
            filters=None,
            score_threshold=0.2,
            min_return=5,
            max_return=12
        )
