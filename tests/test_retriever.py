import pytest
import numpy as np
import json
import os
from unittest.mock import MagicMock
import subprocess
from unittest.mock import patch

# --- Test: retrieve_with_valid_filters ---

def test_retrieve_with_valid_filters(monkeypatch):
    from rag import retriever

    mock_index = MagicMock()
    mock_index.search.return_value = (np.array([[0.9, 0.8, 0.7]]), np.array([[0, 1, 2]]))
    mock_index.reconstruct_n.return_value = np.random.rand(3, 768).astype(np.float32)
    mock_index.ntotal = 3

    mock_metadata = [
        {"text": "A", "laureate": "X", "year_awarded": 2000, "chunk_id": "c1", "source_type": "lecture"},
        {"text": "B", "laureate": "Y", "year_awarded": 2001, "chunk_id": "c2", "source_type": "lecture"},
        {"text": "C", "laureate": "Z", "year_awarded": 2002, "chunk_id": "c3", "source_type": "lecture"},
    ]

    monkeypatch.setattr(retriever, "load_index_and_metadata", lambda model_id: (mock_index, mock_metadata))
    monkeypatch.setattr(retriever, "is_supported_index", lambda index: True)

    emb = np.random.rand(768).astype(np.float32)
    emb /= np.linalg.norm(emb)

    results = retriever.query_index(emb, model_id="bge-large", top_k=3, score_threshold=0.1)
    assert len(results) == 3
    assert all("chunk_id" in r for r in results)
    assert all(r["score"] >= 0.1 for r in results)

# --- Test: retrieve_chunks_path_switching ---

def test_retrieve_chunks_path_switching(monkeypatch):
    from rag import query_engine
    import numpy as np

    mock_embedding = np.ones((768,), dtype=np.float32)
    mock_embedding /= np.linalg.norm(mock_embedding)

    mock_chunks = [{
        "text": "Test chunk",
        "score": 0.9,
        "chunk_id": "c1",
        "laureate": "Test",
        "year_awarded": 2000,
        "source_type": "lecture"
    }]

    monkeypatch.setattr(
        "rag.dual_process_retriever.retrieve_chunks_dual_process",
        lambda query, model_id, top_k, filters=None, score_threshold=0.2, min_return=3, max_return=None: mock_chunks
    )

    class MockRetriever:
        def __init__(self, model_id):
            self.model_id = model_id

        def retrieve(self, query, top_k=5, filters=None):
            assert isinstance(query, np.ndarray)
            return mock_chunks

    monkeypatch.setattr("rag.query_engine.get_mode_aware_retriever", lambda model_id: MockRetriever(model_id))

    for use_subprocess in [0, 1]:
        os.environ["NOBELLM_USE_FAISS_SUBPROCESS"] = str(use_subprocess)
        result = query_engine.retrieve_chunks(mock_embedding, k=5, model_id="bge-large")
        assert len(result) == 1
        assert result[0]["text"] == "Test chunk"

# --- Test: retrieve_chunks_path_consistency ---

def test_retrieve_chunks_path_consistency(monkeypatch):
    from rag import query_engine
    import numpy as np

    mock_embedding = np.ones((768,), dtype=np.float32)
    mock_embedding /= np.linalg.norm(mock_embedding)

    mock_chunks = [
        {
            "text": "Test chunk",
            "score": 0.9,
            "chunk_id": "c1",
            "laureate": "Test",
            "year_awarded": 2000,
            "source_type": "lecture"
        },
        {
            "text": "Another chunk",
            "score": 0.8,
            "chunk_id": "c2",
            "laureate": "Test",
            "year_awarded": 2001,
            "source_type": "lecture"
        }
    ]

    monkeypatch.setattr(
        "rag.dual_process_retriever.retrieve_chunks_dual_process",
        lambda query, model_id, top_k, filters=None, score_threshold=0.2, min_return=3, max_return=None: mock_chunks[:top_k]
    )

    class MockRetriever:
        def __init__(self, model_id):
            self.model_id = model_id

        def retrieve(self, query, top_k=5, filters=None):
            assert isinstance(query, np.ndarray)
            return mock_chunks[:top_k]

    monkeypatch.setattr("rag.query_engine.get_mode_aware_retriever", lambda model_id: MockRetriever(model_id))

    results = {}
    for use_subprocess in [0, 1]:
        os.environ["NOBELLM_USE_FAISS_SUBPROCESS"] = str(use_subprocess)
        results[use_subprocess] = query_engine.retrieve_chunks(mock_embedding, k=2, model_id="bge-large")

    assert results[0] == results[1], "Results should be identical between modes"

# --- Test: dual_process_file_io_errors ---

def test_dual_process_file_io_errors(monkeypatch):
    """
    Test error handling in retrieve_chunks_dual_process.
    
    This function is critical for Mac/Intel compatibility as it runs FAISS search in a subprocess.
    We need to ensure it properly handles and wraps both subprocess and JSON parsing errors.
    
    The function should:
    1. Catch subprocess errors (CalledProcessError) and wrap them in RuntimeError
    2. Catch JSON parsing errors and wrap them in RuntimeError
    3. Never expose raw subprocess or JSON errors to callers
    """
    from rag import dual_process_retriever

    # Setup model mock - this is needed because the function uses SentenceTransformer
    mock_embedding = np.ones((768,), dtype=np.float32)
    mock_embedding /= np.linalg.norm(mock_embedding)
    mock_model = MagicMock()
    mock_model.encode.return_value = mock_embedding
    monkeypatch.setattr("rag.dual_process_retriever.SentenceTransformer", lambda *a, **kw: mock_model)

    # Test Case 1: Subprocess fails to execute (e.g., script not found)
    with monkeypatch.context() as m:
        def mock_failed_subprocess(*a, **kw):
            raise subprocess.CalledProcessError(
                returncode=1,
                cmd=["python", "worker.py"],
                stderr="Worker script not found"
            )
        m.setattr("subprocess.run", mock_failed_subprocess)
        
        os.environ["NOBELLM_USE_FAISS_SUBPROCESS"] = "1"
        with pytest.raises(RuntimeError) as exc_info:
            dual_process_retriever.retrieve_chunks_dual_process(
                "test query",
                model_id="bge-large",
                top_k=5
            )
        assert "FAISS worker failed" in str(exc_info.value)
        assert "Worker script not found" in str(exc_info.value)

    # Test Case 2: Subprocess runs but returns invalid JSON
    with monkeypatch.context() as m:
        mock_result = MagicMock()
        mock_result.stdout = "invalid json"
        m.setattr("subprocess.run", lambda *a, **kw: mock_result)
        
        os.environ["NOBELLM_USE_FAISS_SUBPROCESS"] = "1"
        with pytest.raises(RuntimeError) as exc_info:
            dual_process_retriever.retrieve_chunks_dual_process(
                "test query",
                model_id="bge-large",
                top_k=5
            )
        assert "Failed to parse worker output" in str(exc_info.value)

    # Test Case 3: Subprocess runs but encounters permission error
    with monkeypatch.context() as m:
        def mock_permission_error(*a, **kw):
            raise subprocess.CalledProcessError(
                returncode=1,
                cmd=["python", "worker.py"],
                stderr="Permission denied"
            )
        m.setattr("subprocess.run", mock_permission_error)
        
        os.environ["NOBELLM_USE_FAISS_SUBPROCESS"] = "1"
        with pytest.raises(RuntimeError) as exc_info:
            dual_process_retriever.retrieve_chunks_dual_process(
                "test query",
                model_id="bge-large",
                top_k=5
            )
        assert "FAISS worker failed" in str(exc_info.value)
        assert "Permission denied" in str(exc_info.value)

# --- Test: InProcessRetriever filtering and threshold behavior ---

def test_inprocess_retriever_filters_and_threshold(monkeypatch):
    """Test InProcessRetriever.retrieve() returns correct chunks after applying filter_top_chunks"""
    from rag.retriever import InProcessRetriever
    
    # Mock chunks with varying scores
    mock_chunks = [
        {"chunk_id": "c1", "text": "High quality", "score": 0.9, "laureate": "Test", "year_awarded": 2000, "source_type": "lecture"},
        {"chunk_id": "c2", "text": "Low quality", "score": 0.1, "laureate": "Test", "year_awarded": 2001, "source_type": "lecture"},
        {"chunk_id": "c3", "text": "Medium quality", "score": 0.5, "laureate": "Test", "year_awarded": 2002, "source_type": "lecture"},
    ]
    
    # Mock the query_index function to return our test chunks
    with patch("rag.retriever.query_index", return_value=mock_chunks) as mock_query_index, \
         patch("rag.retriever.SentenceTransformer") as mock_sentence_transformer, \
         patch("rag.retriever.load_index") as mock_load_index:
        # Setup mock model with proper return values
        mock_model = MagicMock()
        mock_model.encode.return_value = np.ones(768, dtype=np.float32)
        mock_model.get_sentence_embedding_dimension.return_value = 768  # Return actual integer
        mock_sentence_transformer.return_value = mock_model
        
        # Setup mock index
        mock_index = MagicMock()
        mock_index.is_trained = True
        mock_index.d = 768
        mock_load_index.return_value = mock_index
        
        retriever = InProcessRetriever(model_id="bge-large")
        result = retriever.retrieve("test query", top_k=3, score_threshold=0.5, min_return=2)
        
        # Should filter out low quality chunk but return at least min_return
        assert len(result) == 2  # min_return=2, only 2 chunks pass threshold
        assert all(chunk["score"] >= 0.5 for chunk in result)
        assert result[0]["chunk_id"] == "c1"  # Highest score first
        assert result[1]["chunk_id"] == "c3"  # Second highest score

def test_retriever_fallbacks_to_min_return_when_needed(monkeypatch):
    """Test that retrievers respect min_return even when score threshold filters out chunks"""
    from rag.retriever import InProcessRetriever
    
    # All chunks below threshold
    mock_chunks = [
        {"chunk_id": "c1", "text": "Low", "score": 0.1, "laureate": "Test", "year_awarded": 2000, "source_type": "lecture"},
        {"chunk_id": "c2", "text": "Lower", "score": 0.05, "laureate": "Test", "year_awarded": 2001, "source_type": "lecture"},
    ]
    
    with patch("rag.retriever.query_index", return_value=mock_chunks), \
         patch("rag.retriever.SentenceTransformer") as mock_sentence_transformer, \
         patch("rag.retriever.load_index") as mock_load_index:
        # Setup mock model with proper return values
        mock_model = MagicMock()
        mock_model.encode.return_value = np.ones(768, dtype=np.float32)
        mock_model.get_sentence_embedding_dimension.return_value = 768  # Return actual integer
        mock_sentence_transformer.return_value = mock_model
        
        # Setup mock index
        mock_index = MagicMock()
        mock_index.is_trained = True
        mock_index.d = 768
        mock_load_index.return_value = mock_index
        
        retriever = InProcessRetriever(model_id="bge-large")
        result = retriever.retrieve("test query", top_k=2, score_threshold=0.9, min_return=2)
        
        # Should return all chunks even though none pass threshold (min_return fallback)
        assert len(result) == 2
        assert result[0]["chunk_id"] == "c1"  # Original order preserved
        assert result[1]["chunk_id"] == "c2"

def test_retriever_respects_max_return(monkeypatch):
    """Test that retrievers respect max_return parameter"""
    from rag.retriever import InProcessRetriever
    
    # Many chunks above threshold
    mock_chunks = [
        {"chunk_id": f"c{i}", "text": f"Chunk {i}", "score": 0.9, "laureate": "Test", "year_awarded": 2000, "source_type": "lecture"}
        for i in range(10)
    ]
    
    with patch("rag.retriever.query_index", return_value=mock_chunks), \
         patch("rag.retriever.SentenceTransformer") as mock_sentence_transformer, \
         patch("rag.retriever.load_index") as mock_load_index:
        # Setup mock model with proper return values
        mock_model = MagicMock()
        mock_model.encode.return_value = np.ones(768, dtype=np.float32)
        mock_model.get_sentence_embedding_dimension.return_value = 768  # Return actual integer
        mock_sentence_transformer.return_value = mock_model
        
        # Setup mock index
        mock_index = MagicMock()
        mock_index.is_trained = True
        mock_index.d = 768
        mock_load_index.return_value = mock_index
        
        retriever = InProcessRetriever(model_id="bge-large")
        result = retriever.retrieve("test query", top_k=10, score_threshold=0.1, min_return=3, max_return=5)
        
        # Should return at most max_return chunks
        assert len(result) == 5
        assert all(chunk["score"] >= 0.1 for chunk in result)

def test_inprocess_retriever_retrieve(monkeypatch):
    """Test InProcessRetriever.retrieve() with score_threshold and min_return filtering"""
    from rag.retriever import InProcessRetriever
    
    # Mock chunks with varying scores
    mock_chunks = [
        {"chunk_id": "c1", "text": "High quality", "score": 0.9, "laureate": "Test", "year_awarded": 2000, "source_type": "lecture"},
        {"chunk_id": "c2", "text": "Low quality", "score": 0.1, "laureate": "Test", "year_awarded": 2001, "source_type": "lecture"},
        {"chunk_id": "c3", "text": "Medium quality", "score": 0.5, "laureate": "Test", "year_awarded": 2002, "source_type": "lecture"},
        {"chunk_id": "c4", "text": "Another high", "score": 0.8, "laureate": "Test", "year_awarded": 2003, "source_type": "lecture"},
    ]
    
    # Mock the query_index function to return our test chunks
    with patch("rag.retriever.query_index", return_value=mock_chunks) as mock_query_index, \
         patch("rag.retriever.SentenceTransformer") as mock_sentence_transformer, \
         patch("rag.retriever.load_index") as mock_load_index:
        # Setup mock model with proper return values
        mock_model = MagicMock()
        mock_model.encode.return_value = np.ones(768, dtype=np.float32)
        mock_model.get_sentence_embedding_dimension.return_value = 768  # Return actual integer
        mock_sentence_transformer.return_value = mock_model
        
        # Setup mock index
        mock_index = MagicMock()
        mock_index.is_trained = True
        mock_index.d = 768
        mock_load_index.return_value = mock_index
        
        retriever = InProcessRetriever(model_id="bge-large")
        result = retriever.retrieve("test query", top_k=4, score_threshold=0.5, min_return=2)
        
        # Should filter out low quality chunk but return at least min_return
        assert len(result) == 3  # 3 chunks pass threshold (0.9, 0.5, 0.8)
        assert all(chunk["score"] >= 0.5 for chunk in result)
        assert result[0]["chunk_id"] == "c1"  # Highest score first (0.9)
        assert result[1]["chunk_id"] == "c4"  # Second highest score (0.8)
        assert result[2]["chunk_id"] == "c3"  # Third highest score (0.5)

def test_subprocess_retriever_retrieve(monkeypatch):
    """Test SubprocessRetriever.retrieve() calls retrieve_chunks_dual_process with correct args"""
    from rag.retriever import SubprocessRetriever
    
    mock_chunks = [
        {"chunk_id": "c1", "text": "Test content", "score": 0.9, "laureate": "Test", "year_awarded": 2000, "source_type": "lecture"},
        {"chunk_id": "c2", "text": "More content", "score": 0.8, "laureate": "Test", "year_awarded": 2001, "source_type": "lecture"},
    ]
    
    with patch("rag.dual_process_retriever.retrieve_chunks_dual_process", return_value=mock_chunks) as mock_dual, \
         patch("rag.retriever.SentenceTransformer") as mock_sentence_transformer, \
         patch("rag.retriever.load_index") as mock_load_index:
        # Setup mock model with proper return values
        mock_model = MagicMock()
        mock_model.encode.return_value = np.ones(768, dtype=np.float32)
        mock_model.get_sentence_embedding_dimension.return_value = 768
        mock_sentence_transformer.return_value = mock_model
        
        # Setup mock index
        mock_index = MagicMock()
        mock_index.is_trained = True
        mock_index.d = 768
        mock_load_index.return_value = mock_index
        
        retriever = SubprocessRetriever(model_id="bge-large")
        result = retriever.retrieve("test query", top_k=2, score_threshold=0.5, min_return=1, max_return=3)
        
        # Verify dual process was called with correct arguments
        mock_dual.assert_called_once_with(
            "test query",
            model_id="bge-large",
            top_k=2,
            filters=None,
            score_threshold=0.5,
            min_return=1,
            max_return=3
        )
        assert result == mock_chunks
