"""
FAISS Index Sanity Check Tests

These tests verify that the NobelLM FAISS index can be loaded and searched correctly.
Use these to debug segmentation faults or index compatibility issues.
"""
import pytest
import logging
import faiss
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.validation
class TestFaissIndexSanity:
    """Test FAISS index loading and searching functionality."""
    
    @pytest.mark.validation
    def test_faiss_index_loading(self):
        """Test that the FAISS index can be loaded successfully."""
        index_path = Path("data/faiss_index_bge-large/index.faiss")
        
        if not index_path.exists():
            pytest.skip(f"FAISS index not found at {index_path}")
        
        logger.info(f"Loading FAISS index from {index_path} ...")
        index = faiss.read_index(str(index_path))
        
        # Verify index properties
        assert index.d > 0, "Index dimension should be positive"
        assert index.ntotal > 0, "Index should contain vectors"
        
        logger.info(f"Index loaded successfully. Dimension: {index.d}, Total vectors: {index.ntotal}")
    
    @pytest.mark.validation
    def test_faiss_index_search(self):
        """Test that the FAISS index can perform searches."""
        index_path = Path("data/faiss_index_bge-large/index.faiss")
        
        if not index_path.exists():
            pytest.skip(f"FAISS index not found at {index_path}")
        
        # Load index
        index = faiss.read_index(str(index_path))
        d = index.d
        
        # Create a random query vector
        vec = np.random.rand(1, d).astype('float32')
        faiss.normalize_L2(vec)
        
        logger.info(f"Running search with random vector of dimension {d}...")
        
        # Perform search
        D, I = index.search(vec, 3)
        
        # Verify search results
        assert D.shape == (1, 3), f"Expected distance shape (1, 3), got {D.shape}"
        assert I.shape == (1, 3), f"Expected index shape (1, 3), got {I.shape}"
        assert np.all(I >= 0), "All indices should be non-negative"
        assert np.all(I < index.ntotal), "All indices should be within index bounds"
        
        logger.info(f"Search completed successfully. Results: D={D}, I={I}")
    
    @pytest.mark.validation
    def test_faiss_index_dimension_consistency(self):
        """Test that the index dimension is consistent with expected values."""
        index_path = Path("data/faiss_index_bge-large/index.faiss")
        
        if not index_path.exists():
            pytest.skip(f"FAISS index not found at {index_path}")
        
        index = faiss.read_index(str(index_path))
        
        # Check that dimension is reasonable (should be 1024 for bge-large)
        expected_dim = 1024
        assert index.d == expected_dim, f"Expected dimension {expected_dim}, got {index.d}"
        
        logger.info(f"Index dimension is consistent: {index.d}")
    
    @pytest.mark.validation
    def test_faiss_index_vector_count(self):
        """Test that the index contains a reasonable number of vectors."""
        index_path = Path("data/faiss_index_bge-large/index.faiss")
        
        if not index_path.exists():
            pytest.skip(f"FAISS index not found at {index_path}")
        
        index = faiss.read_index(str(index_path))
        
        # Check that we have a reasonable number of vectors
        assert index.ntotal > 0, "Index should contain at least one vector"
        assert index.ntotal < 1000000, "Index should not contain an unreasonable number of vectors"
        
        logger.info(f"Index contains {index.ntotal} vectors") 