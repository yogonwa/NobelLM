"""
Embedding Model Sanity Check Tests

These tests verify that the NobelLM embedding model can be loaded and used correctly.
Use these to debug segmentation faults or model compatibility issues.
"""
import pytest
import logging
from sentence_transformers import SentenceTransformer
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.validation
class TestEmbedderSanity:
    """Test embedding model loading and functionality."""
    
    @pytest.mark.validation
    def test_model_loading(self):
        """Test that the embedding model can be loaded successfully."""
        model_name = "BAAI/bge-large-en-v1.5"
        
        logger.info(f"Loading model: {model_name}")
        model = SentenceTransformer(model_name)
        
        # Verify model properties
        assert model is not None, "Model should not be None"
        assert hasattr(model, 'encode'), "Model should have encode method"
        assert hasattr(model, 'get_sentence_embedding_dimension'), "Model should have dimension method"
        
        logger.info("Model loaded successfully")
    
    @pytest.mark.validation
    def test_embedding_generation(self):
        """Test that the model can generate embeddings."""
        model_name = "BAAI/bge-large-en-v1.5"
        model = SentenceTransformer(model_name)
        
        test_text = "Test embedding for NobelLM validation"
        logger.info(f"Generating embedding for: '{test_text}'")
        
        # Generate embedding
        emb = model.encode(test_text, show_progress_bar=False, normalize_embeddings=True)
        
        # Verify embedding properties
        assert emb is not None, "Embedding should not be None"
        assert isinstance(emb, np.ndarray), "Embedding should be a numpy array"
        assert emb.ndim == 1, "Embedding should be 1-dimensional"
        assert emb.shape[0] > 0, "Embedding should have positive dimension"
        
        logger.info(f"Embedding generated successfully. Shape: {emb.shape}, first 5 values: {emb[:5]}")
    
    @pytest.mark.validation
    def test_embedding_dimension(self):
        """Test that the embedding dimension is consistent."""
        model_name = "BAAI/bge-large-en-v1.5"
        model = SentenceTransformer(model_name)
        
        expected_dim = 1024  # bge-large dimension
        actual_dim = model.get_sentence_embedding_dimension()
        
        assert actual_dim == expected_dim, f"Expected dimension {expected_dim}, got {actual_dim}"
        
        # Test with actual embedding
        test_text = "Test dimension consistency"
        emb = model.encode(test_text, show_progress_bar=False, normalize_embeddings=True)
        
        assert emb.shape[0] == expected_dim, f"Embedding dimension should be {expected_dim}"
        
        logger.info(f"Embedding dimension is consistent: {actual_dim}")
    
    @pytest.mark.validation
    def test_embedding_normalization(self):
        """Test that embeddings are properly normalized."""
        model_name = "BAAI/bge-large-en-v1.5"
        model = SentenceTransformer(model_name)
        
        test_text = "Test normalization"
        emb = model.encode(test_text, show_progress_bar=False, normalize_embeddings=True)
        
        # Check that embedding is normalized (L2 norm should be close to 1)
        norm = np.linalg.norm(emb)
        assert abs(norm - 1.0) < 1e-6, f"Embedding should be normalized, got norm {norm}"
        
        logger.info(f"Embedding is properly normalized with L2 norm: {norm}")
    
    @pytest.mark.validation
    def test_multiple_texts_embedding(self):
        """Test that the model can handle multiple texts."""
        model_name = "BAAI/bge-large-en-v1.5"
        model = SentenceTransformer(model_name)
        
        test_texts = [
            "First test text",
            "Second test text",
            "Third test text"
        ]
        
        logger.info(f"Generating embeddings for {len(test_texts)} texts")
        
        # Generate embeddings for multiple texts
        embs = model.encode(test_texts, show_progress_bar=False, normalize_embeddings=True)
        
        # Verify results
        assert embs is not None, "Embeddings should not be None"
        assert isinstance(embs, np.ndarray), "Embeddings should be a numpy array"
        assert embs.ndim == 2, "Multiple embeddings should be 2-dimensional"
        assert embs.shape[0] == len(test_texts), "Number of embeddings should match number of texts"
        
        logger.info(f"Multiple embeddings generated successfully. Shape: {embs.shape}")
    
    @pytest.mark.validation
    def test_empty_text_handling(self):
        """Test that the model handles empty text gracefully."""
        model_name = "BAAI/bge-large-en-v1.5"
        model = SentenceTransformer(model_name)
        
        # Test with empty string
        empty_text = ""
        logger.info("Testing empty text handling")
        
        try:
            emb = model.encode(empty_text, show_progress_bar=False, normalize_embeddings=True)
            # If it doesn't raise an exception, verify the embedding
            assert emb is not None, "Empty text should still produce an embedding"
            assert emb.shape[0] > 0, "Empty text embedding should have positive dimension"
            logger.info("Empty text handled successfully")
        except Exception as e:
            # It's acceptable for the model to raise an exception for empty text
            logger.info(f"Empty text raised expected exception: {e}")
    
    @pytest.mark.validation
    def test_model_consistency(self):
        """Test that the model produces consistent embeddings for the same text."""
        model_name = "BAAI/bge-large-en-v1.5"
        model = SentenceTransformer(model_name)
        
        test_text = "Consistency test text"
        logger.info("Testing embedding consistency")
        
        # Generate embeddings multiple times
        emb1 = model.encode(test_text, show_progress_bar=False, normalize_embeddings=True)
        emb2 = model.encode(test_text, show_progress_bar=False, normalize_embeddings=True)
        
        # Embeddings should be identical (deterministic)
        assert np.allclose(emb1, emb2), "Embeddings should be identical for same text"
        
        logger.info("Embedding consistency verified") 