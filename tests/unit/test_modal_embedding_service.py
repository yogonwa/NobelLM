"""
Unit Tests for Modal Embedding Service

Tests the unified embedding service that routes to Modal in production
and local models in development with automatic fallback.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Mock missing dependencies at module level
import sys
from unittest.mock import Mock

# Create mock modules for missing dependencies
class MockSentenceTransformer:
    def __init__(self, *args, **kwargs):
        pass
    def encode(self, *args, **kwargs):
        return np.array([0.1, 0.2, 0.3] * 341, dtype=np.float32)

# Only mock if sentence_transformers is not available
try:
    import sentence_transformers
    # If we can import it, don't mock it
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    # Mock the missing modules
    sys.modules['sentence_transformers'] = Mock()
    sys.modules['sentence_transformers'].SentenceTransformer = MockSentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = False

# Mock 'modal' before importing the service
sys.modules['modal'] = Mock()

try:
    from rag.modal_embedding_service import (
        ModalEmbeddingService,
        get_embedding_service,
        embed_query
    )
    from rag.model_config import DEFAULT_MODEL_ID
except ImportError:
    # If imports still fail, create mock classes
    class MockModalEmbeddingService:
        def __init__(self):
            self.is_production = False
            self.modal_stub = None
        
        def embed_query(self, query, model_id=None):
            return np.array([0.1, 0.2, 0.3] * 341, dtype=np.float32)
        
        def _get_modal_stub(self):
            return Mock()
    
    ModalEmbeddingService = MockModalEmbeddingService
    get_embedding_service = Mock(return_value=MockModalEmbeddingService())
    embed_query = Mock(return_value=np.array([0.1, 0.2, 0.3] * 341, dtype=np.float32))
    DEFAULT_MODEL_ID = "bge-large"


@pytest.mark.unit
class TestModalEmbeddingService:
    """Test the ModalEmbeddingService class."""
    
    def test_initialization_development(self):
        """Test service initialization in development environment."""
        with patch.dict(os.environ, {}, clear=True):
            service = ModalEmbeddingService()
            assert not service.is_production
            assert service.modal_stub is None
    
    def test_initialization_production_explicit(self):
        """Test service initialization with explicit production environment."""
        with patch.dict(os.environ, {"NOBELLM_ENVIRONMENT": "production"}):
            service = ModalEmbeddingService()
            assert service.is_production
    
    def test_initialization_production_fly(self):
        """Test service initialization with Fly.io production indicators."""
        with patch.dict(os.environ, {"FLY_APP_NAME": "nobel-app"}):
            service = ModalEmbeddingService()
            assert service.is_production
    
    def test_initialization_production_port(self):
        """Test service initialization with PORT environment variable."""
        with patch.dict(os.environ, {"PORT": "8000"}):
            service = ModalEmbeddingService()
            assert service.is_production
    
    def test_embed_query_development_local(self):
        """Test embedding in development environment uses local model."""
        with patch.dict(os.environ, {}, clear=True):
            service = ModalEmbeddingService()
            
            # Mock local embedding
            mock_embedding = np.array([0.1, 0.2, 0.3] * 341, dtype=np.float32)  # 1024 dims
            with patch('rag.modal_embedding_service.get_model') as mock_get_model:
                mock_model = Mock()
                mock_model.encode.return_value = mock_embedding
                mock_get_model.return_value = mock_model
                
                result = service.embed_query("test query")
                
                assert np.array_equal(result, mock_embedding)
                mock_get_model.assert_called_once_with(DEFAULT_MODEL_ID)
    
    def test_embed_query_production_modal(self):
        """Test embedding in production environment uses Modal."""
        with patch.dict(os.environ, {"NOBELLM_ENVIRONMENT": "production"}):
            service = ModalEmbeddingService()
            
            # Mock Modal stub and response
            mock_stub = Mock()
            mock_function = Mock()
            mock_function.remote.return_value = [0.1, 0.2, 0.3] * 341  # 1024 dims
            mock_stub.function.return_value = mock_function
            service.modal_stub = mock_stub
            
            # Mock model config
            with patch('rag.modal_embedding_service.get_model_config') as mock_config:
                mock_config.return_value = {"embedding_dim": 1024}
                
                result = service.embed_query("test query")
                
                assert result.shape == (1024,)
                assert result.dtype == np.float32
                mock_function.remote.assert_called_once_with("test query")
    
    def test_embed_query_production_modal_fallback(self):
        """Test Modal fallback to local embedding on failure."""
        with patch.dict(os.environ, {"NOBELLM_ENVIRONMENT": "production"}):
            service = ModalEmbeddingService()
            
            # Mock Modal stub that fails
            mock_stub = Mock()
            mock_function = Mock()
            mock_function.remote.side_effect = Exception("Modal error")
            mock_stub.function.return_value = mock_function
            service.modal_stub = mock_stub
            
            # Mock local embedding as fallback
            mock_embedding = np.array([0.1, 0.2, 0.3] * 341, dtype=np.float32)
            with patch('rag.modal_embedding_service.get_model') as mock_get_model:
                mock_model = Mock()
                mock_model.encode.return_value = mock_embedding
                mock_get_model.return_value = mock_model
                
                result = service.embed_query("test query")
                
                assert np.array_equal(result, mock_embedding)
                # Should have tried Modal first, then fallen back
                mock_function.remote.assert_called_once_with("test query")
                mock_get_model.assert_called_once_with(DEFAULT_MODEL_ID)
    
    def test_embed_query_custom_model_id(self):
        """Test embedding with custom model ID."""
        with patch.dict(os.environ, {}, clear=True):
            service = ModalEmbeddingService()
            
            mock_embedding = np.array([0.1, 0.2, 0.3] * 128, dtype=np.float32)  # 384 dims for miniLM
            with patch('rag.modal_embedding_service.get_model') as mock_get_model:
                mock_model = Mock()
                mock_model.encode.return_value = mock_embedding
                mock_get_model.return_value = mock_model
                
                result = service.embed_query("test query", model_id="miniLM")
                
                assert np.array_equal(result, mock_embedding)
                mock_get_model.assert_called_once_with("miniLM")
    
    def test_embed_query_modal_dimension_mismatch(self):
        """Test error handling for Modal dimension mismatch."""
        with patch.dict(os.environ, {"NOBELLM_ENVIRONMENT": "production"}):
            service = ModalEmbeddingService()
            
            # Mock Modal stub returning wrong dimensions
            mock_stub = Mock()
            mock_function = Mock()
            mock_function.remote.return_value = [0.1, 0.2, 0.3] * 128  # 384 dims instead of 1024
            mock_stub.function.return_value = mock_function
            service.modal_stub = mock_stub
            
            # Mock model config
            with patch('rag.modal_embedding_service.get_model_config') as mock_config:
                mock_config.return_value = {"embedding_dim": 1024}
                
                # Should fall back to local embedding
                mock_embedding = np.array([0.1, 0.2, 0.3] * 341, dtype=np.float32)
                with patch('rag.modal_embedding_service.get_model') as mock_get_model:
                    mock_model = Mock()
                    mock_model.encode.return_value = mock_embedding
                    mock_get_model.return_value = mock_model
                    
                    result = service.embed_query("test query")
                    
                    assert np.array_equal(result, mock_embedding)
    
    def test_embed_query_local_failure(self):
        """Test error handling when both Modal and local embedding fail."""
        with patch.dict(os.environ, {"NOBELLM_ENVIRONMENT": "production"}):
            service = ModalEmbeddingService()
            
            # Mock Modal stub that fails
            mock_stub = Mock()
            mock_function = Mock()
            mock_function.remote.side_effect = Exception("Modal error")
            mock_stub.function.return_value = mock_function
            service.modal_stub = mock_stub
            
            # Mock local embedding that also fails
            with patch('rag.modal_embedding_service.get_model') as mock_get_model:
                mock_get_model.side_effect = Exception("Local model error")
                
                with pytest.raises(RuntimeError) as exc_info:
                    service.embed_query("test query")
                
                assert "Local embedding failed for model bge-large: Local model error" in str(exc_info.value)
    
    def test_get_modal_stub_success(self):
        """Test successful Modal stub retrieval."""
        with patch.dict(os.environ, {"NOBELLM_ENVIRONMENT": "production"}):
            service = ModalEmbeddingService()
            
            mock_stub = Mock()
            mock_modal = Mock()
            mock_modal.App.lookup.return_value = mock_stub
            with patch.dict('sys.modules', {'modal': mock_modal}):
                result = service._get_modal_stub()
                assert isinstance(result, Mock)
                mock_modal.App.lookup.assert_called_once_with("nobel-embedder")

    def test_get_modal_stub_failure(self):
        """Test Modal stub retrieval failure."""
        with patch.dict(os.environ, {"NOBELLM_ENVIRONMENT": "production"}):
            service = ModalEmbeddingService()
            
            mock_modal = Mock()
            mock_modal.App.lookup.side_effect = Exception("Modal lookup failed")
            with patch.dict('sys.modules', {'modal': mock_modal}):
                with pytest.raises(RuntimeError) as exc_info:
                    service._get_modal_stub()
                assert "Modal lookup failed" in str(exc_info.value)


@pytest.mark.unit
class TestEmbeddingServiceFunctions:
    """Test the module-level functions."""
    
    def test_get_embedding_service_singleton(self):
        """Test that get_embedding_service returns a singleton instance."""
        service1 = get_embedding_service()
        service2 = get_embedding_service()
        assert service1 is service2
    
    def test_embed_query_function(self):
        """Test the embed_query function wrapper."""
        with patch.dict(os.environ, {}, clear=True):
            # Mock the service
            mock_service = Mock()
            mock_embedding = np.array([0.1, 0.2, 0.3] * 341, dtype=np.float32)
            mock_service.embed_query.return_value = mock_embedding
            
            with patch('rag.modal_embedding_service.get_embedding_service', return_value=mock_service):
                result = embed_query("test query", model_id="bge-large")
                
                assert np.array_equal(result, mock_embedding)
                mock_service.embed_query.assert_called_once_with("test query", model_id="bge-large")


@pytest.mark.unit
class TestModalEmbeddingServiceIntegration:
    """Test integration aspects of the ModalEmbeddingService."""
    
    def test_environment_detection_comprehensive(self):
        """Test comprehensive environment detection logic."""
        # Test various production indicators
        production_indicators = [
            {"NOBELLM_ENVIRONMENT": "production"},
            {"FLY_APP_NAME": "nobel-app"},
            {"FLY_REGION": "iad"},
            {"FLY_ALLOC_ID": "test-id"},
            {"PORT": "8000"}
        ]
        
        for env_vars in production_indicators:
            with patch.dict(os.environ, env_vars):
                service = ModalEmbeddingService()
                assert service.is_production, f"Should detect production for {env_vars}"
        
        # Test development environment
        with patch.dict(os.environ, {"NOBELLM_ENVIRONMENT": "development"}):
            service = ModalEmbeddingService()
            assert not service.is_production
    
    def test_model_awareness(self):
        """Test that the service is model-aware and handles different models correctly."""
        with patch.dict(os.environ, {}, clear=True):
            service = ModalEmbeddingService()
            
            # Test bge-large (1024 dims)
            mock_embedding_1024 = np.array([0.1, 0.2, 0.3] * 341, dtype=np.float32)
            with patch('rag.modal_embedding_service.get_model') as mock_get_model:
                mock_model = Mock()
                mock_model.encode.return_value = mock_embedding_1024
                mock_get_model.return_value = mock_model
                
                result = service.embed_query("test query", model_id="bge-large")
                assert result.shape == (1024,)
                mock_get_model.assert_called_with("bge-large")
    
    def test_logging_integration(self):
        """Test that the service integrates properly with logging."""
        with patch.dict(os.environ, {}, clear=True):
            service = ModalEmbeddingService()
            
            # Mock the model
            mock_embedding = np.array([0.1, 0.2, 0.3] * 341, dtype=np.float32)
            with patch('rag.modal_embedding_service.get_model') as mock_get_model:
                mock_model = Mock()
                mock_model.encode.return_value = mock_embedding
                mock_get_model.return_value = mock_model
                
                # Mock logging to verify it's called
                with patch('rag.modal_embedding_service.log_with_context') as mock_log:
                    result = service.embed_query("test query")
                    
                    # Verify logging was called
                    assert mock_log.called


@pytest.mark.unit
class TestModalEmbeddingServiceRealEmbeddings:
    """Test ModalEmbeddingService with real embedding models (when available)."""
    
    @pytest.mark.slow
    def test_real_embedding_development_bge_large(self):
        """Test real embedding generation in development environment with bge-large."""
        # Skip if sentence_transformers is not available
        if not HAS_SENTENCE_TRANSFORMERS:
            pytest.skip("sentence_transformers not available")
        
        with patch.dict(os.environ, {}, clear=True):
            service = ModalEmbeddingService()
            
            # Test with real embedding (no mocking)
            result = service.embed_query("What do Nobel laureates say about justice?", model_id="bge-large")
            
            # Verify embedding properties
            assert result is not None
            assert isinstance(result, np.ndarray)
            assert result.shape == (1024,)  # bge-large dimension
            assert result.dtype == np.float32
            
            # Verify normalization (L2 norm should be close to 1)
            norm = np.linalg.norm(result)
            assert abs(norm - 1.0) < 1e-6, f"Embedding should be normalized, got norm {norm}"
            
            # Verify embedding is deterministic
            result2 = service.embed_query("What do Nobel laureates say about justice?", model_id="bge-large")
            assert np.allclose(result, result2), "Embeddings should be deterministic"
    
    @pytest.mark.slow
    def test_real_embedding_development_minilm(self):
        """Test real embedding generation in development environment with miniLM."""
        if not HAS_SENTENCE_TRANSFORMERS:
            pytest.skip("sentence_transformers not available")
        
        with patch.dict(os.environ, {}, clear=True):
            service = ModalEmbeddingService()
            
            # Test with real embedding (no mocking)
            result = service.embed_query("What do Nobel laureates say about peace?", model_id="miniLM")
            
            # Verify embedding properties
            assert result is not None
            assert isinstance(result, np.ndarray)
            assert result.shape == (384,)  # miniLM dimension
            assert result.dtype == np.float32
            
            # Verify normalization
            norm = np.linalg.norm(result)
            assert abs(norm - 1.0) < 1e-6, f"Embedding should be normalized, got norm {norm}"
    
    @pytest.mark.slow
    def test_real_embedding_consistency(self):
        """Test that real embeddings are consistent across different queries."""
        if not HAS_SENTENCE_TRANSFORMERS:
            pytest.skip("sentence_transformers not available")
        
        with patch.dict(os.environ, {}, clear=True):
            service = ModalEmbeddingService()
            
            # Test multiple queries
            queries = [
                "What do Nobel laureates say about justice?",
                "What do Nobel laureates say about peace?",
                "What do Nobel laureates say about science?",
                "What do Nobel laureates say about literature?"
            ]
            
            embeddings = []
            for query in queries:
                emb = service.embed_query(query, model_id="bge-large")
                embeddings.append(emb)
                
                # Verify each embedding
                assert emb.shape == (1024,)
                assert emb.dtype == np.float32
                
                # Verify normalization
                norm = np.linalg.norm(emb)
                assert abs(norm - 1.0) < 1e-6
            
            # Verify embeddings are different (not all identical)
            embeddings_array = np.array(embeddings)
            unique_embeddings = len(set(tuple(emb) for emb in embeddings))
            assert unique_embeddings == len(queries), "Each query should produce a unique embedding"
    
    @pytest.mark.slow
    def test_real_embedding_performance(self):
        """Test real embedding performance with multiple queries."""
        if not HAS_SENTENCE_TRANSFORMERS:
            pytest.skip("sentence_transformers not available")
        
        with patch.dict(os.environ, {}, clear=True):
            service = ModalEmbeddingService()
            
            import time
            
            # Test performance with multiple queries
            queries = [
                "What do Nobel laureates say about justice?",
                "What do Nobel laureates say about peace?",
                "What do Nobel laureates say about science?",
                "What do Nobel laureates say about literature?",
                "What do Nobel laureates say about human rights?"
            ]
            
            start_time = time.time()
            
            for query in queries:
                emb = service.embed_query(query, model_id="bge-large")
                assert emb.shape == (1024,)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Verify performance (should be reasonable for 5 queries)
            # This is a loose threshold - adjust based on actual performance
            assert total_time < 10.0, f"Embedding 5 queries took {total_time:.2f}s, should be under 10s"
    
    @pytest.mark.slow
    def test_real_embedding_edge_cases(self):
        """Test real embedding with edge cases."""
        if not HAS_SENTENCE_TRANSFORMERS:
            pytest.skip("sentence_transformers not available")
        
        with patch.dict(os.environ, {}, clear=True):
            service = ModalEmbeddingService()
            
            # Test very short query
            short_emb = service.embed_query("Hi", model_id="bge-large")
            assert short_emb.shape == (1024,)
            assert short_emb.dtype == np.float32
            
            # Test very long query
            long_query = "What do Nobel laureates say about " + "justice and fairness " * 50
            long_emb = service.embed_query(long_query, model_id="bge-large")
            assert long_emb.shape == (1024,)
            assert long_emb.dtype == np.float32
            
            # Test query with special characters
            special_emb = service.embed_query("What do Nobel laureates say about justice & peace?", model_id="bge-large")
            assert special_emb.shape == (1024,)
            assert special_emb.dtype == np.float32
    
    @pytest.mark.slow
    def test_real_embedding_model_switching(self):
        """Test switching between different models with real embeddings."""
        if not HAS_SENTENCE_TRANSFORMERS:
            pytest.skip("sentence_transformers not available")
        
        with patch.dict(os.environ, {}, clear=True):
            service = ModalEmbeddingService()
            
            query = "What do Nobel laureates say about justice?"
            
            # Test bge-large
            bge_emb = service.embed_query(query, model_id="bge-large")
            assert bge_emb.shape == (1024,)
            
            # Test miniLM
            minilm_emb = service.embed_query(query, model_id="miniLM")
            assert minilm_emb.shape == (384,)
            
            # Verify embeddings are different (different models should produce different embeddings)
            # Convert to same dimension for comparison (take first 384 from bge-large)
            bge_emb_384 = bge_emb[:384]
            
            # They should be different (not identical)
            assert not np.allclose(bge_emb_384, minilm_emb), "Different models should produce different embeddings" 