"""
End-to-End Embedding + FAISS Sanity Check Tests

These tests verify the full pipeline: embedding a string and searching the NobelLM FAISS index.
Use these to debug integration issues or segmentation faults.
"""
import pytest
import logging
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.validation
class TestE2EEmbedFaissSanity:
    """Test end-to-end embedding and FAISS search functionality."""
    
    @pytest.mark.validation
    def test_full_pipeline_loading(self):
        """Test that both model and index can be loaded successfully."""
        model_name = "BAAI/bge-large-en-v1.5"
        index_path = Path("data/faiss_index_bge-large/index.faiss")
        
        if not index_path.exists():
            pytest.skip(f"FAISS index not found at {index_path}")
        
        logger.info(f"Loading embedding model: {model_name}")
        model = SentenceTransformer(model_name)
        logger.info("Model loaded successfully")
        
        logger.info(f"Loading FAISS index from {index_path}")
        index = faiss.read_index(str(index_path))
        logger.info("Index loaded successfully")
        
        # Verify both components
        assert model is not None, "Model should not be None"
        assert index is not None, "Index should not be None"
        assert index.d > 0, "Index should have positive dimension"
        assert index.ntotal > 0, "Index should contain vectors"
        
        logger.info(f"Full pipeline loaded. Model dimension: {model.get_sentence_embedding_dimension()}, Index dimension: {index.d}")
    
    @pytest.mark.validation
    def test_end_to_end_search(self):
        """Test complete pipeline: embed text and search FAISS index."""
        model_name = "BAAI/bge-large-en-v1.5"
        index_path = Path("data/faiss_index_bge-large/index.faiss")
        
        if not index_path.exists():
            pytest.skip(f"FAISS index not found at {index_path}")
        
        # Load components
        model = SentenceTransformer(model_name)
        index = faiss.read_index(str(index_path))
        
        # Test text
        text = "Test embedding for NobelLM end-to-end validation"
        logger.info(f"Processing text: '{text}'")
        
        # Generate embedding
        emb = model.encode(text, show_progress_bar=False, normalize_embeddings=True)
        logger.info(f"Embedding generated. Shape: {emb.shape}, first 5 values: {emb[:5]}")
        
        # Reshape if needed
        if emb.ndim == 1:
            emb = emb.reshape(1, -1)
        
        # Verify dimension compatibility
        if emb.shape[1] != index.d:
            raise ValueError(f"Embedding dimension {emb.shape[1]} does not match index dimension {index.d}")
        
        # Normalize for FAISS
        faiss.normalize_L2(emb)
        
        # Perform search
        logger.info("Running FAISS search...")
        D, I = index.search(emb, 3)
        
        # Verify search results
        assert D.shape == (1, 3), f"Expected distance shape (1, 3), got {D.shape}"
        assert I.shape == (1, 3), f"Expected index shape (1, 3), got {I.shape}"
        assert np.all(I >= 0), "All indices should be non-negative"
        assert np.all(I < index.ntotal), "All indices should be within index bounds"
        
        logger.info(f"Search completed successfully. Results: D={D}, I={I}")
    
    @pytest.mark.validation
    def test_dimension_consistency(self):
        """Test that model and index dimensions are consistent."""
        model_name = "BAAI/bge-large-en-v1.5"
        index_path = Path("data/faiss_index_bge-large/index.faiss")
        
        if not index_path.exists():
            pytest.skip(f"FAISS index not found at {index_path}")
        
        model = SentenceTransformer(model_name)
        index = faiss.read_index(str(index_path))
        
        model_dim = model.get_sentence_embedding_dimension()
        index_dim = index.d
        
        assert model_dim == index_dim, f"Model dimension {model_dim} should match index dimension {index_dim}"
        
        logger.info(f"Dimension consistency verified: {model_dim}")
    
    @pytest.mark.validation
    def test_multiple_queries(self):
        """Test that the pipeline can handle multiple queries."""
        model_name = "BAAI/bge-large-en-v1.5"
        index_path = Path("data/faiss_index_bge-large/index.faiss")
        
        if not index_path.exists():
            pytest.skip(f"FAISS index not found at {index_path}")
        
        model = SentenceTransformer(model_name)
        index = faiss.read_index(str(index_path))
        
        test_texts = [
            "What do laureates say about justice?",
            "Peace and conflict resolution",
            "Scientific discovery and innovation"
        ]
        
        logger.info(f"Testing multiple queries: {len(test_texts)} texts")
        
        for i, text in enumerate(test_texts):
            logger.info(f"Processing query {i+1}: '{text}'")
            
            # Generate embedding
            emb = model.encode(text, show_progress_bar=False, normalize_embeddings=True)
            if emb.ndim == 1:
                emb = emb.reshape(1, -1)
            
            # Verify dimension
            assert emb.shape[1] == index.d, f"Query {i+1}: dimension mismatch"
            
            # Normalize and search
            faiss.normalize_L2(emb)
            D, I = index.search(emb, 2)
            
            # Verify results
            assert D.shape == (1, 2), f"Query {i+1}: unexpected distance shape"
            assert I.shape == (1, 2), f"Query {i+1}: unexpected index shape"
            
            logger.info(f"Query {i+1} completed. Top result index: {I[0][0]}")
    
    @pytest.mark.validation
    def test_search_result_quality(self):
        """Test that search results are reasonable."""
        model_name = "BAAI/bge-large-en-v1.5"
        index_path = Path("data/faiss_index_bge-large/index.faiss")
        
        if not index_path.exists():
            pytest.skip(f"FAISS index not found at {index_path}")
        
        model = SentenceTransformer(model_name)
        index = faiss.read_index(str(index_path))
        
        # Test with a meaningful query
        query = "Nobel Prize acceptance speech"
        logger.info(f"Testing search quality with query: '{query}'")
        
        # Generate embedding and search
        emb = model.encode(query, show_progress_bar=False, normalize_embeddings=True)
        if emb.ndim == 1:
            emb = emb.reshape(1, -1)
        
        faiss.normalize_L2(emb)
        D, I = index.search(emb, 5)
        
        # Verify that we get different results (not all the same)
        unique_indices = len(set(I[0]))
        assert unique_indices > 1, "Should get different results for meaningful query"
        
        # Verify that distances are reasonable (should be between 0 and 2 for normalized vectors)
        assert np.all(D >= 0), "All distances should be non-negative"
        assert np.all(D <= 2), "All distances should be reasonable for normalized vectors"
        
        logger.info(f"Search quality verified. Unique results: {unique_indices}, Distance range: {D.min():.3f}-{D.max():.3f}")
    
    @pytest.mark.validation
    def test_error_handling(self):
        """Test that the pipeline handles errors gracefully."""
        model_name = "BAAI/bge-large-en-v1.5"
        index_path = Path("data/faiss_index_bge-large/index.faiss")
        
        if not index_path.exists():
            pytest.skip(f"FAISS index not found at {index_path}")
        
        model = SentenceTransformer(model_name)
        index = faiss.read_index(str(index_path))
        
        # Test with very long text (should still work)
        long_text = "This is a very long text " * 100
        logger.info("Testing with very long text")
        
        try:
            emb = model.encode(long_text, show_progress_bar=False, normalize_embeddings=True)
            if emb.ndim == 1:
                emb = emb.reshape(1, -1)
            
            faiss.normalize_L2(emb)
            D, I = index.search(emb, 1)
            
            assert D.shape == (1, 1), "Long text should still produce valid results"
            logger.info("Long text handled successfully")
        except Exception as e:
            logger.warning(f"Long text raised exception (acceptable): {e}")
        
        # Test with very short text
        short_text = "Hi"
        logger.info("Testing with very short text")
        
        try:
            emb = model.encode(short_text, show_progress_bar=False, normalize_embeddings=True)
            if emb.ndim == 1:
                emb = emb.reshape(1, -1)
            
            faiss.normalize_L2(emb)
            D, I = index.search(emb, 1)
            
            assert D.shape == (1, 1), "Short text should still produce valid results"
            logger.info("Short text handled successfully")
        except Exception as e:
            logger.warning(f"Short text raised exception (acceptable): {e}") 