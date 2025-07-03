# modal_embedder.py - Production version with volume storage

import modal
from sentence_transformers import SentenceTransformer
import os
from pathlib import Path

# Name your Modal app
app = modal.App("nobel-embedder")

# Create a volume to store the model
model_volume = modal.Volume.from_name("bge-model-cache", create_if_missing=True)

# Path where model will be stored in the volume
MODEL_CACHE_PATH = "/cache/models"
MODEL_NAME = "BAAI/bge-large-en-v1.5"

# Define the Modal image with minimal dependencies
image = (
    modal.Image.debian_slim()
    .pip_install(
        "sentence-transformers",
        "torch",
        "transformers",
        "numpy"
    )
)

@app.function(
    image=image,
    volumes={MODEL_CACHE_PATH: model_volume},
    memory=1024,  # Reduced since model is cached
    timeout=60,   # Shorter timeout for faster failures
)
def download_and_cache_model():
    """
    Download and cache the model to volume storage.
    This only needs to be run once or when updating the model.
    """
    print(f"Downloading model {MODEL_NAME} to volume...")
    
    # Download model to volume
    model = SentenceTransformer(MODEL_NAME, cache_folder=MODEL_CACHE_PATH)
    
    # Test the model works
    test_embedding = model.encode(["test"], normalize_embeddings=True)
    print(f"✅ Model cached successfully. Test embedding shape: {test_embedding.shape}")
    
    # Commit changes to volume
    model_volume.commit()
    
    return f"Model {MODEL_NAME} cached to volume"

@app.function(
    image=image,
    volumes={MODEL_CACHE_PATH: model_volume},
    memory=2048,
    timeout=300,
    # Keep containers warm for better performance
    min_containers=1,
)
@modal.concurrent(max_inputs=10)  # Allow concurrent requests
def embed_query(text: str) -> list[float]:
    """
    Generate embedding for a single query text.
    Optimized for RAG query embedding.
    
    Args:
        text: User query text to embed
        
    Returns:
        List of float values representing the embedding (1024 dimensions)
    """
    # Load model from volume cache
    model = SentenceTransformer(MODEL_NAME, cache_folder=MODEL_CACHE_PATH)
    
    # Generate embedding
    embedding = model.encode([text], normalize_embeddings=True)[0]
    
    return embedding.tolist()

@app.function(
    image=image,
    volumes={MODEL_CACHE_PATH: model_volume},
    memory=2048,
    timeout=300,
    min_containers=1,
)
@modal.concurrent(max_inputs=10)
def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts in a batch.
    Useful for indexing documents or processing multiple queries.
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embeddings, each embedding is a list of float values
    """
    model = SentenceTransformer(MODEL_NAME, cache_folder=MODEL_CACHE_PATH)
    embeddings = model.encode(texts, normalize_embeddings=True)
    return [embedding.tolist() for embedding in embeddings]

@app.function(
    image=image,
    volumes={MODEL_CACHE_PATH: model_volume},
    memory=2048,
    timeout=300,
    min_containers=1,
)
@modal.concurrent(max_inputs=100)  # Higher concurrency for health checks
def health_check() -> dict:
    """
    Health check endpoint for monitoring.
    """
    try:
        # Quick test embedding
        model = SentenceTransformer(MODEL_NAME, cache_folder=MODEL_CACHE_PATH)
        test_embedding = model.encode(["health check"], normalize_embeddings=True)
        
        return {
            "status": "healthy",
            "model_loaded": True,
            "embedding_dimensions": len(test_embedding[0]),
            "model_name": MODEL_NAME
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "model_loaded": False
        }

# Optimized for RAG workloads
@app.function(
    image=image,
    volumes={MODEL_CACHE_PATH: model_volume},
    memory=3072,  # More memory for better performance
    timeout=300,
    min_containers=2,  # Keep 2 containers warm
)
@modal.concurrent(max_inputs=20)
def embed_rag_query(
    query: str, 
    instruction: str = "Represent this sentence for searching relevant passages:"
) -> list[float]:
    """
    Optimized embedding function specifically for RAG queries.
    Uses instruction-based embedding for better retrieval performance.
    
    Args:
        query: User query text
        instruction: Instruction prefix for better embedding quality
        
    Returns:
        Normalized embedding vector for similarity search
    """
    model = SentenceTransformer(MODEL_NAME, cache_folder=MODEL_CACHE_PATH)
    
    # BGE models benefit from instruction prefixes
    formatted_query = f"{instruction} {query}"
    
    embedding = model.encode([formatted_query], normalize_embeddings=True)[0]
    
    return embedding.tolist()

# Setup and maintenance functions
@app.local_entrypoint()
def setup():
    """Setup the model cache - run this once after deployment"""
    print("Setting up model cache...")
    result = download_and_cache_model.remote()
    print(result)
    
    # Test the cached model
    print("Testing cached model...")
    test_result = embed_query.remote("What is artificial intelligence?")
    print(f"✅ Test successful! Embedding dimensions: {len(test_result)}")

@app.local_entrypoint()
def test_rag_pipeline():
    """Test the RAG-optimized embedding function"""
    queries = [
        "What did Toni Morrison say about justice?",
        "How does climate change affect biodiversity?",
        "What are the latest developments in quantum computing?"
    ]
    
    print("Testing RAG query embedding...")
    for query in queries:
        result = embed_rag_query.remote(query)
        print(f"Query: {query}")
        print(f"✅ Embedding dimensions: {len(result)}")
        print(f"First 5 values: {result[:5]}")
        print("-" * 50)

@app.local_entrypoint() 
def benchmark():
    """Benchmark the embedding performance"""
    import time
    
    query = "What is the impact of artificial intelligence on society?"
    
    # Warm up
    embed_query.remote(query)
    
    # Benchmark
    start_time = time.time()
    for i in range(10):
        embed_query.remote(query)
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 10
    print(f"Average embedding time: {avg_time:.3f} seconds")
    print(f"Queries per second: {1/avg_time:.2f}")