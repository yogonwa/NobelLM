"""
Canonical integration tests for answer_query() - the main API.

This module tests the end-to-end behavior of answer_query() across all query types:
- Factual queries: answer_type == "rag", top_k == 5, score_threshold == 0.25, correct retriever used
- Thematic queries: answer_type == "rag", top_k == 15, filters correct (if applicable)
- Generative queries: answer_type == "rag", top_k == 10
- Metadata queries: answer_type == "metadata", no retriever used, correct metadata answer returned

These tests ensure the new architecture works correctly with QueryRouter, model-aware paths, and consistent score threshold handling.
"""
import pytest
import logging
from unittest.mock import patch, MagicMock
from rag.query_engine import answer_query
from rag.query_router import QueryIntent


@pytest.fixture(autouse=True)
def force_inprocess(monkeypatch):
    """Force in-process mode for consistent test behavior"""
    monkeypatch.setenv("NOBELLM_USE_FAISS_SUBPROCESS", "0")


@pytest.mark.integration
def test_answer_query_factual(monkeypatch):
    """Test factual query path with correct retriever and configuration"""
    mock_chunks = [
        {
            "chunk_id": "c1",
            "text": "Toni Morrison won the Nobel Prize in Literature in 1993.",
            "score": 0.95,
            "laureate": "Toni Morrison",
            "year_awarded": 1993,
            "source_type": "nobel_lecture"
        }
    ]
    
    # Mock the QueryRouter to return factual intent
    mock_route_result = MagicMock()
    mock_route_result.answer_type = "rag"
    mock_route_result.intent = QueryIntent.FACTUAL
    mock_route_result.retrieval_config.top_k = 5
    mock_route_result.retrieval_config.score_threshold = 0.25
    mock_route_result.retrieval_config.filters = None
    mock_route_result.prompt_template = None
    
    with patch("rag.query_engine.get_query_router") as mock_get_router, \
         patch("rag.query_engine.get_mode_aware_retriever") as mock_get_retriever, \
         patch("rag.query_engine.call_openai") as mock_openai:
        
        # Setup mocks
        mock_router = MagicMock()
        mock_router.route_query.return_value = mock_route_result
        mock_get_router.return_value = mock_router
        
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = mock_chunks
        mock_get_retriever.return_value = mock_retriever
        
        mock_openai.return_value = {
            "answer": "Toni Morrison won the Nobel Prize in Literature in 1993.",
            "completion_tokens": 15
        }
        
        result = answer_query("Who won the Nobel Prize in Literature in 1993?", model_id="bge-large")
        
        # Verify result structure
        assert result["answer_type"] == "rag"
        assert "Toni Morrison" in result["answer"]
        assert result["metadata_answer"] is None
        assert len(result["sources"]) == 1
        assert result["sources"][0]["laureate"] == "Toni Morrison"
        
        # Verify retriever was called with correct parameters
        mock_retriever.retrieve.assert_called_once_with(
            "Who won the Nobel Prize in Literature in 1993?",
            top_k=5,
            filters=None,
            score_threshold=0.25,
            min_return=3,
            max_return=10
        )


@pytest.mark.integration
def test_answer_query_thematic(monkeypatch):
    """Test thematic query path with ThematicRetriever and larger top_k"""
    mock_chunks = [
        {
            "chunk_id": "c1",
            "text": "Justice is a recurring theme in literature.",
            "score": 0.92,
            "laureate": "Toni Morrison",
            "year_awarded": 1993,
            "source_type": "nobel_lecture"
        },
        {
            "chunk_id": "c2",
            "text": "Love and redemption appear frequently.",
            "score": 0.88,
            "laureate": "Gabriel García Márquez",
            "year_awarded": 1982,
            "source_type": "nobel_lecture"
        }
    ]
    
    # Mock the QueryRouter to return thematic intent
    mock_route_result = MagicMock()
    mock_route_result.answer_type = "rag"
    mock_route_result.intent = "thematic"
    mock_route_result.retrieval_config.top_k = 15
    mock_route_result.retrieval_config.score_threshold = 0.2
    mock_route_result.retrieval_config.filters = None
    mock_route_result.prompt_template = None
    
    with patch("rag.query_engine.get_query_router") as mock_get_router, \
         patch("rag.query_engine.ThematicRetriever") as mock_thematic_retriever_class, \
         patch("rag.query_engine.call_openai") as mock_openai:
        
        # Setup mocks
        mock_router = MagicMock()
        mock_router.route_query.return_value = mock_route_result
        mock_get_router.return_value = mock_router
        
        mock_thematic_retriever = MagicMock()
        mock_thematic_retriever.retrieve.return_value = mock_chunks
        mock_thematic_retriever_class.return_value = mock_thematic_retriever
        
        mock_openai.return_value = {
            "answer": "Common themes in Nobel lectures include justice, love, and redemption.",
            "completion_tokens": 20
        }
        
        result = answer_query("What are common themes in Nobel lectures?", model_id="bge-large")
        
        # Verify result structure
        assert result["answer_type"] == "rag"
        assert "themes" in result["answer"].lower()
        assert result["metadata_answer"] is None
        assert len(result["sources"]) == 2
        
        # Verify ThematicRetriever was used with correct parameters
        mock_thematic_retriever.retrieve.assert_called_once_with(
            "What are common themes in Nobel lectures?",
            top_k=15,
            filters=None,
            score_threshold=0.2,
            min_return=5,
            max_return=12
        )


@pytest.mark.integration
def test_answer_query_generative(monkeypatch):
    """Test generative query path with standard retriever and top_k == 10"""
    mock_chunks = [
        {
            "chunk_id": "c1",
            "text": "Literature has the power to transform society.",
            "score": 0.89,
            "laureate": "Mario Vargas Llosa",
            "year_awarded": 2010,
            "source_type": "nobel_lecture"
        }
    ]
    
    # Mock the QueryRouter to return generative intent
    mock_route_result = MagicMock()
    mock_route_result.answer_type = "rag"
    mock_route_result.intent = QueryIntent.GENERATIVE
    mock_route_result.retrieval_config.top_k = 10
    mock_route_result.retrieval_config.score_threshold = 0.2
    mock_route_result.retrieval_config.filters = None
    mock_route_result.prompt_template = None
    
    with patch("rag.query_engine.get_query_router") as mock_get_router, \
         patch("rag.query_engine.get_mode_aware_retriever") as mock_get_retriever, \
         patch("rag.query_engine.call_openai") as mock_openai:
        
        # Setup mocks
        mock_router = MagicMock()
        mock_router.route_query.return_value = mock_route_result
        mock_get_router.return_value = mock_router
        
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = mock_chunks
        mock_get_retriever.return_value = mock_retriever
        
        mock_openai.return_value = {
            "answer": "Literature has the power to transform society and inspire change.",
            "completion_tokens": 18
        }
        
        result = answer_query("How does literature impact society?", model_id="bge-large")
        
        # Verify result structure
        assert result["answer_type"] == "rag"
        assert "literature" in result["answer"].lower()
        assert result["metadata_answer"] is None
        assert len(result["sources"]) == 1
        
        # Verify retriever was called with correct parameters
        mock_retriever.retrieve.assert_called_once_with(
            "How does literature impact society?",
            top_k=10,
            filters=None,
            score_threshold=0.2,
            min_return=3,
            max_return=10
        )


@pytest.mark.integration
def test_answer_query_metadata():
    """Test answer_query with metadata answer."""
    query = "Who won the Nobel Prize in Literature in 1993?"
    
    with patch('rag.query_engine.get_query_router') as mock_get_router:
        # Setup mocks for metadata answer
        mock_router = MagicMock()
        mock_route_result = MagicMock()
        mock_route_result.answer_type = "metadata"
        mock_route_result.intent = "metadata"
        mock_route_result.answer = "Toni Morrison won the Nobel Prize in Literature in 1993."
        mock_route_result.metadata_answer = "Toni Morrison won the Nobel Prize in Literature in 1993."
        mock_router.route_query.return_value = mock_route_result
        mock_get_router.return_value = mock_router
        
        # Test the complete pipeline
        result = answer_query(query, model_id="bge-large")
        
        # Verify metadata result structure
        assert result["answer_type"] == "metadata"
        assert "Toni Morrison" in result["answer"]
        assert result["metadata_answer"] == "Toni Morrison won the Nobel Prize in Literature in 1993."
        assert result["sources"] == []


@pytest.mark.integration
def test_answer_query_with_filters(monkeypatch):
    """Test query with filters - ensure filters are passed to retriever"""
    mock_chunks = [
        {
            "chunk_id": "c1",
            "text": "Justice is a recurring theme in literature.",
            "score": 0.92,
            "laureate": "Toni Morrison",
            "year_awarded": 1993,
            "source_type": "nobel_lecture"
        }
    ]
    
    # Mock the QueryRouter to return factual intent with filters
    mock_route_result = MagicMock()
    mock_route_result.answer_type = "rag"
    mock_route_result.intent = QueryIntent.FACTUAL
    mock_route_result.retrieval_config.top_k = 5
    mock_route_result.retrieval_config.score_threshold = 0.25
    mock_route_result.retrieval_config.filters = {"laureate": "Toni Morrison"}
    mock_route_result.prompt_template = None
    
    with patch("rag.query_engine.get_query_router") as mock_get_router, \
         patch("rag.query_engine.get_mode_aware_retriever") as mock_get_retriever, \
         patch("rag.query_engine.call_openai") as mock_openai:
        
        # Setup mocks
        mock_router = MagicMock()
        mock_router.route_query.return_value = mock_route_result
        mock_get_router.return_value = mock_router
        
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = mock_chunks
        mock_get_retriever.return_value = mock_retriever
        
        mock_openai.return_value = {
            "answer": "Toni Morrison discussed justice extensively.",
            "completion_tokens": 12
        }
        
        result = answer_query("What did Toni Morrison say about justice?", model_id="bge-large")
        
        # Verify result structure
        assert result["answer_type"] == "rag"
        assert "justice" in result["answer"].lower()
        assert len(result["sources"]) == 1
        assert result["sources"][0]["laureate"] == "Toni Morrison"
        
        # Verify retriever was called with filters
        mock_retriever.retrieve.assert_called_once_with(
            "What did Toni Morrison say about justice?",
            top_k=5,
            filters={"laureate": "Toni Morrison"},
            score_threshold=0.25,
            min_return=3,
            max_return=10
        )


@pytest.mark.integration
def test_answer_query_error_handling():
    """Test error handling in answer_query."""
    query = "What did Toni Morrison say about justice?"
    
    with patch('rag.query_engine.get_query_router') as mock_get_router, \
         patch('rag.query_engine.get_mode_aware_retriever') as mock_get_retriever:
        
        # Setup mocks
        mock_router = MagicMock()
        mock_route_result = MagicMock()
        mock_route_result.answer_type = "rag"
        mock_route_result.intent = "factual"
        mock_route_result.retrieval_config.top_k = 5
        mock_route_result.retrieval_config.score_threshold = 0.25
        mock_route_result.retrieval_config.filters = None
        mock_route_result.prompt_template = None
        mock_router.route_query.return_value = mock_route_result
        mock_get_router.return_value = mock_router
        
        mock_retriever = MagicMock()
        mock_retriever.retrieve.side_effect = Exception("Retriever failed")
        mock_get_retriever.return_value = mock_retriever
        
        # Test error handling
        with pytest.raises(Exception, match="Retriever failed"):
            answer_query(query, model_id="bge-large")


@pytest.mark.integration
def test_answer_query_logging(caplog):
    """Test logging in answer_query."""
    query = "Test query"
    
    # Set log level to capture INFO messages
    caplog.set_level("INFO")
    
    with patch('rag.query_engine.get_query_router') as mock_get_router, \
         patch('rag.query_engine.get_mode_aware_retriever') as mock_get_retriever, \
         patch('rag.query_engine.call_openai') as mock_llm:
        
        # Setup mocks
        mock_router = MagicMock()
        mock_route_result = MagicMock()
        mock_route_result.answer_type = "rag"
        mock_route_result.intent = "factual"
        mock_route_result.retrieval_config.top_k = 5
        mock_route_result.retrieval_config.score_threshold = 0.2
        mock_route_result.retrieval_config.filters = None
        mock_route_result.prompt_template = None
        mock_router.route_query.return_value = mock_route_result
        mock_get_router.return_value = mock_router
        
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []
        mock_get_retriever.return_value = mock_retriever
        
        mock_llm.return_value = {
            "answer": "Test answer",
            "completion_tokens": 5
        }
        
        # Test the complete pipeline
        result = answer_query(query, model_id="bge-large")
        
        # Verify logging - check for actual log messages from the query engine
        assert "Starting query processing" in caplog.text or "Query completed successfully" in caplog.text 