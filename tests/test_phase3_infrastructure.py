"""
Phase 3 Infrastructure Tests

This module tests the new theme embedding infrastructure and similarity computation
implemented in Phase 3A. These tests validate the core functionality before proceeding
to the enhanced ThemeReformulator.

Tests cover:
- Theme embedding initialization and validation
- Similarity computation with various thresholds
- Model-aware functionality
- Error handling and edge cases
- Performance benchmarks

Author: NobelLM Team
"""
import pytest
import numpy as np
import logging
from typing import Dict, List
from config.theme_embeddings import ThemeEmbeddings
from config.theme_similarity import (
    compute_theme_similarities,
    get_ranked_theme_keywords,
    validate_similarity_threshold,
    get_similarity_stats
)
from rag.cache import get_model
from rag.model_config import get_model_config

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestThemeEmbeddings:
    """Test the ThemeEmbeddings class functionality."""
    
    def test_theme_embeddings_initialization(self):
        """Test that theme embeddings initialize correctly."""
        embeddings = ThemeEmbeddings("bge-large")
        
        # Check basic properties
        assert embeddings.model_id == "bge-large"
        assert embeddings.embedding_dim == 1024
        assert len(embeddings.themes) > 0
        
        # Check that embeddings were computed
        all_embeddings = embeddings.get_all_embeddings()
        assert len(all_embeddings) > 0
        
        # Check embedding dimensions
        for keyword, embedding in all_embeddings.items():
            assert embedding.shape[0] == 1024
            assert embedding.dtype == np.float32
    
    def test_theme_embeddings_minilm(self):
        """Test theme embeddings with miniLM model."""
        embeddings = ThemeEmbeddings("miniLM")
        
        assert embeddings.model_id == "miniLM"
        assert embeddings.embedding_dim == 384
        
        all_embeddings = embeddings.get_all_embeddings()
        assert len(all_embeddings) > 0
        
        for keyword, embedding in all_embeddings.items():
            assert embedding.shape[0] == 384
            assert embedding.dtype == np.float32
    
    def test_theme_embedding_retrieval(self):
        """Test retrieving specific theme embeddings."""
        embeddings = ThemeEmbeddings("bge-large")
        
        # Test valid keywords
        justice_emb = embeddings.get_theme_embedding("justice")
        assert justice_emb is not None
        assert justice_emb.shape[0] == 1024
        
        fairness_emb = embeddings.get_theme_embedding("fairness")
        assert fairness_emb is not None
        assert fairness_emb.shape[0] == 1024
        
        # Test invalid keyword
        invalid_emb = embeddings.get_theme_embedding("nonexistent_keyword")
        assert invalid_emb is None
    
    def test_theme_embedding_validation(self):
        """Test keyword validation functionality."""
        embeddings = ThemeEmbeddings("bge-large")
        
        # Test valid keywords
        assert embeddings.validate_keyword("justice") == True
        assert embeddings.validate_keyword("fairness") == True
        
        # Test invalid keywords
        assert embeddings.validate_keyword("nonexistent") == False
    
    def test_embedding_stats(self):
        """Test embedding statistics functionality."""
        embeddings = ThemeEmbeddings("bge-large")
        stats = embeddings.get_embedding_stats()
        
        assert "model_id" in stats
        assert "embedding_dim" in stats
        assert "total_keywords" in stats
        assert "total_themes" in stats
        assert "mean_norm" in stats
        assert "std_norm" in stats
        
        assert stats["model_id"] == "bge-large"
        assert stats["embedding_dim"] == 1024
        assert stats["total_keywords"] > 0
        assert stats["total_themes"] > 0
        
        # Check that norms are reasonable (should be ~1.0 for normalized embeddings)
        assert 0.9 <= stats["mean_norm"] <= 1.1
    
    def test_invalid_model_id(self):
        """Test that invalid model IDs are rejected."""
        with pytest.raises(ValueError, match="not supported"):
            ThemeEmbeddings("invalid_model")


class TestThemeSimilarity:
    """Test the theme similarity computation functionality."""
    
    def test_similarity_computation_basic(self):
        """Test basic similarity computation."""
        # Get a test query embedding
        model = get_model("bge-large")
        query = "What do laureates say about justice and fairness?"
        query_embedding = model.encode([query], normalize_embeddings=True)[0]
        
        # Compute similarities
        similarities = compute_theme_similarities(
            query_embedding=query_embedding,
            model_id="bge-large",
            similarity_threshold=0.3
        )
        
        # Check results
        assert isinstance(similarities, dict)
        assert len(similarities) > 0
        
        # Check that all scores are above threshold
        for keyword, score in similarities.items():
            assert score >= 0.3
            assert 0.0 <= score <= 1.0
        
        # Check that justice and fairness are likely in results
        keywords = list(similarities.keys())
        assert any("justice" in kw.lower() or "fairness" in kw.lower() for kw in keywords)
    
    def test_similarity_threshold_filtering(self):
        """Test that similarity threshold filtering works correctly."""
        model = get_model("bge-large")
        query = "creativity and imagination in literature"
        query_embedding = model.encode([query], normalize_embeddings=True)[0]
        
        # Test with high threshold
        high_threshold_similarities = compute_theme_similarities(
            query_embedding=query_embedding,
            model_id="bge-large",
            similarity_threshold=0.7
        )
        
        # Test with low threshold
        low_threshold_similarities = compute_theme_similarities(
            query_embedding=query_embedding,
            model_id="bge-large",
            similarity_threshold=0.1
        )
        
        # High threshold should have fewer results
        assert len(high_threshold_similarities) <= len(low_threshold_similarities)
        
        # All scores should be above their respective thresholds
        for score in high_threshold_similarities.values():
            assert score >= 0.7
        
        for score in low_threshold_similarities.values():
            assert score >= 0.1
    
    def test_ranked_theme_keywords(self):
        """Test ranked theme keyword functionality."""
        model = get_model("bge-large")
        query = "peace and conflict resolution"
        query_embedding = model.encode([query], normalize_embeddings=True)[0]
        
        ranked_keywords = get_ranked_theme_keywords(
            query_embedding=query_embedding,
            model_id="bge-large",
            similarity_threshold=0.3,
            max_results=5
        )
        
        assert isinstance(ranked_keywords, list)
        assert len(ranked_keywords) <= 5
        
        # Check that results are sorted by score (descending)
        scores = [score for _, score in ranked_keywords]
        assert scores == sorted(scores, reverse=True)
        
        # Check that all scores are above threshold
        for _, score in ranked_keywords:
            assert score >= 0.3
    
    def test_similarity_threshold_validation(self):
        """Test similarity threshold validation."""
        # Valid thresholds
        validate_similarity_threshold(0.0)
        validate_similarity_threshold(0.5)
        validate_similarity_threshold(1.0)
        
        # Invalid thresholds
        with pytest.raises(ValueError):
            validate_similarity_threshold(-0.1)
        
        with pytest.raises(ValueError):
            validate_similarity_threshold(1.1)
        
        with pytest.raises(ValueError):
            validate_similarity_threshold("invalid")
    
    def test_similarity_stats(self):
        """Test similarity statistics functionality."""
        # Test with data
        similarities = {"justice": 0.8, "fairness": 0.7, "equality": 0.6}
        stats = get_similarity_stats(similarities)
        
        assert stats["count"] == 3
        assert stats["mean"] == pytest.approx(0.7, rel=1e-10)
        assert stats["min"] == 0.6
        assert stats["max"] == 0.8
        
        # Test with empty data
        empty_stats = get_similarity_stats({})
        assert empty_stats["count"] == 0
        assert empty_stats["mean"] == 0.0
    
    def test_invalid_inputs(self):
        """Test error handling for invalid inputs."""
        # Invalid embedding dimension
        invalid_embedding = np.random.rand(512).astype(np.float32)  # Wrong dimension for bge-large
        
        with pytest.raises(ValueError, match="dimension mismatch"):
            compute_theme_similarities(
                query_embedding=invalid_embedding,
                model_id="bge-large"
            )
        
        # Invalid threshold
        valid_embedding = np.random.rand(1024).astype(np.float32)
        
        with pytest.raises(ValueError, match="Invalid similarity threshold"):
            compute_theme_similarities(
                query_embedding=valid_embedding,
                model_id="bge-large",
                similarity_threshold=1.5
            )
        
        # Invalid max_results
        with pytest.raises(ValueError, match="Invalid max_results"):
            compute_theme_similarities(
                query_embedding=valid_embedding,
                model_id="bge-large",
                max_results=0
            )


class TestPhase3Integration:
    """Test integration between theme embeddings and similarity computation."""
    
    def test_end_to_end_similarity_workflow(self):
        """Test complete workflow from query to ranked similarities."""
        # Initialize theme embeddings
        theme_embeddings = ThemeEmbeddings("bge-large")
        
        # Create test query
        model = get_model("bge-large")
        query = "How do Nobel laureates discuss freedom and liberty?"
        query_embedding = model.encode([query], normalize_embeddings=True)[0]
        
        # Compute similarities
        similarities = compute_theme_similarities(
            query_embedding=query_embedding,
            model_id="bge-large",
            similarity_threshold=0.3
        )
        
        # Validate results
        assert len(similarities) > 0
        
        # Check that freedom-related keywords are in results
        freedom_keywords = [kw for kw in similarities.keys() if "freedom" in kw.lower() or "liberty" in kw.lower()]
        assert len(freedom_keywords) > 0
        
        # Verify that all keywords have valid embeddings
        for keyword in similarities.keys():
            assert theme_embeddings.validate_keyword(keyword)
    
    def test_model_switching(self):
        """Test that similarity computation works with different models."""
        # Test with bge-large
        model_large = get_model("bge-large")
        query = "science and discovery"
        query_embedding_large = model_large.encode([query], normalize_embeddings=True)[0]
        
        similarities_large = compute_theme_similarities(
            query_embedding=query_embedding_large,
            model_id="bge-large",
            similarity_threshold=0.3
        )
        
        # Test with miniLM
        model_mini = get_model("miniLM")
        query_embedding_mini = model_mini.encode([query], normalize_embeddings=True)[0]
        
        similarities_mini = compute_theme_similarities(
            query_embedding=query_embedding_mini,
            model_id="miniLM",
            similarity_threshold=0.3
        )
        
        # Both should return results
        assert len(similarities_large) > 0
        assert len(similarities_mini) > 0
        
        # Results should be different due to different models
        # (but both should contain science-related keywords)
        science_keywords_large = [kw for kw in similarities_large.keys() if "science" in kw.lower()]
        science_keywords_mini = [kw for kw in similarities_mini.keys() if "science" in kw.lower()]
        
        assert len(science_keywords_large) > 0
        assert len(science_keywords_mini) > 0


def run_phase3_infrastructure_tests():
    """Run all Phase 3 infrastructure tests and report results."""
    logger.info("Running Phase 3 Infrastructure Tests...")
    
    # Test theme embeddings
    logger.info("Testing ThemeEmbeddings...")
    theme_embeddings = ThemeEmbeddings("bge-large")
    stats = theme_embeddings.get_embedding_stats()
    logger.info(f"Theme embedding stats: {stats}")
    
    # Test similarity computation
    logger.info("Testing similarity computation...")
    model = get_model("bge-large")
    test_queries = [
        "justice and fairness",
        "creativity and imagination", 
        "peace and conflict",
        "science and discovery"
    ]
    
    for query in test_queries:
        query_embedding = model.encode([query], normalize_embeddings=True)[0]
        similarities = compute_theme_similarities(
            query_embedding=query_embedding,
            model_id="bge-large",
            similarity_threshold=0.3
        )
        logger.info(f"Query: '{query}' -> {len(similarities)} similar keywords")
        logger.info(f"Top 3: {list(similarities.items())[:3]}")
    
    logger.info("Phase 3 Infrastructure Tests completed successfully!")


if __name__ == "__main__":
    run_phase3_infrastructure_tests() 