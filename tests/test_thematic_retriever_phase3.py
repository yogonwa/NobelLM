"""
Tests for Phase 3B Enhanced ThematicRetriever with weighted retrieval.

This test suite covers the new weighted retrieval functionality including:
- Similarity-based ranked expansion integration
- Exponential weight scaling
- Weighted chunk merging
- Backward compatibility
- Performance monitoring
"""
import pytest
import math
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any, Tuple
import logging

from rag.thematic_retriever import ThematicRetriever
from config.theme_reformulator import ThemeReformulator


class TestThematicRetrieverPhase3:
    """Test suite for Phase 3B enhanced ThematicRetriever."""

    @pytest.fixture
    def mock_base_retriever(self):
        """Create a mock base retriever for testing."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = []
        return mock_retriever

    @pytest.fixture
    def mock_reformulator(self):
        """Create a mock ThemeReformulator for testing."""
        mock_reformulator = Mock(spec=ThemeReformulator)
        mock_reformulator.expand_query_terms_ranked.return_value = []
        mock_reformulator.expand_query_terms.return_value = set()
        return mock_reformulator

    @pytest.fixture
    def thematic_retriever(self, mock_base_retriever, mock_reformulator):
        """Create a ThematicRetriever instance with mocked dependencies."""
        with patch('rag.query_engine.get_mode_aware_retriever', return_value=mock_base_retriever):
            retriever = ThematicRetriever(model_id="bge-large", similarity_threshold=0.3)
            retriever.reformulator = mock_reformulator
            return retriever

    def test_init_with_similarity_threshold(self):
        """Test initialization with custom similarity threshold."""
        with patch('rag.query_engine.get_mode_aware_retriever'):
            retriever = ThematicRetriever(similarity_threshold=0.5)
            assert retriever.similarity_threshold == 0.5
            assert retriever.reformulator is not None

    def test_weighted_retrieval_with_ranked_terms(self, thematic_retriever, mock_base_retriever):
        """Test weighted retrieval using ranked expansion terms."""
        # Mock ranked expansion
        ranked_terms = [("justice", 0.95), ("fairness", 0.87), ("equality", 0.82)]
        thematic_retriever.reformulator.expand_query_terms_ranked.return_value = ranked_terms
        
        # Mock base retriever responses
        mock_chunks = [
            {"chunk_id": "1", "score": 0.8, "content": "justice content"},
            {"chunk_id": "2", "score": 0.7, "content": "fairness content"},
            {"chunk_id": "3", "score": 0.6, "content": "equality content"}
        ]
        mock_base_retriever.retrieve.return_value = mock_chunks
        
        # Test weighted retrieval
        result = thematic_retriever.retrieve(
            query="What do laureates say about justice?",
            use_weighted_retrieval=True
        )
        
        # Verify ranked expansion was called
        thematic_retriever.reformulator.expand_query_terms_ranked.assert_called_once_with(
            query="What do laureates say about justice?",
            similarity_threshold=0.3
        )
        
        # Verify base retriever was called for each ranked term
        assert mock_base_retriever.retrieve.call_count == 3
        
        # Verify chunks have weighted scores
        assert len(result) > 0
        for chunk in result:
            assert "source_term" in chunk
            assert "term_weight" in chunk
            assert "boost_factor" in chunk

    def test_weighted_retrieval_no_ranked_terms(self, thematic_retriever):
        """Test weighted retrieval when no ranked terms are found."""
        # Mock empty ranked expansion
        thematic_retriever.reformulator.expand_query_terms_ranked.return_value = []
        
        result = thematic_retriever.retrieve(
            query="What do laureates say about justice?",
            use_weighted_retrieval=True
        )
        
        assert result == []

    def test_legacy_retrieval_backward_compatibility(self, thematic_retriever, mock_base_retriever):
        """Test legacy retrieval for backward compatibility."""
        # Mock legacy expansion
        expanded_terms = ["justice", "fairness", "equality"]
        thematic_retriever.reformulator.expand_query_terms.return_value = set(expanded_terms)
        
        # Mock base retriever responses
        mock_chunks = [
            {"chunk_id": "1", "score": 0.8, "content": "justice content"},
            {"chunk_id": "2", "score": 0.7, "content": "fairness content"}
        ]
        mock_base_retriever.retrieve.return_value = mock_chunks
        
        # Test legacy retrieval
        result = thematic_retriever.retrieve(
            query="What do laureates say about justice?",
            use_weighted_retrieval=False
        )
        
        # Verify legacy expansion was called
        thematic_retriever.reformulator.expand_query_terms.assert_called_once_with(
            "What do laureates say about justice?"
        )
        
        # Verify base retriever was called for each term
        assert mock_base_retriever.retrieve.call_count == 3

    def test_apply_term_weights_exponential_scaling(self, thematic_retriever):
        """Test exponential weight scaling for chunk scores."""
        chunks = [
            {"chunk_id": "1", "score": 0.8, "content": "test content"},
            {"chunk_id": "2", "score": 0.6, "content": "test content 2"}
        ]
        term_weight = 0.9
        source_term = "justice"
        
        weighted_chunks = thematic_retriever._apply_term_weights(chunks, term_weight, source_term)
        
        # Verify exponential scaling
        expected_boost = math.exp(2 * term_weight)
        assert len(weighted_chunks) == 2
        
        for orig, chunk in zip(chunks, weighted_chunks):
            assert chunk["source_term"] == source_term
            assert chunk["term_weight"] == term_weight
            assert chunk["boost_factor"] == expected_boost
            assert chunk["score"] == orig["score"] * expected_boost

    def test_apply_term_weights_low_similarity(self, thematic_retriever):
        """Test weight scaling with low similarity scores."""
        chunks = [{"chunk_id": "1", "score": 0.8, "content": "test content"}]
        term_weight = 0.1  # Low similarity
        
        weighted_chunks = thematic_retriever._apply_term_weights(chunks, term_weight, "test")
        
        # Verify low boost factor for low similarity
        expected_boost = math.exp(2 * term_weight)
        assert weighted_chunks[0]["boost_factor"] == expected_boost
        assert expected_boost < 1.5  # Should be relatively low

    def test_merge_weighted_chunks_deduplication(self, thematic_retriever):
        """Test weighted chunk merging with deduplication."""
        chunks = [
            {"chunk_id": "1", "score": 0.8, "source_term": "justice", "term_weight": 0.9},
            {"chunk_id": "1", "score": 0.9, "source_term": "fairness", "term_weight": 0.8},  # Higher score
            {"chunk_id": "2", "score": 0.7, "source_term": "equality", "term_weight": 0.7}
        ]
        
        merged = thematic_retriever._merge_weighted_chunks(chunks)
        
        # Should deduplicate chunk_id "1" and keep the higher score
        assert len(merged) == 2
        chunk_ids = [chunk["chunk_id"] for chunk in merged]
        assert "1" in chunk_ids
        assert "2" in chunk_ids
        
        # Verify the chunk with higher score was kept
        chunk_1 = next(chunk for chunk in merged if chunk["chunk_id"] == "1")
        assert chunk_1["score"] == 0.9
        assert chunk_1["source_term"] == "fairness"

    def test_merge_weighted_chunks_sorting(self, thematic_retriever):
        """Test weighted chunk sorting by score and source type preference."""
        chunks = [
            {"chunk_id": "1", "score": 0.8, "source_type": "ceremony_speech"},
            {"chunk_id": "2", "score": 0.8, "source_type": "lecture"},  # Same score, prefer lecture
            {"chunk_id": "3", "score": 0.9, "source_type": "ceremony_speech"}  # Higher score
        ]
        
        merged = thematic_retriever._merge_weighted_chunks(chunks)
        
        # Should be sorted by score descending, then prefer lecture for equal scores
        assert len(merged) == 3
        assert merged[0]["chunk_id"] == "3"  # Highest score
        assert merged[1]["chunk_id"] == "2"  # Same score as 1, but lecture preferred
        assert merged[2]["chunk_id"] == "1"  # Same score as 1, but ceremony

    def test_expand_thematic_query_ranked_success(self, thematic_retriever):
        """Test successful ranked expansion."""
        ranked_terms = [("justice", 0.95), ("fairness", 0.87)]
        thematic_retriever.reformulator.expand_query_terms_ranked.return_value = ranked_terms
        
        result = thematic_retriever._expand_thematic_query_ranked("test query")
        
        assert result == ranked_terms
        thematic_retriever.reformulator.expand_query_terms_ranked.assert_called_once_with(
            query="test query",
            similarity_threshold=0.3
        )

    def test_expand_thematic_query_ranked_fallback(self, thematic_retriever):
        """Test ranked expansion fallback when no terms found."""
        thematic_retriever.reformulator.expand_query_terms_ranked.return_value = []
        
        result = thematic_retriever._expand_thematic_query_ranked("test query")
        
        assert result == [("test query", 1.0)]

    def test_expand_thematic_query_ranked_exception(self, thematic_retriever):
        """Test ranked expansion exception handling."""
        thematic_retriever.reformulator.expand_query_terms_ranked.side_effect = Exception("Test error")
        
        result = thematic_retriever._expand_thematic_query_ranked("test query")
        
        assert result == [("test query", 1.0)]

    def test_expand_thematic_query_legacy_success(self, thematic_retriever):
        """Test successful legacy expansion."""
        expanded_keywords = {"justice", "fairness", "equality"}
        thematic_retriever.reformulator.expand_query_terms.return_value = expanded_keywords
        
        result = thematic_retriever._expand_thematic_query_legacy("test query")
        
        assert set(result) == expanded_keywords

    def test_expand_thematic_query_legacy_short_terms_filtered(self, thematic_retriever):
        """Test that short terms are filtered out in legacy expansion."""
        expanded_keywords = {"justice", "fairness", "eq", "liberty"}  # "eq" is too short
        thematic_retriever.reformulator.expand_query_terms.return_value = expanded_keywords
        
        result = thematic_retriever._expand_thematic_query_legacy("test query")
        
        assert "eq" not in result
        assert "justice" in result
        assert "fairness" in result
        assert "liberty" in result

    def test_expand_thematic_query_legacy_fallback(self, thematic_retriever):
        """Test legacy expansion fallback when no terms found."""
        thematic_retriever.reformulator.expand_query_terms.return_value = set()
        
        result = thematic_retriever._expand_thematic_query_legacy("test query")
        
        assert result == ["test query"]

    def test_expand_thematic_query_legacy_exception(self, thematic_retriever):
        """Test legacy expansion exception handling."""
        thematic_retriever.reformulator.expand_query_terms.side_effect = Exception("Test error")
        
        result = thematic_retriever._expand_thematic_query_legacy("test query")
        
        assert result == ["test query"]

    def test_backward_compatibility_expand_thematic_query(self, thematic_retriever):
        """Test backward compatibility of _expand_thematic_query method."""
        expanded_keywords = {"justice", "fairness"}
        thematic_retriever.reformulator.expand_query_terms.return_value = expanded_keywords
        
        result = thematic_retriever._expand_thematic_query("test query")
        
        assert set(result) == expanded_keywords

    def test_merge_chunks_legacy_method(self, thematic_retriever):
        """Test legacy merge method for backward compatibility."""
        chunks = [
            {"chunk_id": "1", "score": 0.8, "source_type": "ceremony_speech"},
            {"chunk_id": "1", "score": 0.9, "source_type": "lecture"},  # Higher score
            {"chunk_id": "2", "score": 0.7, "source_type": "lecture"}
        ]
        
        merged = thematic_retriever._merge_chunks(chunks)
        
        # Should deduplicate and keep higher score
        assert len(merged) == 2
        chunk_1 = next(chunk for chunk in merged if chunk["chunk_id"] == "1")
        assert chunk_1["score"] == 0.9

    def test_weighted_retrieval_performance_logging(self, thematic_retriever, mock_base_retriever, caplog):
        """Test that weighted retrieval logs performance metrics."""
        ranked_terms = [("justice", 0.95), ("fairness", 0.87)]
        thematic_retriever.reformulator.expand_query_terms_ranked.return_value = ranked_terms
        
        mock_chunks = [{"chunk_id": "1", "score": 0.8, "content": "test"}]
        mock_base_retriever.retrieve.return_value = mock_chunks
        
        # Set logger level to INFO for this test
        logger = logging.getLogger("rag.thematic_retriever")
        logger.setLevel(logging.INFO)
        with caplog.at_level(logging.INFO, logger="rag.thematic_retriever"):
            thematic_retriever.retrieve("test query", use_weighted_retrieval=True)
        
        # Verify logging messages
        log_messages = [record.getMessage() for record in caplog.records if record.name == "rag.thematic_retriever"]
        assert any("Weighted retrieval for query" in msg for msg in log_messages)
        assert any("Found" in msg and "unique chunks after weighted merging" in msg for msg in log_messages)

    def test_weighted_retrieval_empty_chunks(self, thematic_retriever, mock_base_retriever):
        """Test weighted retrieval when base retriever returns empty results."""
        ranked_terms = [("justice", 0.95)]
        thematic_retriever.reformulator.expand_query_terms_ranked.return_value = ranked_terms
        mock_base_retriever.retrieve.return_value = []
        
        result = thematic_retriever.retrieve("test query", use_weighted_retrieval=True)
        
        assert result == []

    def test_weighted_retrieval_mixed_chunk_scores(self, thematic_retriever, mock_base_retriever):
        """Test weighted retrieval with chunks of varying scores."""
        ranked_terms = [("justice", 0.95), ("fairness", 0.5)]
        thematic_retriever.reformulator.expand_query_terms_ranked.return_value = ranked_terms
        
        # Mock different chunk scores for different terms
        def mock_retrieve(term, **kwargs):
            if term == "justice":
                return [{"chunk_id": "1", "score": 0.8, "content": "justice content"}]
            else:  # fairness
                return [{"chunk_id": "2", "score": 0.6, "content": "fairness content"}]
        
        mock_base_retriever.retrieve.side_effect = mock_retrieve
        
        result = thematic_retriever.retrieve("test query", use_weighted_retrieval=True)
        
        # Should have chunks from both terms with different weights
        assert len(result) == 2
        chunk_1 = next(chunk for chunk in result if chunk["chunk_id"] == "1")
        chunk_2 = next(chunk for chunk in result if chunk["chunk_id"] == "2")
        
        # Justice chunk should have higher weight
        assert chunk_1["term_weight"] == 0.95
        assert chunk_2["term_weight"] == 0.5
        assert chunk_1["boost_factor"] > chunk_2["boost_factor"] 