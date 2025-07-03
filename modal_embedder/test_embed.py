import modal
import time

def test_embedder():
    try:
        print("🔍 Looking up deployed app...")
        stub = modal.App.lookup("nobel-embedder")
        
        # Test health check first
        print("🏥 Running health check...")
        health_check = stub.function("health_check")
        health_result = health_check.remote()
        print(f"Health status: {health_result}")
        
        if health_result.get("status") != "healthy":
            print("❌ Service is unhealthy, aborting test")
            return
        
        # Test embedding function
        print("🧠 Testing embedding function...")
        embed_query = stub.function("embed_query")
        
        # Test with different queries
        test_queries = [
            "What did Toni Morrison say about justice?",
            "How does literature reflect society?",
            "The importance of storytelling in human culture"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: {query[:50]}...")
            
            start_time = time.time()
            result = embed_query.remote(query)
            end_time = time.time()
            
            print(f"✅ Got embedding with {len(result)} dimensions")
            print(f"⏱️  Time taken: {end_time - start_time:.2f} seconds")
            print(f"🔢 First 5 values: {result[:5]}")
            
            # Validate embedding
            if len(result) != 1024:  # BAAI/bge-large-en-v1.5 has 1024 dimensions
                print(f"⚠️  Warning: Expected 1024 dimensions, got {len(result)}")
            
            # Small delay between requests
            time.sleep(0.5)
        
        print("\n🎉 All tests completed successfully!")
        
    except modal.NotFoundError:
        print("❌ App 'nobel-embedder' not found. Make sure to deploy it first with:")
        print("   modal deploy modal_embedder.py")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    test_embedder()
