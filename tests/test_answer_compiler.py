import pytest
from unittest.mock import patch, MagicMock

# --- Test for factual/metadata answer ---
def test_answer_compiler_metadata():
    from rag import query_engine
    from rag.query_router import QueryIntent, RetrievalConfig
    # Patch QueryRouter to always return a metadata answer
    class DummyRouteResult:
        intent = QueryIntent.FACTUAL
        answer_type = "metadata"
        answer = "Toni Morrison won in 1993."
        metadata_answer = {"answer": "Toni Morrison won in 1993.", "laureate": "Toni Morrison", "year_awarded": 1993}
        retrieval_config = RetrievalConfig(top_k=0)
        prompt_template = ""
        logs = {"metadata_handler": "matched", "metadata_rule": "award_year_by_name"}
    with patch("rag.query_engine.get_query_router") as mock_router:
        mock_router.return_value.route_query.return_value = DummyRouteResult()
        # Test with explicit model_id
        result = query_engine.answer_query("When did Toni Morrison win?", model_id="test-model")
        assert result["answer_type"] == "metadata"
        assert "Toni Morrison" in result["answer"]
        assert result["metadata_answer"]["year_awarded"] == 1993
        assert result["sources"] == []

# --- Test for thematic (RAG) answer ---
def test_answer_compiler_thematic():
    from rag import query_engine
    from rag.query_router import QueryIntent, RetrievalConfig
    # Patch QueryRouter to return a RAG/thematic answer
    class DummyRouteResult:
        intent = QueryIntent.THEMATIC
        answer_type = "rag"
        answer = None
        metadata_answer = None
        retrieval_config = RetrievalConfig(top_k=3, filters=None, score_threshold=None)
        prompt_template = "Analyze the following thematic question about Nobel Literature laureates: {query}\n\nContext: {context}"
        logs = {"thematic_expanded_terms": "theme, motif, pattern"}
    dummy_chunks = [
        {"text": "Theme chunk 1.", "laureate": "A", "year_awarded": 2000, "source_type": "lecture", "score": 0.9, "chunk_id": 1},
        {"text": "Theme chunk 2.", "laureate": "B", "year_awarded": 2001, "source_type": "speech", "score": 0.8, "chunk_id": 2}
    ]
    # Create a mock ThematicRetriever that returns our dummy chunks
    mock_thematic_retriever = MagicMock()
    mock_thematic_retriever.retrieve.return_value = dummy_chunks

    with patch("rag.query_engine.get_query_router") as mock_router, \
         patch("rag.query_engine.ThematicRetriever", return_value=mock_thematic_retriever) as mock_thematic_class, \
         patch("rag.query_engine.call_openai", return_value={"answer": "Synthesized answer."}):
        mock_router.return_value.route_query.return_value = DummyRouteResult()
        
        # Test with explicit model_id
        result = query_engine.answer_query("What are common themes?", model_id="test-model")
        
        # Verify ThematicRetriever was created with correct model_id
        mock_thematic_class.assert_called_once_with(model_id="test-model")
        
        # Verify downstream logic works as expected
        assert result["answer_type"] == "rag"
        assert "Synthesized answer" in result["answer"]
        assert isinstance(result["sources"], list)
        assert len(result["sources"]) == 2
        assert "Theme chunk 1" in result["sources"][0]["text"]

# --- Test for hybrid query (should route as RAG or metadata depending on router logic) ---
def test_answer_compiler_hybrid():
    from rag import query_engine
    from rag.query_router import QueryIntent, RetrievalConfig
    # Patch QueryRouter to return a RAG answer for a hybrid query
    class DummyRouteResult:
        intent = QueryIntent.FACTUAL  # Changed from hybrid to factual since hybrid isn't special
        answer_type = "rag"
        answer = None
        metadata_answer = None
        retrieval_config = RetrievalConfig(top_k=3, filters=None, score_threshold=None)
        prompt_template = "Answer the following factual question about Nobel Literature laureates: {query}\n\nContext: {context}"
        logs = {}
    dummy_chunks = [
        {"text": "Hybrid chunk.", "laureate": "C", "year_awarded": 2010, "source_type": "lecture", "score": 0.7, "chunk_id": 3}
    ]
    # Create a mock retriever that returns our dummy chunks
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = dummy_chunks

    with patch("rag.query_engine.get_query_router") as mock_router, \
         patch("rag.query_engine.get_mode_aware_retriever", return_value=mock_retriever) as mock_get_retriever, \
         patch("rag.query_engine.call_openai", return_value={"answer": "Hybrid answer."}):
        mock_router.return_value.route_query.return_value = DummyRouteResult()
        
        # Test with explicit model_id
        result = query_engine.answer_query("Write a summary of what Morrison said about justice.", model_id="test-model")
        
        # Verify retriever factory was called with correct model_id
        mock_get_retriever.assert_called_once_with("test-model")
        
        # Verify downstream logic works as expected
        assert result["answer_type"] == "rag"
        assert "Hybrid answer" in result["answer"]
        assert isinstance(result["sources"], list)
        assert len(result["sources"]) == 1
        assert "Hybrid chunk" in result["sources"][0]["text"]

# --- Test for no relevant chunks (fallback) ---
def test_answer_compiler_no_chunks():
    from rag import query_engine
    from rag.query_router import QueryIntent, RetrievalConfig
    class DummyRouteResult:
        intent = QueryIntent.THEMATIC
        answer_type = "rag"
        answer = None
        metadata_answer = None
        retrieval_config = RetrievalConfig(top_k=3, filters=None, score_threshold=None)
        prompt_template = "Analyze the following thematic question about Nobel Literature laureates: {query}\n\nContext: {context}"
        logs = {"thematic_expanded_terms": "theme, motif, pattern"}
    # Create a mock ThematicRetriever that returns empty chunks
    mock_thematic_retriever = MagicMock()
    mock_thematic_retriever.retrieve.return_value = []

    with patch("rag.query_engine.get_query_router") as mock_router, \
         patch("rag.query_engine.ThematicRetriever", return_value=mock_thematic_retriever) as mock_thematic_class, \
         patch("rag.query_engine.call_openai", return_value={"answer": "No relevant information found in the corpus"}):
        mock_router.return_value.route_query.return_value = DummyRouteResult()
        
        # Test with explicit model_id
        result = query_engine.answer_query("What are common themes?", model_id="test-model")
        
        # Verify ThematicRetriever was created with correct model_id
        mock_thematic_class.assert_called_once_with(model_id="test-model")
        
        # Verify fallback behavior
        assert result["answer_type"] == "rag"
        assert "No relevant information found in the corpus" in result["answer"]
        assert result["sources"] == []

# --- Test for default model_id behavior ---
def test_answer_compiler_default_model_id():
    from rag import query_engine
    from rag.model_config import DEFAULT_MODEL_ID
    from rag.query_router import QueryIntent, RetrievalConfig
    
    class DummyRouteResult:
        intent = QueryIntent.FACTUAL
        answer_type = "rag"
        answer = None
        metadata_answer = None
        retrieval_config = RetrievalConfig(top_k=3, filters=None, score_threshold=None)
        prompt_template = "Answer the following factual question about Nobel Literature laureates: {query}\n\nContext: {context}"
        logs = {}
    dummy_chunks = [{"text": "Test chunk", "laureate": "Test", "year_awarded": 2020, "source_type": "lecture", "score": 0.8, "chunk_id": 1}]
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = dummy_chunks

    with patch("rag.query_engine.get_query_router") as mock_router, \
         patch("rag.query_engine.get_mode_aware_retriever", return_value=mock_retriever) as mock_get_retriever, \
         patch("rag.query_engine.call_openai", return_value={"answer": "Test answer."}):
        mock_router.return_value.route_query.return_value = DummyRouteResult()
        
        # Test without explicit model_id
        result = query_engine.answer_query("Test query")
        
        # Verify retriever factory was called with default model_id
        mock_get_retriever.assert_called_once_with(None)  # None should trigger DEFAULT_MODEL_ID
        
        # Verify downstream logic works as expected
        assert result["answer_type"] == "rag"
        assert "Test answer" in result["answer"]
        assert len(result["sources"]) == 1
        assert "Test chunk" in result["sources"][0]["text"] 