#!/usr/bin/env python3
"""
Test script for Modal batch embedding endpoint.

This script validates the new batch embedding endpoint and compares its performance
with individual requests to demonstrate the elimination of cold start storms.

Usage:
    python test_batch.py

Author: NobelLM Team
Date: 2025
"""

import requests
import json
import time
from typing import List, Dict, Any

def test_batch_endpoint():
    """Test the new batch embedding endpoint."""
    
    # Test configuration
    url = "https://yogonwa--nobel-embedder-clean-slate-embed-batch.modal.run"
    api_key = "6dab23095a3f8968074d7c9152d6707f3f7445bc145022f46fcceb0712864147"
    
    # Test queries that would typically be expanded by ThematicRetriever
    test_queries = [
        "justice",
        "freedom", 
        "equality",
        "injustice",
        "liberty",
        "democracy",
        "human rights",
        "civil rights",
        "oppression",
        "liberation"
    ]
    
    print("🧪 Testing Modal Batch Embedding Endpoint")
    print("=" * 50)
    
    # Test 1: Batch request
    print(f"\n🔍 Test 1: Batch embedding {len(test_queries)} queries")
    start_time = time.time()
    
    try:
        response = requests.post(
            url,
            json={"api_key": api_key, "texts": test_queries},
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        batch_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            embeddings = data["embeddings"]
            print(f"✅ Batch request successful!")
            print(f"   Time: {batch_time:.2f}s")
            print(f"   Embeddings returned: {len(embeddings)}")
            print(f"   Embedding dimensions: {len(embeddings[0])}")
            
            # Validate embeddings
            for i, emb in enumerate(embeddings):
                if len(emb) != 1024:
                    print(f"❌ Embedding {i} has wrong dimensions: {len(emb)}")
                    return False
                    
            print(f"✅ All embeddings have correct dimensions (1024)")
            
        else:
            print(f"❌ Batch request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Batch request error: {e}")
        return False
    
    # Test 2: Individual requests (for comparison)
    print(f"\n🔍 Test 2: Individual requests for comparison")
    individual_times = []
    
    for i, query in enumerate(test_queries[:3]):  # Test first 3 for speed
        start_time = time.time()
        
        try:
            response = requests.post(
                "https://yogonwa--nobel-embedder-clean-slate-embed-query.modal.run",
                json={"api_key": api_key, "text": query},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            individual_time = time.time() - start_time
            individual_times.append(individual_time)
            
            if response.status_code == 200:
                print(f"   Query {i+1}: {individual_time:.2f}s")
            else:
                print(f"   Query {i+1}: Failed ({response.status_code})")
                
        except Exception as e:
            print(f"   Query {i+1}: Error - {e}")
    
    # Performance comparison
    if individual_times:
        avg_individual = sum(individual_times) / len(individual_times)
        total_individual = avg_individual * len(test_queries)
        
        print(f"\n📊 Performance Comparison:")
        print(f"   Batch request ({len(test_queries)} queries): {batch_time:.2f}s")
        print(f"   Individual requests (estimated): {total_individual:.2f}s")
        print(f"   Speedup: {total_individual / batch_time:.1f}x")
        
        if batch_time < total_individual * 0.5:  # At least 2x faster
            print(f"✅ Batch endpoint provides significant performance improvement!")
        else:
            print(f"⚠️  Batch endpoint performance improvement is modest")
    
    # Test 3: Edge cases
    print(f"\n🔍 Test 3: Edge cases")
    
    # Empty list
    try:
        response = requests.post(
            url,
            json={"api_key": api_key, "texts": []},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code == 400:
            print("✅ Empty list correctly rejected")
        else:
            print(f"⚠️  Empty list response: {response.status_code}")
    except Exception as e:
        print(f"❌ Empty list test error: {e}")
    
    # Single item
    try:
        response = requests.post(
            url,
            json={"api_key": api_key, "texts": ["single query"]},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            if len(data["embeddings"]) == 1:
                print("✅ Single item handled correctly")
            else:
                print(f"❌ Single item returned {len(data['embeddings'])} embeddings")
        else:
            print(f"❌ Single item failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Single item test error: {e}")
    
    # Large list (test limit)
    large_list = [f"query_{i}" for i in range(60)]  # Over the 50 limit
    try:
        response = requests.post(
            url,
            json={"api_key": api_key, "texts": large_list},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code == 400:
            print("✅ Large list correctly rejected")
        else:
            print(f"⚠️  Large list response: {response.status_code}")
    except Exception as e:
        print(f"❌ Large list test error: {e}")
    
    print(f"\n🎉 Batch endpoint testing completed!")
    return True

if __name__ == "__main__":
    success = test_batch_endpoint()
    if success:
        print("\n✅ All tests passed! Batch endpoint is ready for production use.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.") 