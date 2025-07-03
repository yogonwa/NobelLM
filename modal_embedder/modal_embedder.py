# modal_embedder.py

import modal
from sentence_transformers import SentenceTransformer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = modal.App("nobel-embedder")

# Define a preload function to download the model at build time
def download_model():
    try:
        logger.info("Downloading BAAI/bge-large-en-v1.5 model...")
        model = SentenceTransformer("BAAI/bge-large-en-v1.5")
        logger.info("Model downloaded successfully")
        return model
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        raise

# Define the image with model preloaded and all necessary dependencies
image = (
    modal.Image.debian_slim()
    .pip_install([
        "sentence-transformers",
        "torch",
        "transformers",
        "numpy",
        "scikit-learn"
    ])
    .run_function(download_model)
)

# Global variable to cache the model
model = None

@app.function(image=image)
def embed_query(text: str) -> list:
    global model
    
    try:
        # Load model once and cache it
        if model is None:
            logger.info("Loading model...")
            model = SentenceTransformer("BAAI/bge-large-en-v1.5")
            logger.info("Model loaded successfully")
        
        # Validate input
        if not text or not isinstance(text, str):
            raise ValueError("Input must be a non-empty string")
        
        # Generate embedding
        embedding = model.encode([text], normalize_embeddings=True)[0]
        return embedding.tolist()
        
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise

# Add a health check function
@app.function(image=image)
def health_check() -> dict:
    try:
        global model
        if model is None:
            model = SentenceTransformer("BAAI/bge-large-en-v1.5")
        
        # Test with a simple query
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
