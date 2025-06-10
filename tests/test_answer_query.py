# tests/test_answer_query.py

import pytest
import logging
from rag.query_engine import answer_query
from rag.query_router import QueryIntent  # Add import for enum
from unittest.mock import patch, MagicMock

# -----------------------------------------------------------------------------------
# Test Thematic Query → answer_query
# -----------------------------------------------------------------------------------

def test_answer_query_thematic(caplog):
    mock_chunks = [
        {
            "text": "Justice is a recurring theme.",
            "laureate": "Toni Morrison",
            "year_awarded": 1993,
            "source_type": "nobel_lecture",
            "score": 0.95,
            "chunk_id": "1993_morrison_lecture_0",
            "text_snippet": "Justice is a recurring theme."
        }
    ]
    
    with caplog.at_level(logging.INFO):
        with patch("rag.query_engine.ThematicRetriever.retrieve", return_value=mock_chunks) as mock_retrieve, \
             patch("rag.query_engine.call_openai", return_value={"answer": "Justice is a key theme across laureates.", "completion_tokens": 20}):
            
            result = answer_query("What are common themes in Nobel lectures?")
            
            # Verify retriever was called
            assert mock_retrieve.called, "ThematicRetriever.retrieve was not called"
            
            # Verify result structure
            assert result["answer_type"] == "rag"
            assert "justice" in result["answer"].lower()
            assert result["sources"][0]["laureate"] == "Toni Morrison"
            assert "text_snippet" in result["sources"][0]
            assert result["sources"][0]["text_snippet"] == "Justice is a recurring theme."
            
            # Verify log content
            assert any("Starting query processing" in record.message for record in caplog.records)
            assert any("Retrieved chunks" in record.message for record in caplog.records)
            assert any("Query completed successfully" in record.message for record in caplog.records)

# -----------------------------------------------------------------------------------
# Test Factual Query → answer_query
# -----------------------------------------------------------------------------------

def test_answer_query_factual(caplog):
    with caplog.at_level(logging.INFO):
        with patch("rag.query_engine.QueryRouter.route_query") as mock_router:
            # Mock route result for factual query
            mock_router.return_value.answer_type = "metadata"
            mock_router.return_value.answer = "Toni Morrison won in 1993."
            mock_router.return_value.metadata_answer = {
                "answer": "Toni Morrison won in 1993.",
                "laureate": "Toni Morrison",
                "year_awarded": 1993
            }
            mock_router.return_value.intent = QueryIntent.FACTUAL  # Use enum instead of string
            mock_router.return_value.logs = {
                "metadata_handler": "matched",
                "metadata_rule": "award_year_by_name"
            }
            mock_router.return_value.retrieval_config = None
            mock_router.return_value.prompt_template = None

            result = answer_query("What year did Toni Morrison win?")
            
            # Verify result structure
            assert result["answer_type"] == "metadata"
            assert "1993" in result["answer"]
            assert result["metadata_answer"]["laureate"] == "Toni Morrison"
            assert result["metadata_answer"]["year_awarded"] == 1993
            assert result["sources"] == []  # No sources for metadata answers
            
            # Verify log content - metadata answers return early, so no "Query completed successfully"
            assert any("Starting query processing" in record.message for record in caplog.records)
            assert any("Using metadata answer" in record.message for record in caplog.records)
            # Note: "Query completed successfully" is only logged for RAG answers, not metadata answers

def test_answer_query_generative(caplog):
    """Test generative query path with standard retriever and correct configuration"""
    mock_chunks = [
        {
            "text": "Literature has the power to transform society.",
            "laureate": "Mario Vargas Llosa",
            "year_awarded": 2010,
            "source_type": "nobel_lecture",
            "score": 0.89,
            "chunk_id": "2010_llosa_lecture_0",
            "text_snippet": "Literature has the power to transform society."
        }
    ]
    
    with caplog.at_level(logging.INFO):
        with patch("rag.query_engine.QueryRouter.route_query") as mock_router:
            # Mock route result for generative query
            mock_router.return_value.answer_type = "rag"
            mock_router.return_value.answer = "Literature has the power to transform society and inspire change."
            mock_router.return_value.intent = QueryIntent.GENERATIVE
            mock_router.return_value.retrieval_config.top_k = 10
            mock_router.return_value.retrieval_config.score_threshold = 0.2
            mock_router.return_value.retrieval_config.filters = None
            mock_router.return_value.prompt_template = None
            
            with patch("rag.query_engine.get_mode_aware_retriever") as mock_get_retriever, \
                 patch("rag.query_engine.call_openai", return_value={"answer": "Literature has the power to transform society and inspire change.", "completion_tokens": 18}):
                
                mock_retriever = MagicMock()
                mock_retriever.retrieve.return_value = mock_chunks
                mock_get_retriever.return_value = mock_retriever
                
                result = answer_query("How does literature impact society?")
                
                # Verify result structure
                assert result["answer_type"] == "rag"
                assert "literature" in result["answer"].lower()
                assert result["sources"][0]["laureate"] == "Mario Vargas Llosa"
                
                # Verify retriever was called with correct parameters for generative query
                mock_retriever.retrieve.assert_called_once_with(
                    "How does literature impact society?",
                    top_k=10,
                    filters=None,
                    score_threshold=0.2,
                    min_return=3,
                    max_return=10
                )

def test_answer_query_thematic_with_filters(caplog):
    """Test thematic query path with filters properly propagated to ThematicRetriever"""
    mock_chunks = [
        {
            "text": "American literature perspective on justice.",
            "laureate": "Toni Morrison",
            "year_awarded": 1993,
            "source_type": "nobel_lecture",
            "score": 0.92,
            "chunk_id": "1993_morrison_lecture_0",
            "text_snippet": "American literature perspective on justice.",
            "country": "United States"
        }
    ]
    
    with caplog.at_level(logging.INFO):
        with patch("rag.query_engine.QueryRouter.route_query") as mock_router:
            # Mock route result for thematic query with filters
            mock_router.return_value.answer_type = "rag"
            mock_router.return_value.answer = "American literature has unique perspectives on justice."
            mock_router.return_value.intent = "thematic"
            mock_router.return_value.retrieval_config.top_k = 15
            mock_router.return_value.retrieval_config.score_threshold = 0.2
            mock_router.return_value.retrieval_config.filters = {"country": "United States"}
            mock_router.return_value.prompt_template = None
            
            with patch("rag.query_engine.ThematicRetriever") as mock_thematic_class, \
                 patch("rag.query_engine.call_openai", return_value={"answer": "American literature has unique perspectives on justice.", "completion_tokens": 15}):
                
                mock_thematic_retriever = MagicMock()
                mock_thematic_retriever.retrieve.return_value = mock_chunks
                mock_thematic_class.return_value = mock_thematic_retriever
                
                result = answer_query("What are common themes in American Nobel lectures?")
                
                # Verify result structure
                assert result["answer_type"] == "rag"
                assert "American" in result["answer"]
                assert result["sources"][0]["country"] == "United States"
                
                # Verify ThematicRetriever was called with correct filters
                mock_thematic_retriever.retrieve.assert_called_once_with(
                    "What are common themes in American Nobel lectures?",
                    top_k=15,
                    filters={"country": "United States"},
                    score_threshold=0.2,
                    min_return=5,
                    max_return=12
                )

def test_answer_query_score_threshold_propagation(caplog):
    """Test that score_threshold from QueryRouter is properly propagated to retriever"""
    mock_chunks = [
        {
            "text": "High quality content.",
            "laureate": "Test Author",
            "year_awarded": 2000,
            "source_type": "nobel_lecture",
            "score": 0.95,
            "chunk_id": "test_chunk_0",
            "text_snippet": "High quality content."
        }
    ]
    
    with caplog.at_level(logging.INFO):
        with patch("rag.query_engine.QueryRouter.route_query") as mock_router:
            # Mock route result with custom score_threshold
            mock_router.return_value.answer_type = "rag"
            mock_router.return_value.answer = "High quality answer."
            mock_router.return_value.intent = QueryIntent.FACTUAL
            mock_router.return_value.retrieval_config.top_k = 5
            mock_router.return_value.retrieval_config.score_threshold = 0.5  # Custom threshold
            mock_router.return_value.retrieval_config.filters = None
            mock_router.return_value.prompt_template = None
            
            with patch("rag.query_engine.get_mode_aware_retriever") as mock_get_retriever, \
                 patch("rag.query_engine.call_openai", return_value={"answer": "High quality answer.", "completion_tokens": 10}):
                
                mock_retriever = MagicMock()
                mock_retriever.retrieve.return_value = mock_chunks
                mock_get_retriever.return_value = mock_retriever
                
                result = answer_query("Test query", score_threshold=0.2)  # Function parameter
                
                # Verify retriever was called with router's score_threshold, not function parameter
                mock_retriever.retrieve.assert_called_once_with(
                    "Test query",
                    top_k=5,
                    filters=None,
                    score_threshold=0.5,  # Should use router's threshold, not 0.2
                    min_return=3,
                    max_return=10
                )
