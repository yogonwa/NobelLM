"""
Phase 3 Enhanced ThemeReformulator Tests

This module tests the enhanced ThemeReformulator with similarity-based ranked expansion
functionality implemented in Phase 3A.

Tests cover:
- Ranked expansion with similarity scoring
- Hybrid keyword extraction and preprocessing
- Backward compatibility with existing methods
- Fallback behavior and error handling
- Performance and logging

Author: NobelLM Team
"""
import pytest
import logging
from typing import List, Tuple
from config.theme_reformulator import ThemeReformulator

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEnhancedThemeReformulator:
    """Test the enhanced ThemeReformulator with ranked expansion functionality."""
    
    @pytest.fixture
    def reformulator(self):
        """Create a ThemeReformulator instance for testing."""
        return ThemeReformulator("config/themes.json", model_id="bge-large")
    
    def test_ranked_expansion_with_similarity(self, reformulator):
        """Test ranked expansion with similarity scoring."""
        query = "What do laureates say about justice and fairness?"
        
        ranked_expansions = reformulator.expand_query_terms_ranked(
            query, 
            similarity_threshold=0.3
        )
        
        # Check that we get ranked results
        assert isinstance(ranked_expansions, list)
        assert len(ranked_expansions) > 0
        
        # Check that results are tuples of (keyword, score)
        for keyword, score in ranked_expansions:
            assert isinstance(keyword, str)
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0
        
        # Check that results are sorted by score (descending)
        scores = [score for _, score in ranked_expansions]
        assert scores == sorted(scores, reverse=True)
        
        # Check that justice and fairness are likely in results
        keywords = [kw for kw, _ in ranked_expansions]
        assert any("justice" in kw.lower() or "fairness" in kw.lower() for kw in keywords)
    
    def test_low_similarity_pruning(self, reformulator):
        """Test that low similarity expansions are pruned."""
        query = "creativity and imagination in literature"
        
        # Test with high threshold
        high_threshold_expansions = reformulator.expand_query_terms_ranked(
            query, 
            similarity_threshold=0.7
        )
        
        # Test with low threshold
        low_threshold_expansions = reformulator.expand_query_terms_ranked(
            query, 
            similarity_threshold=0.1
        )
        
        # High threshold should have fewer results
        assert len(high_threshold_expansions) <= len(low_threshold_expansions)
        
        # All scores should be above their respective thresholds
        for _, score in high_threshold_expansions:
            assert score >= 0.7
        
        for _, score in low_threshold_expansions:
            assert score >= 0.1
    
    def test_mixed_theme_expansion_ranking(self, reformulator):
        """Test expansion ranking with mixed themes."""
        query = "peace and conflict resolution in science"
        
        ranked_expansions = reformulator.expand_query_terms_ranked(
            query, 
            similarity_threshold=0.3
        )
        
        assert len(ranked_expansions) > 0
        
        # Check that we get diverse themes
        keywords = [kw for kw, _ in ranked_expansions]
        
        # Should have peace-related keywords
        peace_keywords = [kw for kw in keywords if any(term in kw.lower() for term in ["peace", "conflict", "war"])]
        assert len(peace_keywords) > 0
        
        # Should have science-related keywords
        science_keywords = [kw for kw in keywords if any(term in kw.lower() for term in ["science", "research", "discovery"])]
        assert len(science_keywords) > 0
    
    def test_fallback_to_original_query(self, reformulator):
        """Test fallback behavior when similarity computation fails."""
        # Test with a query that has no clear theme keywords and very low similarity
        query = "xyz123 completely random query with no thematic content whatsoever"
        
        # This should fall back to original expansion method
        ranked_expansions = reformulator.expand_query_terms_ranked(
            query, 
            similarity_threshold=0.9  # Very high threshold to force fallback
        )
        
        # Should still return results (even if empty)
        assert isinstance(ranked_expansions, list)
        
        # If there are results, they should have score 1.0 (fallback)
        # If no results, that's also valid (empty list)
        if ranked_expansions:
            for _, score in ranked_expansions:
                assert score == 1.0
    
    def test_similarity_score_logging(self, reformulator, caplog):
        """Test that similarity scores are properly logged."""
        query = "justice and equality"
        
        with caplog.at_level(logging.INFO):
            reformulator.expand_query_terms_ranked(query, similarity_threshold=0.3)
        
        # Check that logging occurred
        assert any("Starting ranked expansion" in record.message for record in caplog.records)
        assert any("Ranked expansion completed" in record.message for record in caplog.records)
    
    def test_hybrid_keyword_extraction(self, reformulator):
        """Test hybrid keyword extraction logic."""
        # Test with theme keywords
        query_with_themes = "What do laureates say about justice?"
        theme_keywords = reformulator.extract_theme_keywords(query_with_themes)
        assert len(theme_keywords) > 0
        
        # Test with no theme keywords
        query_without_themes = "What is the weather like today?"
        theme_keywords = reformulator.extract_theme_keywords(query_without_themes)
        assert len(theme_keywords) == 0
    
    def test_stopword_removal(self, reformulator):
        """Test stopword removal in preprocessing."""
        query = "What do the laureates say about justice and fairness?"
        
        preprocessed = reformulator._preprocess_query_for_themes(query)
        
        # Should remove stopwords like "what", "do", "the", "and"
        assert "what" not in preprocessed.lower()
        assert "do" not in preprocessed.lower()
        assert "the" not in preprocessed.lower()
        assert "and" not in preprocessed.lower()
        
        # Should keep meaningful words
        assert "laureates" in preprocessed.lower()
        assert "justice" in preprocessed.lower()
        assert "fairness" in preprocessed.lower()
    
    def test_max_results_limiting(self, reformulator):
        """Test that max_results parameter works correctly."""
        query = "creativity and imagination"
        
        # Test with max_results limit
        limited_expansions = reformulator.expand_query_terms_ranked(
            query, 
            similarity_threshold=0.3,
            max_results=5
        )
        
        assert len(limited_expansions) <= 5
        
        # Test without limit
        unlimited_expansions = reformulator.expand_query_terms_ranked(
            query, 
            similarity_threshold=0.3
        )
        
        # Limited should have fewer or equal results
        assert len(limited_expansions) <= len(unlimited_expansions)
    
    def test_backward_compatibility(self, reformulator):
        """Test that existing methods still work correctly."""
        query = "justice and fairness"
        
        # Test original expansion method
        original_expansions = reformulator.expand_query_terms(query)
        assert isinstance(original_expansions, set)
        assert len(original_expansions) > 0
        
        # Test theme extraction
        themes = reformulator.extract_themes(query)
        assert isinstance(themes, set)
        assert len(themes) > 0
        
        # Test theme keyword extraction
        theme_keywords = reformulator.extract_theme_keywords(query)
        assert isinstance(theme_keywords, set)
        assert len(theme_keywords) > 0
    
    def test_expansion_stats(self, reformulator):
        """Test expansion statistics functionality."""
        query = "peace and conflict resolution"
        
        stats = reformulator.get_expansion_stats(query)
        
        # Check required fields
        assert "query" in stats
        assert "original_expansion_count" in stats
        assert "ranked_expansion_count" in stats
        assert "theme_keywords_found" in stats
        assert "theme_keywords" in stats
        assert "preprocessed_query" in stats
        assert "used_preprocessing" in stats
        assert "top_ranked_expansions" in stats
        
        # Check data types
        assert isinstance(stats["original_expansion_count"], int)
        assert isinstance(stats["ranked_expansion_count"], int)
        assert isinstance(stats["theme_keywords_found"], int)
        assert isinstance(stats["theme_keywords"], list)
        assert isinstance(stats["top_ranked_expansions"], list)
        
        # Check that counts are reasonable
        assert stats["original_expansion_count"] >= 0
        assert stats["ranked_expansion_count"] >= 0
        assert stats["theme_keywords_found"] >= 0
    
    def test_model_awareness(self, reformulator):
        """Test that the reformulator is model-aware."""
        assert reformulator.model_id == "bge-large"
        
        # Test with different model
        mini_reformulator = ThemeReformulator("config/themes.json", model_id="miniLM")
        assert mini_reformulator.model_id == "miniLM"
    
    def test_lazy_loading(self, reformulator):
        """Test that theme embeddings are loaded lazily."""
        # Initially, embeddings should not be loaded
        assert reformulator._theme_embeddings is None
        assert reformulator._embedding_model is None
        
        # Trigger loading by calling ranked expansion
        query = "justice and fairness"
        reformulator.expand_query_terms_ranked(query, similarity_threshold=0.3)
        
        # Now embeddings should be loaded (check via the getter method)
        theme_embeddings = reformulator._get_theme_embeddings()
        embedding_model = reformulator._get_embedding_model()
        
        assert theme_embeddings is not None
        assert embedding_model is not None


class TestThemeReformulatorPerformance:
    """Test performance characteristics of enhanced ThemeReformulator."""
    
    @pytest.fixture
    def reformulator(self):
        """Create a ThemeReformulator instance for performance testing."""
        return ThemeReformulator("config/themes.json", model_id="bge-large")
    
    def test_expansion_time_performance(self, reformulator):
        """Test that expansion completes within reasonable time."""
        import time
        
        query = "justice and fairness in society"
        
        # Time the expansion
        start_time = time.time()
        ranked_expansions = reformulator.expand_query_terms_ranked(
            query, 
            similarity_threshold=0.3
        )
        end_time = time.time()
        
        expansion_time = end_time - start_time
        
        # Should complete within 1 second (including model loading)
        assert expansion_time < 1.0
        
        # Should return results
        assert len(ranked_expansions) > 0
        
        logger.info(f"Expansion completed in {expansion_time:.3f}s with {len(ranked_expansions)} results")
    
    def test_multiple_expansions_performance(self, reformulator):
        """Test performance with multiple consecutive expansions."""
        import time
        
        queries = [
            "justice and fairness",
            "creativity and imagination", 
            "peace and conflict",
            "science and discovery"
        ]
        
        total_time = 0
        total_results = 0
        
        for query in queries:
            start_time = time.time()
            expansions = reformulator.expand_query_terms_ranked(query, similarity_threshold=0.3)
            end_time = time.time()
            
            total_time += (end_time - start_time)
            total_results += len(expansions)
        
        avg_time = total_time / len(queries)
        
        # Average expansion time should be reasonable
        assert avg_time < 0.5  # 500ms average
        
        logger.info(f"Average expansion time: {avg_time:.3f}s, total results: {total_results}")


def run_enhanced_theme_reformulator_tests():
    """Run all enhanced ThemeReformulator tests and report results."""
    logger.info("Running Enhanced ThemeReformulator Tests...")
    
    # Test basic functionality
    reformulator = ThemeReformulator("config/themes.json", model_id="bge-large")
    
    test_queries = [
        "What do laureates say about justice and fairness?",
        "How do winners discuss creativity and imagination?",
        "Peace and conflict resolution in modern times",
        "Science and discovery in the 21st century"
    ]
    
    for query in test_queries:
        logger.info(f"Testing query: '{query}'")
        
        # Test ranked expansion
        ranked_expansions = reformulator.expand_query_terms_ranked(query, similarity_threshold=0.3)
        logger.info(f"Ranked expansions: {len(ranked_expansions)} results")
        logger.info(f"Top 3: {ranked_expansions[:3]}")
        
        # Test expansion stats
        stats = reformulator.get_expansion_stats(query)
        logger.info(f"Expansion stats: {stats}")
    
    logger.info("Enhanced ThemeReformulator Tests completed!")


if __name__ == "__main__":
    run_enhanced_theme_reformulator_tests() 