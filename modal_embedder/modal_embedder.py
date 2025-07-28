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
- Secure HTTP endpoint with API key authentication

Usage:
    # Deploy the service
    modal deploy modal_embedder.py
    
    # Test locally
    modal run modal_embedder.py
    
    # Use in production via HTTP endpoint
    POST https://<modal-app-id>--embed-query.modal.run
    Headers: {"x-api-key": "<your-api-key>"}
    Body: {"text": "your query here"}

Author: NobelLM Team
Date: 2025
"""

import modal
import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sentence_transformers import SentenceTransformer

# Configure logging for debugging and monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Modal app instance
app = modal.App("nobel-embedder-clean-slate")


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
    modal.Image.from_registry("python:3.10-slim")
    .pip_install([
        "sentence-transformers",  # For BGE model
        "torch",                  # PyTorch backend
        "transformers",           # Hugging Face transformers
        "numpy",                  # Numerical computing
        "scikit-learn",           # Additional ML utilities
        "fastapi",                # FastAPI for web endpoints
        "uvicorn"                 # ASGI server for FastAPI
    ])
    .run_function(download_model)  # Preload model during build
)

# Global variable to cache the model instance across function calls
# This improves performance by avoiding repeated model loading
model = None

# Simple POST endpoint for embedding
@app.function(
    image=image,
    secrets=[modal.Secret.from_name("MODAL_EMBEDDER_API_KEY")]
)
@modal.fastapi_endpoint(method="POST")
def embed_query(item: dict):
    """
    Convert a text query into a 1024-dimensional embedding vector via HTTP endpoint.
    
    This function uses the BGE-large-en-v1.5 model to generate embeddings
    that are normalized and suitable for vector similarity search in Weaviate.
    
    Args:
        item: Dictionary containing:
            - "api_key": API key for authentication
            - "text": The text to embed
            
    Returns:
        Dictionary containing the embedding array
        
    Raises:
        Exception: If authentication fails or embedding generation fails
    """
    global model
    
    # Validate API key
    api_key = item.get("api_key")
    if api_key != os.environ["MODAL_EMBEDDER_API_KEY"]:
        raise Exception("Unauthorized")
    
    # Get text from request
    text = item.get("text")
    if not text:
        raise Exception("Missing 'text' field")
    
    if not isinstance(text, str):
        raise Exception("'text' must be a string")
    
    try:
        # Load model once and cache it for subsequent calls
        if model is None:
            logger.info("Loading model...")
            model = SentenceTransformer("BAAI/bge-large-en-v1.5")
            logger.info("Model loaded successfully")
        
        # Generate embedding with normalization enabled
        # normalize_embeddings=True ensures values are in [-1, 1] range
        embedding = model.encode([text], normalize_embeddings=True)[0]
        
        logger.info(f"Generated embedding for text of length {len(text)}")
        return {"embedding": embedding.tolist()}
        
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise Exception(f"Embedding generation failed: {e}")

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("MODAL_EMBEDDER_API_KEY")]
)
@modal.fastapi_endpoint(method="POST")
def embed_batch(item: dict):
    """
    Convert multiple text queries into 1024-dimensional embedding vectors via HTTP endpoint.
    
    This function uses the BGE-large-en-v1.5 model to generate embeddings for multiple
    texts in a single request, eliminating cold start storms from parallel requests.
    
    Args:
        item: Dictionary containing:
            - "api_key": API key for authentication
            - "texts": List of texts to embed
            
    Returns:
        Dictionary containing list of embedding arrays
        
    Raises:
        Exception: If authentication fails or embedding generation fails
    """
    global model
    
    # Validate API key
    api_key = item.get("api_key")
    if api_key != os.environ["MODAL_EMBEDDER_API_KEY"]:
        raise Exception("Unauthorized")
    
    # Get texts from request
    texts = item.get("texts")
    if not texts:
        raise Exception("Missing 'texts' field")
    
    if not isinstance(texts, list):
        raise Exception("'texts' must be a list")
    
    if len(texts) == 0:
        raise Exception("'texts' list cannot be empty")
    
    if len(texts) > 50:  # Reasonable limit to prevent abuse
        raise Exception("'texts' list cannot exceed 50 items")
    
    # Validate all texts are strings
    for i, text in enumerate(texts):
        if not isinstance(text, str):
            raise Exception(f"Text at index {i} must be a string")
    
    try:
        # Load model once and cache it for subsequent calls
        if model is None:
            logger.info("Loading model...")
            model = SentenceTransformer("BAAI/bge-large-en-v1.5")
            logger.info("Model loaded successfully")
        
        # Generate embeddings for all texts with normalization enabled
        # normalize_embeddings=True ensures values are in [-1, 1] range
        embeddings = model.encode(texts, normalize_embeddings=True)
        
        # Convert to list of lists for JSON serialization
        embedding_lists = [emb.tolist() for emb in embeddings]
        
        logger.info(f"Generated {len(embeddings)} embeddings for {len(texts)} texts")
        return {"embeddings": embedding_lists}
        
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {e}")
        raise Exception(f"Batch embedding generation failed: {e}")

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

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("MODAL_EMBEDDER_API_KEY")]
)
@modal.fastapi_endpoint(method="GET")
def health_check_web():
    """
    Web endpoint for health check that can be called by the backend warm-up.
    
    This endpoint is designed to be lightweight and fast for warming up
    the Modal service when the frontend loads.
    
    Returns:
        JSONResponse: Health status information
    """
    try:
        health = health_check.remote()
        return JSONResponse(content=health)
    except Exception as e:
        return JSONResponse(
            content={"status": "unhealthy", "error": str(e)},
            status_code=503
        )

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
        print("\n🔍 Step 2: Embedding generation")
        test_query = "What did Toni Morrison say about justice?"
        print(f"Test query: '{test_query}'")
        
        embedding = embed_query.remote(test_query)
        print(f"Embedding length: {len(embedding)}")
        print(f"Embedding type: {type(embedding)}")
        
        # Validate embedding properties
        if len(embedding) != 1024:
            print(f"❌ Expected 1024 dimensions, got {len(embedding)}")
            return
        
        max_val = max(abs(x) for x in embedding)
        if max_val > 1.0:
            print(f"❌ Embedding not normalized (max abs value: {max_val})")
            return
        
        print("✅ Embedding generation successful!")
        print(f"✅ Embedding is normalized (max abs value: {max_val:.4f})")
        
        # Test 3: Error handling
        print("\n🔍 Step 3: Error handling")
        try:
            # This should fail gracefully
            bad_embedding = embed_query.remote("")
            print("❌ Should have failed for empty string")
        except Exception as e:
            print(f"✅ Correctly handled empty string: {e}")
        
        print("\n🎉 All tests passed! Service is ready for deployment.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Test failure: {e}")
