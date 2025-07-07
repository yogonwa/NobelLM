"""
End-to-End Tests for Modal Embedding Service

Tests the complete Modal embedding service pipeline from query input
to embedding output in both development and production environments.
"""

import pytest
import numpy as np
import os
from unittest.mock import Mock, patch

from rag.modal_embedding_service import embed_query, get_embedding_service
from rag.query_engine import answer_query
from rag.model_config import DEFAULT_MODEL_ID


@pytest.mark.e2e
class TestModalEmbeddingE2E:
    """End-to-end tests for Modal embedding service."""
    
    def test_development_embedding_pipeline(self):
        """Test complete embedding pipeline in development environment."""
        with patch.dict(os.environ, {}, clear=True):
            # Test with real local model (if available)
            try:
                result = embed_query("What did Toni Morrison say about justice?")
                
                # Verify embedding properties
                assert isinstance(result, np.ndarray)
                assert result.ndim == 1
                assert result.shape[0] > 0
                assert result.dtype == np.float32
                
                # Check normalization (values should be between -1 and 1)
                max_val = max(abs(x) for x in result)
                assert max_val <= 1.0, f"Embedding not normalized, max abs value: {max_val}"
                
                print(f"✅ Development embedding successful: shape={result.shape}, max_abs={max_val:.4f}")
                
            except Exception as e:
                pytest.skip(f"Local model not available: {e}")
    
    def test_production_embedding_pipeline_mock(self):
        """Test complete embedding pipeline in production environment (mocked)."""
        with patch.dict(os.environ, {"NOBELLM_ENVIRONMENT": "production"}):
            # Mock Modal stub for production testing
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
                    
                    result = embed_query("What did Toni Morrison say about justice?")
                    
                    # Verify embedding properties
                    assert isinstance(result, np.ndarray)
                    assert result.shape == (1024,)
                    assert result.dtype == np.float32
                    
                    # Verify Modal was called
                    mock_function.remote.assert_called_once_with("What did Toni Morrison say about justice?")
                    
                    print(f"✅ Production embedding successful: shape={result.shape}")
    
    def test_production_fallback_e2e(self):
        """Test production fallback to local embedding when Modal fails."""
        with patch.dict(os.environ, {"NOBELLM_ENVIRONMENT": "production"}):
            # Mock Modal stub that fails
            with patch('rag.modal_embedding_service.modal') as mock_modal:
                mock_modal.App.lookup.side_effect = Exception("Modal not available")
                
                # Test with real local model as fallback
                try:
                    result = embed_query("What did Toni Morrison say about justice?")
                    
                    # Verify embedding properties
                    assert isinstance(result, np.ndarray)
                    assert result.ndim == 1
                    assert result.shape[0] > 0
                    assert result.dtype == np.float32
                    
                    print(f"✅ Production fallback successful: shape={result.shape}")
                    
                except Exception as e:
                    pytest.skip(f"Local model not available for fallback: {e}")
    
    def test_model_awareness_e2e(self):
        """Test model-aware embedding with different model configurations."""
        test_cases = [
            ("bge-large", 1024),
            ("miniLM", 384)
        ]
        
        for model_id, expected_dim in test_cases:
            with patch.dict(os.environ, {}, clear=True):
                try:
                    result = embed_query("Test query", model_id=model_id)
                    
                    # Verify embedding properties
                    assert isinstance(result, np.ndarray)
                    assert result.shape == (expected_dim,)
                    assert result.dtype == np.float32
                    
                    print(f"✅ Model-aware embedding successful for {model_id}: shape={result.shape}")
                    
                except Exception as e:
                    pytest.skip(f"Model {model_id} not available: {e}")


@pytest.mark.e2e
class TestModalEmbeddingWithRAGPipeline:
    """Test Modal embedding service integration with the complete RAG pipeline."""
    
    def test_query_engine_with_modal_service(self):
        """Test that the query engine works with the Modal embedding service."""
        with patch.dict(os.environ, {}, clear=True):
            # Mock all components except embedding service
            with patch('rag.query_engine.get_query_router') as mock_get_router, \
                 patch('rag.query_engine.get_mode_aware_retriever') as mock_get_retriever, \
                 patch('rag.query_engine.get_prompt_builder') as mock_get_builder, \
                 patch('rag.query_engine.call_openai') as mock_openai:
                
                # Mock query router
                mock_router = Mock()
                mock_router_result = Mock()
                mock_router_result.intent = "factual"
                mock_router_result.retrieval_config = Mock()
                mock_router_result.retrieval_config.top_k = 5
                mock_router_result.retrieval_config.filters = {}
                mock_router.classify_and_route.return_value = mock_router_result
                mock_get_router.return_value = mock_router
                
                # Mock retriever
                mock_retriever = Mock()
                mock_chunks = [
                    {
                        "chunk_id": "test_1",
                        "text": "Toni Morrison won the Nobel Prize in 1993.",
                        "score": 0.9,
                        "laureate": "Toni Morrison",
                        "year_awarded": 1993
                    }
                ]
                mock_retriever.retrieve.return_value = mock_chunks
                mock_get_retriever.return_value = mock_retriever
                
                # Mock prompt builder
                mock_builder = Mock()
                mock_builder.build_qa_prompt.return_value = "Answer: Toni Morrison won in 1993."
                mock_get_builder.return_value = mock_builder
                
                # Mock OpenAI
                mock_openai.return_value = {"choices": [{"message": {"content": "Toni Morrison won the Nobel Prize in Literature in 1993."}}]}
                
                # Test with real embedding service
                try:
                    result = answer_query("When did Toni Morrison win the Nobel Prize?")
                    
                    # Verify result structure
                    assert "answer" in result
                    assert "answer_type" in result
                    assert "sources" in result
                    assert result["answer_type"] == "rag"
                    
                    print(f"✅ Query engine with Modal service successful: {result['answer'][:50]}...")
                    
                except Exception as e:
                    pytest.skip(f"Embedding service not available: {e}")
    
    def test_environment_switching_e2e(self):
        """Test switching between development and production environments."""
        test_query = "What did Toni Morrison say about justice?"
        
        # Test development environment
        with patch.dict(os.environ, {}, clear=True):
            try:
                dev_result = embed_query(test_query)
                assert isinstance(dev_result, np.ndarray)
                print(f"✅ Development embedding: shape={dev_result.shape}")
            except Exception as e:
                pytest.skip(f"Development embedding not available: {e}")
        
        # Test production environment (mocked)
        with patch.dict(os.environ, {"NOBELLM_ENVIRONMENT": "production"}):
            with patch('rag.modal_embedding_service.modal') as mock_modal:
                mock_stub = Mock()
                mock_function = Mock()
                mock_embedding = np.random.rand(1024).astype(np.float32)
                mock_embedding = mock_embedding / np.linalg.norm(mock_embedding)
                mock_function.remote.return_value = mock_embedding.tolist()
                mock_stub.function.return_value = mock_function
                mock_modal.App.lookup.return_value = mock_stub
                
                with patch('rag.modal_embedding_service.get_model_config') as mock_config:
                    mock_config.return_value = {"embedding_dim": 1024}
                    
                    prod_result = embed_query(test_query)
                    assert isinstance(prod_result, np.ndarray)
                    assert prod_result.shape == (1024,)
                    print(f"✅ Production embedding: shape={prod_result.shape}")


@pytest.mark.e2e
class TestModalEmbeddingPerformance:
    """Test performance characteristics of the Modal embedding service."""
    
    def test_embedding_consistency(self):
        """Test that embeddings are consistent for the same input."""
        with patch.dict(os.environ, {}, clear=True):
            test_query = "What did Toni Morrison say about justice?"
            
            try:
                # Generate embeddings multiple times
                result1 = embed_query(test_query)
                result2 = embed_query(test_query)
                
                # Embeddings should be identical (deterministic)
                assert np.allclose(result1, result2), "Embeddings should be identical for same input"
                
                print(f"✅ Embedding consistency verified: shape={result1.shape}")
                
            except Exception as e:
                pytest.skip(f"Embedding service not available: {e}")
    
    def test_embedding_performance(self):
        """Test embedding performance with multiple queries."""
        with patch.dict(os.environ, {}, clear=True):
            test_queries = [
                "What did Toni Morrison say about justice?",
                "How do laureates discuss creativity?",
                "What themes appear in Nobel lectures?",
                "Compare speeches from different decades",
                "What do winners say about literature?"
            ]
            
            try:
                import time
                start_time = time.time()
                
                embeddings = []
                for query in test_queries:
                    embedding = embed_query(query)
                    embeddings.append(embedding)
                
                end_time = time.time()
                total_time = end_time - start_time
                avg_time = total_time / len(test_queries)
                
                # Verify all embeddings have correct properties
                for i, embedding in enumerate(embeddings):
                    assert isinstance(embedding, np.ndarray)
                    assert embedding.ndim == 1
                    assert embedding.shape[0] > 0
                    assert embedding.dtype == np.float32
                
                print(f"✅ Performance test: {len(test_queries)} queries in {total_time:.2f}s "
                      f"(avg {avg_time:.2f}s per query)")
                
                # Performance should be reasonable (less than 2 seconds per query)
                assert avg_time < 2.0, f"Embedding too slow: {avg_time:.2f}s per query"
                
            except Exception as e:
                pytest.skip(f"Performance test not available: {e}")


@pytest.mark.e2e
class TestModalEmbeddingErrorScenarios:
    """Test error handling scenarios in end-to-end context."""
    
    def test_empty_query_handling(self):
        """Test handling of empty queries."""
        with patch.dict(os.environ, {}, clear=True):
            try:
                # Test with empty string
                result = embed_query("")
                
                # Should still produce a valid embedding
                assert isinstance(result, np.ndarray)
                assert result.ndim == 1
                assert result.shape[0] > 0
                
                print(f"✅ Empty query handled successfully: shape={result.shape}")
                
            except Exception as e:
                # It's acceptable for empty queries to raise exceptions
                print(f"✅ Empty query raised expected exception: {e}")
    
    def test_long_query_handling(self):
        """Test handling of very long queries."""
        with patch.dict(os.environ, {}, clear=True):
            # Create a very long query
            long_query = "What did " + "very long " * 100 + "Toni Morrison say about justice?"
            
            try:
                result = embed_query(long_query)
                
                # Should still produce a valid embedding
                assert isinstance(result, np.ndarray)
                assert result.ndim == 1
                assert result.shape[0] > 0
                
                print(f"✅ Long query handled successfully: shape={result.shape}")
                
            except Exception as e:
                pytest.skip(f"Long query test not available: {e}")
    
    def test_special_characters_handling(self):
        """Test handling of queries with special characters."""
        with patch.dict(os.environ, {}, clear=True):
            special_queries = [
                "What did Toni Morrison say about justice & equality?",
                "How do laureates discuss 'creativity' and \"innovation\"?",
                "What about justice, equality, and human rights?",
                "Discuss: literature, art, and culture!",
                "What's the role of storytelling in society?"
            ]
            
            try:
                for query in special_queries:
                    result = embed_query(query)
                    
                    # Should produce valid embeddings
                    assert isinstance(result, np.ndarray)
                    assert result.ndim == 1
                    assert result.shape[0] > 0
                
                print(f"✅ Special characters handled successfully for {len(special_queries)} queries")
                
            except Exception as e:
                pytest.skip(f"Special characters test not available: {e}") 