"""
Integration test: Prompt → Compiler

Tests the integration between prompt generation and answer compilation,
ensuring proper data flow and error handling through the answer_query pipeline.
"""

import pytest
from unittest.mock import patch, MagicMock
from rag.query_engine import build_prompt, answer_query

# -----------------------------------------------------------------------------------
# Test Fixtures
# -----------------------------------------------------------------------------------

@pytest.fixture
def mock_chunks():
    """Mock chunks for testing."""
    return [
        {
            "text": "Justice is a recurring theme in literature.",
            "score": 0.85,
            "chunk_id": "c1",
            "laureate": "Toni Morrison",
            "year_awarded": 1993,
            "source_type": "nobel_lecture"
        },
        {
            "text": "The human condition is explored through narrative.",
            "score": 0.78,
            "chunk_id": "c2",
            "laureate": "Gabriel García Márquez",
            "year_awarded": 1982,
            "source_type": "nobel_lecture"
        }
    ]

# -----------------------------------------------------------------------------------
# Test: Prompt → Compiler Integration
# -----------------------------------------------------------------------------------

@pytest.mark.integration
def test_prompt_to_compiler_integration(mock_chunks):
    """Test complete integration from prompt building to answer compilation."""
    query = "What are common themes in Nobel laureate speeches?"
    
    with patch('rag.query_engine.get_query_router') as mock_get_router, \
         patch('rag.query_engine.get_mode_aware_retriever') as mock_get_retriever, \
         patch('rag.query_engine.call_openai') as mock_llm:
        
        # Setup mocks
        mock_router = MagicMock()
        mock_route_result = MagicMock()
        mock_route_result.answer_type = "rag"
        mock_route_result.intent = "thematic"
        mock_route_result.retrieval_config.top_k = 15
        mock_route_result.retrieval_config.score_threshold = 0.2
        mock_route_result.retrieval_config.filters = None
        mock_route_result.prompt_template = None
        mock_router.route_query.return_value = mock_route_result
        mock_get_router.return_value = mock_router
        
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = mock_chunks
        mock_get_retriever.return_value = mock_retriever
        
        mock_llm.return_value = {
            "answer": "Common themes include justice, human dignity, and the power of storytelling.",
            "completion_tokens": 20
        }
        
        # Test the complete pipeline
        result = answer_query(query, model_id="bge-large")
        
        # Verify result structure
        assert result["answer_type"] == "rag"
        assert "justice" in result["answer"].lower()
        assert "storytelling" in result["answer"].lower()
        assert len(result["sources"]) == 2
        assert result["sources"][0]["laureate"] == "Toni Morrison"
        assert result["sources"][1]["laureate"] == "Gabriel García Márquez"
        
        # Verify prompt was built with chunks
        mock_llm.assert_called_once()
        call_args = mock_llm.call_args
        prompt = call_args[0][0]  # First argument is the prompt
        assert query in prompt
        assert "Justice is a recurring theme" in prompt
        assert "human condition is explored" in prompt

@pytest.mark.integration
def test_prompt_to_compiler_empty_chunks():
    """Test prompt to compiler integration with empty chunks."""
    query = "What did Toni Morrison say about justice?"
    
    with patch('rag.query_engine.get_query_router') as mock_get_router, \
         patch('rag.query_engine.get_mode_aware_retriever') as mock_get_retriever, \
         patch('rag.query_engine.call_openai') as mock_llm:
        
        # Setup mocks
        mock_router = MagicMock()
        mock_route_result = MagicMock()
        mock_route_result.answer_type = "rag"
        mock_route_result.intent = "factual"
        mock_route_result.retrieval_config.top_k = 5
        mock_route_result.retrieval_config.score_threshold = 0.25
        mock_route_result.retrieval_config.filters = None
        mock_route_result.prompt_template = None
        mock_router.route_query.return_value = mock_route_result
        mock_get_router.return_value = mock_router
        
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []
        mock_get_retriever.return_value = mock_retriever
        
        mock_llm.return_value = {
            "answer": "I couldn't find specific information about that.",
            "completion_tokens": 8
        }
        
        # Test the complete pipeline
        result = answer_query(query, model_id="bge-large")
        
        # Verify result structure
        assert result["answer_type"] == "rag"
        assert "couldn't find" in result["answer"].lower()
        assert len(result["sources"]) == 0
        
        # Verify prompt was built with empty context
        mock_llm.assert_called_once()
        call_args = mock_llm.call_args
        prompt = call_args[0][0]  # First argument is the prompt
        assert query in prompt
        # Should indicate no relevant information

@pytest.mark.integration
def test_prompt_to_compiler_error_handling():
    """Test error handling in prompt to compiler integration."""
    query = "What did Toni Morrison say about justice?"
    
    with patch('rag.query_engine.get_query_router') as mock_get_router, \
         patch('rag.query_engine.get_mode_aware_retriever') as mock_get_retriever:
        
        # Setup mocks
        mock_router = MagicMock()
        mock_route_result = MagicMock()
        mock_route_result.answer_type = "rag"
        mock_route_result.intent = "factual"
        mock_route_result.retrieval_config.top_k = 5
        mock_route_result.retrieval_config.score_threshold = 0.25
        mock_route_result.retrieval_config.filters = None
        mock_route_result.prompt_template = None
        mock_router.route_query.return_value = mock_route_result
        mock_get_router.return_value = mock_router
        
        mock_retriever = MagicMock()
        mock_retriever.retrieve.side_effect = Exception("Retriever failed")
        mock_get_retriever.return_value = mock_retriever
        
        # Test error handling
        with pytest.raises(Exception, match="Retriever failed"):
            answer_query(query, model_id="bge-large")

@pytest.mark.integration
def test_prompt_to_compiler_metadata_answer():
    """Test prompt to compiler integration with metadata answers."""
    query = "Who won the Nobel Prize in Literature in 1993?"
    
    with patch('rag.query_engine.get_query_router') as mock_get_router, \
         patch('rag.query_engine.call_openai') as mock_llm:
        
        # Setup mocks for metadata answer
        mock_router = MagicMock()
        mock_route_result = MagicMock()
        mock_route_result.answer_type = "metadata"
        mock_route_result.intent = "metadata"
        mock_route_result.answer = "Toni Morrison won the Nobel Prize in Literature in 1993."
        mock_route_result.metadata_answer = "Toni Morrison won the Nobel Prize in Literature in 1993."
        mock_router.route_query.return_value = mock_route_result
        mock_get_router.return_value = mock_router
        
        # Test the complete pipeline
        result = answer_query(query, model_id="bge-large")
        
        # Verify metadata result structure
        assert result["answer_type"] == "metadata"
        assert "Toni Morrison" in result["answer"]
        assert result["metadata_answer"] == "Toni Morrison won the Nobel Prize in Literature in 1993."
        assert result["sources"] == []
        
        # Verify no LLM was called for metadata answers
        mock_llm.assert_not_called()

@pytest.mark.integration
def test_prompt_to_compiler_thematic_retriever():
    """Test prompt to compiler integration with thematic retriever."""
    query = "What are common themes in Nobel laureate speeches?"
    
    with patch('rag.query_engine.get_query_router') as mock_get_router, \
         patch('rag.query_engine.ThematicRetriever') as mock_thematic_class, \
         patch('rag.query_engine.call_openai') as mock_llm:
        
        # Setup mocks
        mock_router = MagicMock()
        mock_route_result = MagicMock()
        mock_route_result.answer_type = "rag"
        mock_route_result.intent = "thematic"
        mock_route_result.retrieval_config.top_k = 15
        mock_route_result.retrieval_config.score_threshold = 0.2
        mock_route_result.retrieval_config.filters = None
        mock_route_result.prompt_template = None
        mock_router.route_query.return_value = mock_route_result
        mock_get_router.return_value = mock_router
        
        mock_thematic_retriever = MagicMock()
        mock_thematic_retriever.retrieve.return_value = [
            {
                "text": "Justice and human dignity are common themes.",
                "score": 0.82,
                "chunk_id": "c1",
                "laureate": "Toni Morrison",
                "year_awarded": 1993,
                "source_type": "nobel_lecture"
            }
        ]
        mock_thematic_class.return_value = mock_thematic_retriever
        
        mock_llm.return_value = {
            "answer": "Common themes include justice and human dignity.",
            "completion_tokens": 15
        }
        
        # Test the complete pipeline
        result = answer_query(query, model_id="bge-large")
        
        # Verify thematic retriever was used
        mock_thematic_class.assert_called_once_with(model_id="bge-large")
        mock_thematic_retriever.retrieve.assert_called_once_with(
            query,
            top_k=15,
            filters=None,
            score_threshold=0.2,
            min_return=5,
            max_return=12
        )
        
        # Verify result structure
        assert result["answer_type"] == "rag"
        assert "justice" in result["answer"].lower()
        assert len(result["sources"]) == 1
