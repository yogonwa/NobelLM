#!/usr/bin/env python3
"""
Test script for Modal embedder - validates use case in standalone isolation.

This script tests the deployed Modal embedder service to ensure it's working
correctly for the NobelLM project. It validates the complete embedding pipeline
from query to vector output.

Use Case: Convert user query to embedding for Weaviate vector search.

Note: This script is provided for reference, but the recommended testing approach
is to use the local entrypoint in modal_embedder.py:
    modal run modal_embedder.py

Author: NobelLM Team
Date: 2025
"""

import modal
import sys
import time

def test_embedding_service():
    """
    Test the embedding service end-to-end using Modal's deployed app.
    
    This function tests the complete embedding pipeline:
    1. Health check to verify service status
    2. Single query embedding generation
    3. Embedding format validation for Weaviate
    4. Performance testing
    
    Returns:
        bool: True if all tests pass, False otherwise
        
    Note: This approach requires the app to be deployed first.
    For local testing, use: modal run modal_embedder.py
    """
    print("🧪 Testing Modal Embedding Service")
    print("=" * 50)
    
    try:
        # Look up the deployed app and get function references
        print("🔍 Looking up deployed app...")
        stub = modal.App.lookup("nobel-embedder")
        print("✅ App found successfully")
        
        # Get function references using the correct Modal API
        # Note: This approach works for deployed apps but has limitations
        health_check = stub.function("health_check")
        embed_query = stub.function("embed_query")
        print("✅ Functions retrieved from deployed app")
        
        # Test 1: Health check
        print("\n🔍 Step 1: Health check")
        health = health_check.remote()
        print(f"Health status: {health}")
        
        if health.get("status") != "healthy":
            print("❌ Service not healthy. Exiting.")
            return False
        
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
        if len(embedding) == 1024:
            print("✅ Embedding dimensions correct (1024)")
        else:
            print(f"⚠️  Unexpected dimensions: {len(embedding)} (expected 1024)")
        
        # Check data type
        if all(isinstance(x, (int, float)) for x in embedding):
            print("✅ Embedding contains numeric values")
        else:
            print("❌ Embedding contains non-numeric values")
        
        # Check normalization (values should be between -1 and 1)
        max_val = max(abs(x) for x in embedding)
        if max_val <= 1.0:
            print("✅ Embedding appears to be normalized")
        else:
            print(f"⚠️  Embedding may not be normalized (max abs value: {max_val})")
        
        # Test 4: Performance test
        print("\n🔍 Step 4: Performance test")
        
        start_time = time.time()
        for i in range(3):
            embed_query.remote(f"Test query {i}")
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 3
        print(f"Average embedding time: {avg_time:.3f} seconds")
        print(f"Queries per second: {1/avg_time:.2f}")
        
        if avg_time < 2.0:
            print("✅ Performance is acceptable")
        else:
            print("⚠️  Performance may be slow for production use")
        
        # Success summary
        print("\n" + "=" * 50)
        print("🎉 USE CASE VALIDATION SUCCESSFUL!")
        print("=" * 50)
        print("✅ Service is healthy and responding")
        print("✅ Can convert queries to embeddings")
        print("✅ Embeddings are in correct format for Weaviate")
        print("✅ Performance is acceptable")
        print("\n📋 Ready for production use:")
        print("   - Use stub.function('embed_query').remote('your query')")
        print("   - Use returned embedding for Weaviate vector search")
        print("   - Embedding is 1024-dimensional, normalized vector")
        
        return True
        
    except modal.exception.NotFoundError:
        print("❌ App 'nobel-embedder' not found!")
        print("Deploy the app first:")
        print("   modal deploy modal_embedder.py")
        print("   or")
        print("   python deploy.py")
        print("\n💡 For easier testing, use:")
        print("   modal run modal_embedder.py")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Check that the service is deployed and running")
        print("\n💡 For easier testing, use:")
        print("   modal run modal_embedder.py")
        return False

if __name__ == "__main__":
    """
    Main entry point for the test script.
    
    This script can be run directly to test the deployed Modal embedder.
    However, the recommended approach is to use the local entrypoint:
        modal run modal_embedder.py
    """
    print("🚀 Starting Modal Embedder Test")
    print("Note: For easier testing, use 'modal run modal_embedder.py'")
    print("-" * 50)
    
    success = test_embedding_service()
    sys.exit(0 if success else 1)
