#!/usr/bin/env python3
"""
Test script to verify Modal embedder service client calls.
"""
import modal

def test_modal_client():
    """Test calling the Modal embedder service."""
    try:
        # Look up the app
        stub = modal.App.lookup("nobel-embedder")
        print("✅ Successfully connected to Modal embedder service")
        
        # Test health check
        print("Testing health check...")
        health_check = stub.function("health_check")
        health = health_check.remote()
        print(f"Health status: {health}")
        
        # Test embedding
        print("Testing embedding...")
        test_query = "What did Toni Morrison say about justice?"
        embed_query = stub.function("embed_query")
        embedding = embed_query.remote(test_query)
        print(f"✅ Got embedding with {len(embedding)} dimensions")
        print(f"First 5 values: {embedding[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_modal_client() 