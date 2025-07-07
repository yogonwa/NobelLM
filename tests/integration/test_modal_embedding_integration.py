"""
Integration Tests for Modal Embedding Service

Tests the integration of the Modal embedding service with other RAG pipeline
components including retrievers, query engine, and thematic retriever.
"""

import pytest
import numpy as np
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from rag.modal_embedding_service import embed_query, ModalEmbeddingService
from rag.query_engine import answer_query
from rag.thematic_retriever import ThematicRetriever
from rag.safe_retriever import SafeRetriever
from rag.model_config import DEFAULT_MODEL_ID


@pytest.fixture(autouse=True)
def reset_embedding_service():
    """Reset the global embedding service instance before each test to prevent interference."""
    # Reset the global service instance
    import rag.modal_embedding_service
    rag.modal_embedding_service._embedding_service = None
    
    # Set environment to force FAISS usage and prevent Weaviate fallback
    with patch.dict(os.environ, {
        "NOBELLM_USE_WEAVIATE": "0",
        "NOBELLM_USE_FAISS_SUBPROCESS": "0"
    }, clear=False):
        yield


@pytest.mark.integration
class TestModalEmbeddingWithRetrievers:
    """Test Modal embedding service integration with various retrievers."""
    
    def test_safe_retriever_uses_modal_service(self):
        """Test that SafeRetriever uses the unified embedding service."""
        # Mock the underlying model to prevent actual model loading
        mock_embedding = np.array([0.1, 0.2, 0.3] * 341, dtype=np.float32)
        with patch('rag.modal_embedding_service.get_model') as mock_get_model:
            mock_model = Mock()
            mock_model.encode.return_value = mock_embedding
            mock_get_model.return_value = mock_model

            # Mock FAISS index and metadata
            mock_chunks = [
                {
                    "chunk_id": "test_1",
                    "text": "Test chunk 1",
                    "score": 0.8,
                    "laureate": "Test Author"
                }
            ]
            with patch('rag.safe_retriever.query_index') as mock_query:
                mock_query.return_value = mock_chunks

                retriever = SafeRetriever()
                result = retriever.retrieve("test query", top_k=5)

                # Verify the actual embedding service was called (not mocked)
                mock_get_model.assert_called_once_with(DEFAULT_MODEL_ID)
                mock_model.encode.assert_called_once_with("test query", show_progress_bar=False, normalize_embeddings=True)
                assert len(result) == 1
                assert result[0]["chunk_id"] == "test_1"
    
    def test_thematic_retriever_uses_modal_service(self):
        """Test that ThematicRetriever uses the unified embedding service."""
        mock_embedding = np.array([0.1, 0.2, 0.3] * 341 + [0.1], dtype=np.float32)
        with patch('rag.modal_embedding_service.get_model') as mock_get_model:
            mock_model = Mock()
            mock_model.encode.return_value = mock_embedding
            mock_get_model.return_value = mock_model

            # Patch the FAISS index query to return mock chunks
            mock_chunks = [{
                "chunk_id": "test_1",
                "text": "Test chunk 1",
                "score": 0.8,
                "laureate": "Test Author"
            }]
            with patch('rag.safe_retriever.query_index') as mock_query_index:
                mock_query_index.return_value = mock_chunks

                retriever = ThematicRetriever()
                with patch.object(retriever, '_expand_thematic_query_ranked') as mock_expand:
                    mock_expand.return_value = [("justice", 0.9), ("fairness", 0.8)]

                    result = retriever.retrieve("What do laureates say about justice?")

                    # Now the embedding service should be called
                    assert mock_get_model.call_count >= 1
                    assert len(result) == 1
    
    def test_query_engine_uses_modal_service(self):
        """Test that the main query engine uses the unified embedding service."""
        # Mock the underlying model to prevent actual model loading
        mock_embedding = np.array([0.1, 0.2, 0.3] * 341, dtype=np.float32)
        with patch('rag.modal_embedding_service.get_model') as mock_get_model:
            mock_model = Mock()
            mock_model.encode.return_value = mock_embedding
            mock_get_model.return_value = mock_model
            
            # Mock the components that the retriever uses, but not the retriever itself
            with patch('rag.query_engine.get_query_router') as mock_get_router, \
                 patch('rag.safe_retriever.query_index') as mock_query_index, \
                 patch('rag.query_engine.get_prompt_builder') as mock_get_builder, \
                 patch('rag.query_engine.call_openai') as mock_openai:
                
                # Mock query router - use factual intent to ensure embedding service is called
                mock_router = Mock()
                mock_router_result = Mock()
                mock_router_result.intent = "factual"  # Change to factual
                mock_router_result.retrieval_config = Mock()
                mock_router_result.retrieval_config.top_k = 10
                mock_router_result.retrieval_config.filters = {}
                mock_router_result.retrieval_config.score_threshold = 0.2
                mock_router.route_query.return_value = mock_router_result
                mock_get_router.return_value = mock_router
                
                # Mock the FAISS index query
                mock_chunks = [
                    {
                        "chunk_id": "test_1",
                        "text": "Test chunk 1",
                        "score": 0.8,
                        "laureate": "Test Author"
                    }
                ]
                mock_query_index.return_value = mock_chunks
                
                # Mock prompt builder
                mock_builder = Mock()
                mock_builder.build_qa_prompt.return_value = "Test prompt with actual text content"  # Change to qa_prompt
                mock_get_builder.return_value = mock_builder
                
                # Mock OpenAI - fix the response structure
                mock_openai.return_value = {
                    "choices": [{"message": {"content": "Test answer"}}],
                    "answer": "Test answer"  # Add the expected answer field
                }
                
                result = answer_query("When did Toni Morrison win the Nobel Prize?")  # Change to factual query
                
                # Verify the actual embedding service was called
                mock_get_model.assert_called_with(DEFAULT_MODEL_ID)
                assert result["answer"] == "Test answer"
                assert result["answer_type"] == "rag"


@pytest.mark.integration
class TestModalEmbeddingEnvironmentRouting:
    """Test environment-based routing between Modal and local embedding."""
    
    def test_development_routes_to_local(self):
        """Test that development environment routes to local embedding."""
        with patch.dict(os.environ, {}, clear=True):
            mock_embedding = np.array([0.1, 0.2, 0.3] * 341, dtype=np.float32)
            
            # Mock local embedding
            with patch('rag.modal_embedding_service.get_model') as mock_get_model:
                mock_model = Mock()
                mock_model.encode.return_value = mock_embedding
                mock_get_model.return_value = mock_model
                
                result = embed_query("test query")
                
                assert np.array_equal(result, mock_embedding)
                mock_get_model.assert_called_once_with(DEFAULT_MODEL_ID)
    
    def test_production_routes_to_modal(self):
        """Test that production environment routes to Modal."""
        with patch.dict(os.environ, {"NOBELLM_ENVIRONMENT": "production"}):
            # Mock the environment detection to ensure it returns True
            with patch('rag.modal_embedding_service.ModalEmbeddingService._detect_production_environment', return_value=True):
                # Mock Modal stub
                with patch('rag.modal_embedding_service.ModalEmbeddingService._get_modal_stub') as mock_get_stub:
                    mock_stub = Mock()
                    mock_function = Mock()
                    mock_function.remote.return_value = [0.1, 0.2, 0.3] * 341 + [0.1]  # 1024 dims
                    mock_stub.function.return_value = mock_function
                    mock_get_stub.return_value = mock_stub
                    
                    # Mock model config
                    with patch('rag.modal_embedding_service.get_model_config') as mock_config:
                        mock_config.return_value = {"embedding_dim": 1024}
                        
                        result = embed_query("test query")
                        
                        assert result.shape == (1024,)
                        mock_function.remote.assert_called_once_with("test query")
    
    def test_production_fallback_to_local(self):
        """Test that production falls back to local when Modal fails."""
        with patch.dict(os.environ, {"NOBELLM_ENVIRONMENT": "production"}):
            mock_embedding = np.array([0.1, 0.2, 0.3] * 341 + [0.1], dtype=np.float32)  # 1024 dims
            
            # Mock the environment detection to ensure it returns True
            with patch('rag.modal_embedding_service.ModalEmbeddingService._detect_production_environment', return_value=True):
                # Mock Modal stub that fails
                with patch('rag.modal_embedding_service.ModalEmbeddingService._get_modal_stub') as mock_get_stub:
                    mock_get_stub.side_effect = Exception("Modal not available")
                    
                    # Mock local embedding as fallback
                    with patch('rag.modal_embedding_service.get_model') as mock_get_model:
                        mock_model = Mock()
                        mock_model.encode.return_value = mock_embedding
                        mock_get_model.return_value = mock_model
                        
                        result = embed_query("test query")
                        
                        assert np.array_equal(result, mock_embedding)
                        mock_get_model.assert_called_once_with(DEFAULT_MODEL_ID)


@pytest.mark.integration
class TestModalEmbeddingWithModelConfig:
    """Test model-aware embedding with different model configurations."""
    
    def test_model_aware_embedding_bge_large(self):
        """Test embedding with bge-large model configuration."""
        with patch.dict(os.environ, {}, clear=True):
            # Fix the embedding dimension to match the actual array size
            mock_embedding = np.array([0.1, 0.2, 0.3] * 341 + [0.1], dtype=np.float32)  # 1024 dims
            
            with patch('rag.modal_embedding_service.get_model') as mock_get_model:
                mock_model = Mock()
                mock_model.encode.return_value = mock_embedding
                mock_get_model.return_value = mock_model
                
                result = embed_query("test query", model_id="bge-large")
                
                assert result.shape == (1024,)
                mock_get_model.assert_called_once_with("bge-large")
    
    def test_model_aware_embedding_miniLM(self):
        """Test embedding with miniLM model configuration."""
        with patch.dict(os.environ, {}, clear=True):
            mock_embedding = np.array([0.1, 0.2, 0.3] * 128, dtype=np.float32)  # 384 dims
            
            with patch('rag.modal_embedding_service.get_model') as mock_get_model:
                mock_model = Mock()
                mock_model.encode.return_value = mock_embedding
                mock_get_model.return_value = mock_model
                
                result = embed_query("test query", model_id="all-MiniLM-L6-v2")
                
                assert result.shape == (384,)
                mock_get_model.assert_called_once_with("all-MiniLM-L6-v2")
    
    def test_model_aware_embedding_production_modal(self):
        """Test model-aware embedding in production with Modal."""
        with patch.dict(os.environ, {"NOBELLM_ENVIRONMENT": "production"}):
            # Mock the environment detection to ensure it returns True
            with patch('rag.modal_embedding_service.ModalEmbeddingService._detect_production_environment', return_value=True):
                # Mock Modal stub - fix the import path
                with patch('rag.modal_embedding_service.ModalEmbeddingService._get_modal_stub') as mock_get_stub:
                    mock_stub = Mock()
                    mock_function = Mock()
                    mock_function.remote.return_value = [0.1, 0.2, 0.3] * 341 + [0.1]  # 1024 dims
                    mock_stub.function.return_value = mock_function
                    mock_get_stub.return_value = mock_stub
                    
                    # Mock model config
                    with patch('rag.modal_embedding_service.get_model_config') as mock_config:
                        mock_config.return_value = {"embedding_dim": 1024}
                        
                        result = embed_query("test query", model_id="bge-large")
                        
                        assert result.shape == (1024,)
                        mock_function.remote.assert_called_once_with("test query")


@pytest.mark.integration
class TestModalEmbeddingErrorHandling:
    """Test error handling and fallback behavior."""
    
    def test_retriever_handles_embedding_failure(self):
        """Test that retrievers handle embedding service failures gracefully."""
        with patch('rag.modal_embedding_service.get_model') as mock_get_model:
            mock_get_model.side_effect = Exception("Model loading failed")
            
            retriever = SafeRetriever()
            # Should handle the error gracefully
            with pytest.raises(Exception):
                retriever.retrieve("test query")
    
    def test_query_engine_handles_embedding_failure(self):
        """Test that query engine handles embedding failures gracefully."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('rag.modal_embedding_service.get_model') as mock_get_model:
                mock_get_model.side_effect = Exception("Model loading failed")
                
                # Should handle the error gracefully
                with pytest.raises(Exception):
                    answer_query("test query")
    
    def test_production_fallback_integration(self):
        """Test production fallback behavior in integration scenario."""
        with patch.dict(os.environ, {"NOBELLM_ENVIRONMENT": "production"}):
            mock_embedding = np.array([0.1, 0.2, 0.3] * 341, dtype=np.float32)
            
            # Mock Modal stub that fails
            with patch('rag.modal_embedding_service.ModalEmbeddingService._get_modal_stub') as mock_get_stub:
                mock_get_stub.side_effect = Exception("Modal not available")
                
                # Mock local embedding as fallback
                with patch('rag.modal_embedding_service.get_model') as mock_get_model:
                    mock_model = Mock()
                    mock_model.encode.return_value = mock_embedding
                    mock_get_model.return_value = mock_model
                    
                    result = embed_query("test query")
                    
                    assert np.array_equal(result, mock_embedding)
                    mock_get_model.assert_called_once_with(DEFAULT_MODEL_ID) 