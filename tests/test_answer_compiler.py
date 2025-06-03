import pytest
from unittest.mock import patch, MagicMock

# --- Test for factual/metadata answer ---
def test_answer_compiler_metadata():
    from rag import query_engine
    # Patch QueryRouter to always return a metadata answer
    class DummyRouteResult:
        answer_type = "metadata"
        metadata_answer = {"answer": "Toni Morrison won in 1993.", "laureate": "Toni Morrison", "year_awarded": 1993}
    with patch("rag.query_engine.get_query_router") as mock_router:
        mock_router.return_value.route_query.return_value = DummyRouteResult()
        result = query_engine.answer_query("When did Toni Morrison win?")
        assert result["answer_type"] == "metadata"
        assert "Toni Morrison" in result["answer"]
        assert result["metadata_answer"]["year_awarded"] == 1993
        assert result["sources"] == []

# --- Test for thematic (RAG) answer ---
def test_answer_compiler_thematic():
    from rag import query_engine
    # Patch QueryRouter to return a RAG/thematic answer
    class DummyRouteResult:
        answer_type = "rag"
        intent = "thematic"
        retrieval_config = MagicMock(top_k=3, filters=None, score_threshold=None)
    dummy_chunks = [
        {"text": "Theme chunk 1.", "laureate": "A", "year_awarded": 2000, "source_type": "lecture", "score": 0.9, "chunk_id": 1},
        {"text": "Theme chunk 2.", "laureate": "B", "year_awarded": 2001, "source_type": "speech", "score": 0.8, "chunk_id": 2}
    ]
    with patch("rag.query_engine.get_query_router") as mock_router, \
         patch("rag.query_engine.ThematicRetriever") as mock_thematic, \
         patch("rag.query_engine.embed_query", return_value=None), \
         patch("rag.query_engine.retrieve_chunks", return_value=dummy_chunks), \
         patch("rag.query_engine.call_openai", return_value={"answer": "Synthesized answer."}):
        mock_router.return_value.route_query.return_value = DummyRouteResult()
        mock_thematic.return_value.retrieve.return_value = dummy_chunks
        result = query_engine.answer_query("What are common themes?")
        assert result["answer_type"] == "rag"
        assert "Synthesized answer" in result["answer"]
        assert isinstance(result["sources"], list)
        assert len(result["sources"]) == 2
        assert "Theme chunk 1"[:10] in result["sources"][0]["text_snippet"]

# --- Test for hybrid query (should route as RAG or metadata depending on router logic) ---
def test_answer_compiler_hybrid():
    from rag import query_engine
    # Patch QueryRouter to return a RAG answer for a hybrid query
    class DummyRouteResult:
        answer_type = "rag"
        intent = "hybrid"
        retrieval_config = MagicMock(top_k=3, filters=None, score_threshold=None)
    dummy_chunks = [
        {"text": "Hybrid chunk.", "laureate": "C", "year_awarded": 2010, "source_type": "lecture", "score": 0.7, "chunk_id": 3}
    ]
    with patch("rag.query_engine.get_query_router") as mock_router, \
         patch("rag.query_engine.embed_query", return_value=None), \
         patch("rag.query_engine.retrieve_chunks", return_value=dummy_chunks), \
         patch("rag.query_engine.call_openai", return_value={"answer": "Hybrid answer."}):
        mock_router.return_value.route_query.return_value = DummyRouteResult()
        result = query_engine.answer_query("Write a summary of what Morrison said about justice.")
        assert result["answer_type"] == "rag"
        assert "Hybrid answer" in result["answer"]
        assert isinstance(result["sources"], list)
        assert len(result["sources"]) == 1

# --- Test for no relevant chunks (fallback) ---
def test_answer_compiler_no_chunks():
    from rag import query_engine
    class DummyRouteResult:
        answer_type = "rag"
        intent = "thematic"
        retrieval_config = MagicMock(top_k=3, filters=None, score_threshold=None)
    with patch("rag.query_engine.get_query_router") as mock_router, \
         patch("rag.query_engine.ThematicRetriever") as mock_thematic:
        mock_router.return_value.route_query.return_value = DummyRouteResult()
        mock_thematic.return_value.retrieve.return_value = []
        result = query_engine.answer_query("What are common themes?")
        assert result["answer_type"] == "rag"
        assert "No relevant information found" in result["answer"]
        assert result["sources"] == [] 