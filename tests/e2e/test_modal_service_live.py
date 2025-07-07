#!/usr/bin/env python3
"""
Live Modal Service E2E Test

This test validates the deployed Modal embedder service end-to-end.
It tests the complete embedding pipeline from query to vector output
using the actual deployed Modal service.

Use Case: Convert user query to embedding for Weaviate vector search.

Note: This test requires the Modal service to be deployed:
    modal deploy modal_embedder.py

Author: NobelLM Team
Date: 2025
"""

import pytest
import modal
import time
import numpy as np
import os

@pytest.mark.e2e
@pytest.mark.skipif(
    os.getenv("NOBELLM_TEST_MODAL_LIVE") != "1", 
    reason="Live Modal service test skipped unless NOBELLM_TEST_MODAL_LIVE=1"
)
def test_modal_service_live():
    """
    Live E2E test for deployed Modal embedding service.
    
    This test validates the complete embedding pipeline:
    1. Health check to verify service status
    2. Single query embedding generation
    3. Embedding format validation for Weaviate
    4. Performance testing
    
    Requires:
        - Modal service deployed: modal deploy modal_embedder.py
        - Environment variable: NOBELLM_TEST_MODAL_LIVE=1
    """
    print("🧪 Testing Live Modal Embedding Service")
    print("=" * 50)
    
    try:
        # Look up the deployed app and get function references
        print("🔍 Looking up deployed app...")
        stub = modal.App.lookup("nobel-embedder")
        print("✅ App found successfully")
        
        # Get function references using the correct Modal API
        health_check = stub.function("health_check")
        embed_query = stub.function("embed_query")
        print("✅ Functions retrieved from deployed app")
        
        # Test 1: Health check
        print("\n🔍 Step 1: Health check")
        health = health_check.remote()
        print(f"Health status: {health}")
        
        assert health.get("status") == "healthy", f"Service not healthy: {health}"
        assert health.get("model_loaded") == True, "Model not loaded"
        assert health.get("embedding_dimensions") == 1024, "Wrong embedding dimensions"
        
        print("✅ Service is healthy!")
        
        # Test 2: Single query embedding
        print("\n🔍 Step 2: Single query embedding")
        test_query = "What did Toni Morrison say about justice and race in America?"
        
        print(f"Query: '{test_query}'")
        embedding = embed_query.remote(test_query)
        
        print(f"✅ Got embedding with {len(embedding)} dimensions")
        print(f"First 5 values: {embedding[:5]}")
        print(f"Embedding type: {type(embedding[0])}")
        
        # Test 3: Validate embedding format for Weaviate
        print("\n🔍 Step 3: Validate embedding format for Weaviate")
        
        # Check dimensions (BGE-large-en-v1.5 should be 1024)
        assert len(embedding) == 1024, f"Wrong dimensions: {len(embedding)} (expected 1024)"
        print("✅ Embedding dimensions correct (1024)")
        
        # Check data type
        assert all(isinstance(x, (int, float)) for x in embedding), "Non-numeric values in embedding"
        print("✅ Embedding contains numeric values")
        
        # Check normalization (values should be between -1 and 1)
        max_val = max(abs(x) for x in embedding)
        assert max_val <= 1.0, f"Embedding not normalized, max abs value: {max_val}"
        print("✅ Embedding appears to be normalized")
        
        # Test 4: Performance test
        print("\n🔍 Step 4: Performance test")
        
        start_time = time.time()
        for i in range(3):
            embed_query.remote(f"Test query {i}")
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 3
        print(f"Average embedding time: {avg_time:.3f} seconds")
        print(f"Queries per second: {1/avg_time:.2f}")
        
        assert avg_time < 2.0, f"Performance too slow: {avg_time:.3f}s average"
        print("✅ Performance is acceptable")
        
        # Test 5: Consistency test
        print("\n🔍 Step 5: Consistency test")
        
        # Test that same query produces same embedding
        embedding1 = embed_query.remote(test_query)
        embedding2 = embed_query.remote(test_query)
        
        # Convert to numpy for comparison
        emb1_np = np.array(embedding1)
        emb2_np = np.array(embedding2)
        
        # Check that embeddings are identical (within floating point precision)
        assert np.allclose(emb1_np, emb2_np), "Embeddings not consistent for same query"
        print("✅ Embedding consistency verified")
        
        # Success summary
        print("\n" + "=" * 50)
        print("🎉 LIVE MODAL SERVICE TEST SUCCESSFUL!")
        print("=" * 50)
        print("✅ Service is healthy and responding")
        print("✅ Can convert queries to embeddings")
        print("✅ Embeddings are in correct format for Weaviate")
        print("✅ Performance is acceptable")
        print("✅ Embeddings are consistent")
        print("\n📋 Ready for production use:")
        print("   - Use stub.function('embed_query').remote('your query')")
        print("   - Use returned embedding for Weaviate vector search")
        print("   - Embedding is 1024-dimensional, normalized vector")
        
    except modal.exception.NotFoundError:
        pytest.skip("Modal app 'nobel-embedder' not found! Deploy with: modal deploy modal_embedder.py")
        
    except Exception as e:
        pytest.fail(f"Live Modal service test failed: {e}")


@pytest.mark.e2e
@pytest.mark.skipif(
    os.getenv("NOBELLM_TEST_MODAL_LIVE") != "1", 
    reason="Live Modal service test skipped unless NOBELLM_TEST_MODAL_LIVE=1"
)
def test_modal_service_health_only():
    """
    Quick health check for Modal service.
    
    This is a lightweight test that only checks if the service is deployed
    and responding, without running full embedding tests.
    """
    try:
        stub = modal.App.lookup("nobel-embedder")
        health_check = stub.function("health_check")
        health = health_check.remote()
        
        assert health.get("status") == "healthy", f"Service not healthy: {health}"
        print("✅ Modal service health check passed")
        
    except modal.exception.NotFoundError:
        pytest.skip("Modal app 'nobel-embedder' not found! Deploy with: modal deploy modal_embedder.py")
        
    except Exception as e:
        pytest.fail(f"Modal service health check failed: {e}")
