"""
Integration test: FAISS Query Worker

Tests the integration between the FAISS query worker and the main retrieval pipeline,
ensuring proper subprocess communication and error handling.
"""

import pytest
import numpy as np
import json
from unittest.mock import patch, MagicMock
from rag.faiss_query_worker import main

# -----------------------------------------------------------------------------------
# Test Fixtures
# -----------------------------------------------------------------------------------

@pytest.fixture
def mock_embedding():
    """Mock embedding vector."""
    embedding = np.random.rand(768).astype(np.float32)
    embedding /= np.linalg.norm(embedding)
    return embedding

@pytest.fixture
def mock_chunks():
    """Mock chunks returned by query worker."""
    return [
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

# -----------------------------------------------------------------------------------
# Test: FAISS Query Worker Integration
# -----------------------------------------------------------------------------------

@pytest.mark.integration
def test_query_worker_main_integration(mock_embedding, mock_chunks):
    """Test complete query worker main function integration."""
    query = "What are common themes in Nobel laureate speeches?"
    
    with patch('rag.faiss_query_worker.get_model') as mock_model, \
         patch('rag.faiss_query_worker.query_index') as mock_query_index, \
         patch('rag.faiss_query_worker.filter_top_chunks') as mock_filter:
        
        # Setup mocks
        mock_model_instance = MagicMock()
        mock_model_instance.encode.return_value = [mock_embedding]  # encode returns a list
        mock_model_instance.get_sentence_embedding_dimension.return_value = 768
        mock_model.return_value = mock_model_instance
        mock_query_index.return_value = mock_chunks
        mock_filter.return_value = mock_chunks
        
        # Test query worker main function
        result = main(
            query=query,
            model_id="bge-large",
            top_k=5,
            filters=None,
            score_threshold=0.2
        )
        
        # Verify result structure
        assert len(result) == 2
        assert result[0]["text"] == "Justice is a recurring theme in literature."
        assert result[1]["text"] == "The human condition is explored through narrative."
        
        # Verify FAISS index was called correctly
        mock_query_index.assert_called_once()
        call_args = mock_query_index.call_args
        # The embedding is passed as the first argument
        assert call_args[0][0] is mock_embedding  # First positional argument
        assert call_args[1]["top_k"] == 5  # top_k parameter
        assert call_args[1]["model_id"] == "bge-large"  # model_id parameter

@pytest.mark.integration
def test_query_worker_with_filters(mock_embedding, mock_chunks):
    """Test query worker integration with filters."""
    query = "What did Toni Morrison say about justice?"
    
    with patch('rag.faiss_query_worker.get_model') as mock_model, \
         patch('rag.faiss_query_worker.query_index') as mock_query_index, \
         patch('rag.faiss_query_worker.filter_top_chunks') as mock_filter:
        
        # Setup mocks
        mock_model.return_value.encode.return_value = mock_embedding
        mock_query_index.return_value = [mock_chunks[0]]  # Only first chunk matches filter
        mock_filter.return_value = [mock_chunks[0]]
        
        filters = {"laureate": "Toni Morrison"}
        
        result = main(
            query=query,
            model_id="bge-large",
            top_k=5,
            filters=filters,
            score_threshold=0.2
        )
        
        # Verify result with filters
        assert len(result) == 1
        assert result[0]["laureate"] == "Toni Morrison"
        
        # Verify query_index was called with filters
        mock_query_index.assert_called_once()
        call_args = mock_query_index.call_args
        assert call_args[1]["filters"] == {"laureate": "Toni Morrison"}

@pytest.mark.integration
def test_query_worker_error_handling():
    """Test error handling in query worker integration."""
    query = "Invalid query"
    
    with patch('rag.faiss_query_worker.get_model_config') as mock_get_config:
        mock_get_config.side_effect = KeyError("Model 'invalid-model' is not supported. Available: ['bge-large', 'miniLM']")
        
        with pytest.raises(KeyError, match="Model 'invalid-model' is not supported"):
            main(
                query=query,
                model_id="invalid-model",
                top_k=5,
                filters=None,
                score_threshold=0.2
            )

@pytest.mark.integration
def test_query_worker_empty_results(mock_embedding):
    """Test query worker integration with empty results."""
    query = "Query with no results"
    
    with patch('rag.faiss_query_worker.get_model') as mock_model, \
         patch('rag.faiss_query_worker.query_index') as mock_query_index, \
         patch('rag.faiss_query_worker.filter_top_chunks') as mock_filter:
        
        # Setup mocks
        mock_model.return_value.encode.return_value = mock_embedding
        mock_query_index.return_value = []
        mock_filter.return_value = []
        
        result = main(
            query=query,
            model_id="bge-large",
            top_k=5,
            filters=None,
            score_threshold=0.2
        )
        
        # Verify empty result handling
        assert len(result) == 0

@pytest.mark.integration
def test_query_worker_score_threshold_filtering(mock_embedding, mock_chunks):
    """Test query worker integration with score threshold filtering."""
    query = "What are common themes in Nobel laureate speeches?"
    
    with patch('rag.faiss_query_worker.get_model') as mock_model, \
         patch('rag.faiss_query_worker.query_index') as mock_query_index, \
         patch('rag.faiss_query_worker.filter_top_chunks') as mock_filter:
        
        # Setup mocks
        mock_model.return_value.encode.return_value = mock_embedding
        mock_query_index.return_value = mock_chunks
        # Only first chunk passes threshold
        filtered_chunks = [mock_chunks[0]]
        mock_filter.return_value = filtered_chunks
        
        result = main(
            query=query,
            model_id="bge-large",
            top_k=5,
            filters=None,
            score_threshold=0.8  # High threshold
        )
        
        # Verify threshold filtering
        assert len(result) == 1
        assert result[0]["score"] >= 0.8
        assert result[0]["chunk_id"] == "c1"
        
        # Verify filter_top_chunks was called with correct parameters
        mock_filter.assert_called_once()
        call_args = mock_filter.call_args
        assert call_args[1]["score_threshold"] == 0.8
