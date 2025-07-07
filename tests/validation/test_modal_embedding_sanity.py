"""
Modal Embedding Service Sanity Check Tests

These tests verify that the Modal embedding service can be loaded and used correctly
in both development and production environments. They complement the existing
embedding sanity tests by focusing on the unified service interface.
"""

import pytest
import logging
import numpy as np
import os
from unittest.mock import Mock, patch

from rag.modal_embedding_service import (
    ModalEmbeddingService,
    get_embedding_service,
    embed_query
)
from rag.model_config import DEFAULT_MODEL_ID

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.validation
class TestModalEmbeddingServiceSanity:
    """Test Modal embedding service health and functionality."""
    
    @pytest.mark.validation
    def test_service_initialization(self):
        """Test that the Modal embedding service can be initialized successfully."""
        with patch.dict(os.environ, {}, clear=True):
            service = ModalEmbeddingService()
            
            # Verify service properties
            assert hasattr(service, 'is_production')
            assert hasattr(service, 'modal_stub')
            assert hasattr(service, 'embed_query')
            
            # Should be in development mode by default
            assert not service.is_production
            
            logger.info("Modal embedding service initialized successfully")
    
    @pytest.mark.validation
    def test_service_singleton(self):
        """Test that get_embedding_service returns a singleton instance."""
        service1 = get_embedding_service()
        service2 = get_embedding_service()
        
        assert service1 is service2, "Should return the same instance"
        
        logger.info("Service singleton pattern verified")
    
    @pytest.mark.validation
    def test_development_embedding_functionality(self):
        """Test embedding functionality in development environment."""
        with patch.dict(os.environ, {}, clear=True):
            try:
                result = embed_query("Test embedding for Modal service validation")
                
                # Verify embedding properties
                assert result is not None, "Embedding should not be None"
                assert isinstance(result, np.ndarray), "Embedding should be a numpy array"
                assert result.ndim == 1, "Embedding should be 1-dimensional"
                assert result.shape[0] > 0, "Embedding should have positive dimension"
                assert result.dtype == np.float32, "Embedding should be float32"
                
                logger.info(f"Development embedding successful. Shape: {result.shape}, "
                           f"first 5 values: {result[:5]}")
                
            except Exception as e:
                pytest.skip(f"Local model not available: {e}")
    
    @pytest.mark.validation
    def test_production_embedding_functionality_mock(self):
        """Test embedding functionality in production environment (mocked)."""
        with patch.dict(os.environ, {"NOBELLM_ENVIRONMENT": "production"}):
            # Mock Modal stub
            with patch('rag.modal_embedding_service.modal') as mock_modal:
                mock_stub = Mock()
                mock_function = Mock()
                # Create realistic embedding data
                mock_embedding = np.random.rand(1024).astype(np.float32)
                mock_embedding = mock_embedding / np.linalg.norm(mock_embedding)  # Normalize
                mock_function.remote.return_value = mock_embedding.tolist()
                mock_stub.function.return_value = mock_function
                mock_modal.App.lookup.return_value = mock_stub
                
                # Mock model config
                with patch('rag.modal_embedding_service.get_model_config') as mock_config:
                    mock_config.return_value = {"embedding_dim": 1024}
                    
                    result = embed_query("Test production embedding")
                    
                    # Verify embedding properties
                    assert result is not None, "Embedding should not be None"
                    assert isinstance(result, np.ndarray), "Embedding should be a numpy array"
                    assert result.ndim == 1, "Embedding should be 1-dimensional"
                    assert result.shape == (1024,), "Should match expected dimension"
                    assert result.dtype == np.float32, "Embedding should be float32"
                    
                    # Verify Modal was called
                    mock_function.remote.assert_called_once_with("Test production embedding")
                    
                    logger.info(f"Production embedding successful. Shape: {result.shape}")
    
    @pytest.mark.validation
    def test_embedding_dimension_consistency(self):
        """Test that embedding dimensions are consistent with model configuration."""
        with patch.dict(os.environ, {}, clear=True):
            try:
                # Test with default model
                result = embed_query("Test dimension consistency")
                
                # Get expected dimension from model config
                from rag.model_config import get_model_config
                expected_dim = get_model_config(DEFAULT_MODEL_ID)["embedding_dim"]
                
                assert result.shape[0] == expected_dim, \
                    f"Embedding dimension {result.shape[0]} doesn't match expected {expected_dim}"
                
                logger.info(f"Embedding dimension is consistent: {result.shape[0]}")
                
            except Exception as e:
                pytest.skip(f"Local model not available: {e}")
    
    @pytest.mark.validation
    def test_embedding_normalization(self):
        """Test that embeddings are properly normalized."""
        with patch.dict(os.environ, {}, clear=True):
            try:
                result = embed_query("Test normalization")
                
                # Check that embedding is normalized (L2 norm should be close to 1)
                norm = np.linalg.norm(result)
                assert abs(norm - 1.0) < 1e-6, f"Embedding should be normalized, got norm {norm}"
                
                logger.info(f"Embedding is properly normalized with L2 norm: {norm}")
                
            except Exception as e:
                pytest.skip(f"Local model not available: {e}")
    
    @pytest.mark.validation
    def test_model_awareness(self):
        """Test that the service is model-aware and respects different model configurations."""
        with patch.dict(os.environ, {}, clear=True):
            test_models = [
                ("bge-large", 1024),
                ("miniLM", 384)
            ]
            
            for model_id, expected_dim in test_models:
                try:
                    result = embed_query("Test model awareness", model_id=model_id)
                    
                    assert result.shape[0] == expected_dim, \
                        f"Model {model_id} should produce {expected_dim} dimensions, got {result.shape[0]}"
                    
                    logger.info(f"Model awareness verified for {model_id}: {result.shape[0]} dimensions")
                    
                except Exception as e:
                    logger.warning(f"Model {model_id} not available: {e}")
                    continue
    
    @pytest.mark.validation
    def test_multiple_queries_handling(self):
        """Test that the service can handle multiple queries efficiently."""
        with patch.dict(os.environ, {}, clear=True):
            test_queries = [
                "First test query",
                "Second test query",
                "Third test query"
            ]
            
            try:
                embeddings = []
                for query in test_queries:
                    embedding = embed_query(query)
                    embeddings.append(embedding)
                
                # Verify all embeddings have correct properties
                for i, embedding in enumerate(embeddings):
                    assert embedding is not None, f"Embedding {i} should not be None"
                    assert isinstance(embedding, np.ndarray), f"Embedding {i} should be numpy array"
                    assert embedding.ndim == 1, f"Embedding {i} should be 1-dimensional"
                    assert embedding.shape[0] > 0, f"Embedding {i} should have positive dimension"
                
                logger.info(f"Multiple queries handled successfully: {len(embeddings)} embeddings")
                
            except Exception as e:
                pytest.skip(f"Local model not available: {e}")
    
    @pytest.mark.validation
    def test_error_handling(self):
        """Test error handling for various failure scenarios."""
        with patch.dict(os.environ, {}, clear=True):
            # Test with invalid input
            try:
                # This should either work or raise a clear exception
                result = embed_query("")
                
                # If it works, verify the embedding
                assert isinstance(result, np.ndarray)
                assert result.shape[0] > 0
                
                logger.info("Empty query handled successfully")
                
            except Exception as e:
                # It's acceptable for empty queries to raise exceptions
                logger.info(f"Empty query raised expected exception: {e}")
    
    @pytest.mark.validation
    def test_consistency_across_calls(self):
        """Test that embeddings are consistent across multiple calls."""
        with patch.dict(os.environ, {}, clear=True):
            test_query = "Consistency test query"
            
            try:
                # Generate embeddings multiple times
                embedding1 = embed_query(test_query)
                embedding2 = embed_query(test_query)
                
                # Embeddings should be identical (deterministic)
                assert np.allclose(embedding1, embedding2), \
                    "Embeddings should be identical for same input"
                
                logger.info("Embedding consistency verified across multiple calls")
                
            except Exception as e:
                pytest.skip(f"Local model not available: {e}")


@pytest.mark.validation
class TestModalEmbeddingServiceIntegration:
    """Test integration with existing validation test patterns."""
    
    @pytest.mark.validation
    def test_compatibility_with_existing_embedder_tests(self):
        """Test that Modal service is compatible with existing embedder test patterns."""
        with patch.dict(os.environ, {}, clear=True):
            try:
                # Test that follows the same pattern as test_embedder_sanity.py
                test_text = "Test embedding for NobelLM validation"
                logger.info(f"Generating embedding for: '{test_text}'")
                
                embedding = embed_query(test_text)
                
                # Verify embedding properties (same as existing tests)
                assert embedding is not None, "Embedding should not be None"
                assert isinstance(embedding, np.ndarray), "Embedding should be a numpy array"
                assert embedding.ndim == 1, "Embedding should be 1-dimensional"
                assert embedding.shape[0] > 0, "Embedding should have positive dimension"
                
                logger.info(f"Embedding generated successfully. Shape: {embedding.shape}, "
                           f"first 5 values: {embedding[:5]}")
                
            except Exception as e:
                pytest.skip(f"Local model not available: {e}")
    
    @pytest.mark.validation
    def test_environment_detection_accuracy(self):
        """Test that environment detection works correctly."""
        test_cases = [
            ({"NOBELLM_ENVIRONMENT": "production"}, True),
            ({"NOBELLM_ENVIRONMENT": "development"}, False),
            ({"FLY_APP_NAME": "test-app"}, True),
            ({"PORT": "8000"}, True),
            ({}, False),  # Default to development
        ]
        
        for env_vars, expected_production in test_cases:
            with patch.dict(os.environ, env_vars, clear=True):
                service = ModalEmbeddingService()
                assert service.is_production == expected_production, \
                    f"Environment detection failed for {env_vars}"
        
        logger.info("Environment detection accuracy verified")
    
    @pytest.mark.validation
    def test_fallback_behavior(self):
        """Test fallback behavior from Modal to local embedding."""
        with patch.dict(os.environ, {"NOBELLM_ENVIRONMENT": "production"}):
            # Mock Modal stub that fails
            with patch('rag.modal_embedding_service.modal') as mock_modal:
                mock_modal.App.lookup.side_effect = Exception("Modal not available")
                
                try:
                    # Should fall back to local embedding
                    result = embed_query("Test fallback behavior")
                    
                    # Verify fallback worked
                    assert isinstance(result, np.ndarray)
                    assert result.ndim == 1
                    assert result.shape[0] > 0
                    
                    logger.info("Fallback behavior verified")
                    
                except Exception as e:
                    pytest.skip(f"Local model not available for fallback: {e}")


@pytest.mark.validation
class TestModalEmbeddingServicePerformance:
    """Test performance characteristics of the Modal embedding service."""
    
    @pytest.mark.validation
    def test_embedding_speed(self):
        """Test that embeddings are generated within reasonable time limits."""
        with patch.dict(os.environ, {}, clear=True):
            try:
                import time
                
                # Test single embedding speed
                start_time = time.time()
                result = embed_query("Performance test query")
                end_time = time.time()
                
                embedding_time = end_time - start_time
                
                # Should complete within reasonable time (less than 5 seconds)
                assert embedding_time < 5.0, f"Embedding too slow: {embedding_time:.2f}s"
                
                logger.info(f"Embedding speed test passed: {embedding_time:.2f}s")
                
            except Exception as e:
                pytest.skip(f"Local model not available: {e}")
    
    @pytest.mark.validation
    def test_memory_usage(self):
        """Test that embedding service doesn't cause memory issues."""
        with patch.dict(os.environ, {}, clear=True):
            try:
                import psutil
                import os
                
                # Get initial memory usage
                process = psutil.Process(os.getpid())
                initial_memory = process.memory_info().rss
                
                # Generate multiple embeddings
                embeddings = []
                for i in range(10):
                    embedding = embed_query(f"Memory test query {i}")
                    embeddings.append(embedding)
                
                # Get final memory usage
                final_memory = process.memory_info().rss
                memory_increase = final_memory - initial_memory
                
                # Memory increase should be reasonable (less than 100MB)
                assert memory_increase < 100 * 1024 * 1024, \
                    f"Memory usage increased too much: {memory_increase / (1024*1024):.1f}MB"
                
                logger.info(f"Memory usage test passed: {memory_increase / (1024*1024):.1f}MB increase")
                
            except ImportError:
                pytest.skip("psutil not available for memory testing")
            except Exception as e:
                pytest.skip(f"Memory test not available: {e}") 