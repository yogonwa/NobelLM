#!/usr/bin/env python3
"""
Modal Embedder Service for NobelLM

This module provides a cloud-based embedding service using Modal and the BGE-large-en-v1.5 model.
It converts text queries into 1024-dimensional embeddings suitable for vector search in Weaviate.

Key Features:
- Cloud-based embedding generation using Modal
- BGE-large-en-v1.5 model for high-quality embeddings
- Automatic model caching and normalization
- Health check endpoint for monitoring
- Local testing entrypoint

Usage:
    # Deploy the service
    modal deploy modal_embedder.py
    
    # Test locally
    modal run modal_embedder.py
    
    # Use in production
    from modal_embedder import embed_query
    embedding = embed_query.remote("your query here")

Author: NobelLM Team
Date: 2025
"""

import modal
from sentence_transformers import SentenceTransformer
import logging

# Configure logging for debugging and monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Modal app instance
app = modal.App("nobel-embedder")

def download_model():
    """
    Preload function to download the BGE-large-en-v1.5 model at build time.
    
    This function is executed during the Modal image build process to ensure
    the model is available when the container starts, reducing cold start times.
    
    Returns:
        SentenceTransformer: The loaded model instance
        
    Raises:
        Exception: If model download fails
    """
    try:
        logger.info("Downloading BAAI/bge-large-en-v1.5 model...")
        model = SentenceTransformer("BAAI/bge-large-en-v1.5")
        logger.info("Model downloaded successfully")
        return model
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        raise

# Define the Modal container image with all necessary dependencies
# This image includes the model preloaded for faster startup times
image = (
    modal.Image.debian_slim()
    .pip_install([
        "sentence-transformers",  # For BGE model
        "torch",                  # PyTorch backend
        "transformers",           # Hugging Face transformers
        "numpy",                  # Numerical computing
        "scikit-learn"            # Additional ML utilities
    ])
    .run_function(download_model)  # Preload model during build
)

# Global variable to cache the model instance across function calls
# This improves performance by avoiding repeated model loading
model = None

@app.function(image=image)
def embed_query(text: str) -> list:
    """
    Convert a text query into a 1024-dimensional embedding vector.
    
    This function uses the BGE-large-en-v1.5 model to generate embeddings
    that are normalized and suitable for vector similarity search in Weaviate.
    
    Args:
        text (str): The input text to embed. Must be non-empty.
        
    Returns:
        list: A 1024-dimensional list of floats representing the embedding.
              Values are normalized to the range [-1, 1].
              
    Raises:
        ValueError: If input is empty or not a string
        Exception: If embedding generation fails
        
    Example:
        >>> embedding = embed_query.remote("What did Toni Morrison say about justice?")
        >>> len(embedding)  # 1024
        >>> max(abs(x) for x in embedding) <= 1.0  # True (normalized)
    """
    global model
    
    try:
        # Load model once and cache it for subsequent calls
        if model is None:
            logger.info("Loading model...")
            model = SentenceTransformer("BAAI/bge-large-en-v1.5")
            logger.info("Model loaded successfully")
        
        # Validate input to prevent errors
        if not text or not isinstance(text, str):
            raise ValueError("Input must be a non-empty string")
        
        # Generate embedding with normalization enabled
        # normalize_embeddings=True ensures values are in [-1, 1] range
        embedding = model.encode([text], normalize_embeddings=True)[0]
        return embedding.tolist()
        
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise

@app.function(image=image)
def health_check() -> dict:
    """
    Check the health and status of the embedding service.
    
    This function verifies that the model is loaded correctly and can
    generate embeddings. It's useful for monitoring and debugging.
    
    Returns:
        dict: Health status information including:
            - status: "healthy" or "unhealthy"
            - model_loaded: Boolean indicating if model is available
            - embedding_dimensions: Number of dimensions (should be 1024)
            - model_name: Name of the loaded model
            - error: Error message if unhealthy
            
    Example:
        >>> health = health_check.remote()
        >>> health["status"]  # "healthy"
        >>> health["embedding_dimensions"]  # 1024
    """
    try:
        global model
        # Load model if not already loaded
        if model is None:
            model = SentenceTransformer("BAAI/bge-large-en-v1.5")
        
        # Test embedding generation with a simple query
        test_embedding = model.encode(["test"], normalize_embeddings=True)[0]
        
        return {
            "status": "healthy",
            "model_loaded": model is not None,
            "embedding_dimensions": len(test_embedding),
            "model_name": "BAAI/bge-large-en-v1.5"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.local_entrypoint()
def main():
    """
    Local entrypoint for testing the embedder functions.
    
    This function provides a comprehensive test of the embedding service,
    including health checks and embedding generation validation.
    
    Run with: modal run modal_embedder.py
    
    The test validates:
    - Service health and model loading
    - Embedding generation with correct dimensions (1024)
    - Embedding normalization (values in [-1, 1] range)
    - Error handling and logging
    """
    print("🧪 Testing Modal Embedding Service")
    print("=" * 50)
    
    try:
        # Test 1: Health check
        print("\n🔍 Step 1: Health check")
        health = health_check.remote()
        print(f"Health status: {health}")
        
        if health.get("status") != "healthy":
            print("❌ Service not healthy. Exiting.")
            return
        
        print("✅ Service is healthy!")
        
        # Test 2: Embedding generation
        print("\n🔍 Step 2: Single query embedding")
        test_query = "What did Toni Morrison say about justice and race in America?"
        print(f"Query: '{test_query}'")
        
        embedding = embed_query.remote(test_query)
        print(f"✅ Got embedding with {len(embedding)} dimensions")
        print(f"First 5 values: {embedding[:5]}")
        
        # Test 3: Validate embedding properties
        if len(embedding) == 1024:
            print("✅ Embedding dimensions correct (1024)")
        else:
            print(f"⚠️  Unexpected dimensions: {len(embedding)} (expected 1024)")
        
        # Check normalization (values should be between -1 and 1)
        max_val = max(abs(x) for x in embedding)
        if max_val <= 1.0:
            print("✅ Embedding appears to be normalized")
        else:
            print(f"⚠️  Embedding may not be normalized (max abs value: {max_val})")
        
        print("\n🎉 TEST SUCCESSFUL!")
        print("The embedder is working correctly and ready for production use.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
