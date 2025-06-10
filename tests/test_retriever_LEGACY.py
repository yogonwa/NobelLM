import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import json
import os
from pathlib import Path

# --- Tests for retriever.py ---

def test_retrieve_with_valid_filters(monkeypatch):
    """Test retriever with valid filters and embedding (mocked FAISS and metadata)."""
    from rag import retriever
    # Mock FAISS index and metadata
    mock_index = MagicMock()
    mock_index.search.return_value = (np.array([[0.9, 0.8, 0.7]]), np.array([[0, 1, 2]]))
    # Mock reconstruct_n to return a proper numpy array
    mock_vectors = np.random.rand(3, 768).astype(np.float32)  # 3 vectors of dimension 768
    mock_index.reconstruct_n.return_value = mock_vectors
    mock_index.ntotal = 3
    mock_metadata = [
        {"text": "A", "laureate": "X", "year_awarded": 2000, "chunk_id": "c1", "source_type": "lecture"},
        {"text": "B", "laureate": "Y", "year_awarded": 2001, "chunk_id": "c2", "source_type": "lecture"},
        {"text": "C", "laureate": "Z", "year_awarded": 2002, "chunk_id": "c3", "source_type": "lecture"},
    ]
    monkeypatch.setattr(retriever, "load_index_and_metadata", lambda model_id: (mock_index, mock_metadata))
    # Patch is_supported_index to return True for our mock
    monkeypatch.setattr(retriever, "is_supported_index", lambda index: True)
    
    # Create a normalized embedding vector
    emb = np.random.rand(768).astype(np.float32)
    emb = emb / np.linalg.norm(emb)  # Normalize the vector
    
    results = retriever.query_index(emb, model_id="bge-large", top_k=3, score_threshold=0.1)
    assert len(results) == 3
    assert all(0.7 <= r["score"] <= 0.9 for r in results)
    assert results[0]["rank"] == 0
    assert all("chunk_id" in r for r in results)

def test_retrieve_with_zero_vector():
    """Test retriever with a zero vector embedding (should raise ValueError)."""
    from rag import retriever
    emb = np.zeros((768,), dtype=np.float32)
    with pytest.raises(ValueError):
        retriever.query_index(emb, model_id="bge-large", top_k=3, score_threshold=0.1)

# --- Tests for dual_process_retriever.py ---

def test_dual_process_retriever_success(monkeypatch):
    """Test dual_process_retriever returns results (mock subprocess and file I/O)."""
    from rag import dual_process_retriever
    mock_results = [{"text": "A", "score": 0.9}]
    # Patch SentenceTransformer.encode
    monkeypatch.setattr("rag.dual_process_retriever.SentenceTransformer", MagicMock())
    monkeypatch.setattr("rag.dual_process_retriever.SentenceTransformer.encode", 
                       lambda self, q, normalize_embeddings: np.ones((768,), dtype=np.float32))
    
    # Create a mock result object with stdout
    mock_result = MagicMock()
    mock_result.stdout = json.dumps(mock_results)
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)
    
    results = dual_process_retriever.retrieve_chunks_dual_process("query", model_id="bge-large", top_k=1)
    assert isinstance(results, list)
    assert results[0]["score"] == 0.9

def test_dual_process_retriever_subprocess_error(monkeypatch):
    """Test dual_process_retriever handles subprocess error gracefully."""
    from rag import dual_process_retriever
    monkeypatch.setattr("rag.dual_process_retriever.SentenceTransformer", MagicMock())
    monkeypatch.setattr("rag.dual_process_retriever.SentenceTransformer.encode", lambda self, q, normalize_embeddings: np.ones((768,), dtype=np.float32))
    # Patch subprocess.run to raise error
    def raise_error(*a, **kw):
        raise RuntimeError("Subprocess failed")
    monkeypatch.setattr("subprocess.run", raise_error)
    # Patch file I/O
    monkeypatch.setattr("builtins.open", lambda *a, **kw: MagicMock())
    monkeypatch.setattr("json.load", lambda f: [{"text": "A", "score": 0.9}])
    with pytest.raises(RuntimeError):
        dual_process_retriever.retrieve_chunks_dual_process("query", model_id="bge-large", top_k=1)

# --- Additional tests for query_index ---
def test_query_index_returns_top_k(monkeypatch):
    """Test that query_index returns the correct number of top_k results and correct metadata."""
    from rag import retriever
    import numpy as np
    
    # Setup mock index with proper vector reconstruction and search results
    mock_index = MagicMock()
    mock_vectors = np.random.rand(3, 768).astype(np.float32)
    mock_index.reconstruct_n.return_value = mock_vectors
    mock_index.ntotal = 3
    # Add search results for the no-filter case
    mock_index.search.return_value = (np.array([[0.9, 0.8]]), np.array([[0, 1]]))
    
    # Metadata with all required fields
    mock_metadata = [
        {
            "text": f"Chunk {i}",
            "laureate": f"L{i}",
            "year_awarded": 2000 + i,
            "chunk_id": f"c{i}",
            "source_type": "lecture"
        }
        for i in range(3)
    ]
    
    # Mock the loader and patch is_supported_index
    monkeypatch.setattr(retriever, "load_index_and_metadata", 
                       lambda model_id: (mock_index, mock_metadata))
    monkeypatch.setattr(retriever, "is_supported_index", lambda index: True)
    
    # Create a query vector that will give predictable scores
    query_vector = np.ones((768,), dtype=np.float32)
    query_vector = query_vector / np.linalg.norm(query_vector)
    
    # Execute query
    results = retriever.query_index(
        query_vector,
        model_id="bge-large",
        top_k=2,  # Test with fewer results
        score_threshold=0.1
    )
    
    # Verify results
    assert len(results) == 2, "Should return exactly top_k results"
    assert all(isinstance(r, dict) for r in results)
    assert all("score" in r for r in results)
    assert all("rank" in r for r in results)
    assert results[0]["score"] >= results[1]["score"], "Results should be ordered by score"
    assert all(k in results[0] for k in ["text", "laureate", "year_awarded", "chunk_id", "source_type"])

def test_query_index_with_missing_index(monkeypatch):
    """Test that query_index raises FileNotFoundError if the index file is missing."""
    from rag import retriever
    # Patch load_index_and_metadata to raise FileNotFoundError
    monkeypatch.setattr(retriever, "load_index_and_metadata", lambda model_id: (_ for _ in ()).throw(FileNotFoundError("Index file not found")))
    emb = np.ones((768,), dtype=np.float32)
    with pytest.raises(FileNotFoundError):
        retriever.query_index(emb, model_id="bge-large", top_k=3, score_threshold=0.1)

# --- Tests for path switching and consistency ---
def test_retrieve_chunks_path_switching(monkeypatch):
    """Test that retrieve_chunks switches between dual-process and single-process based on environment."""
    from rag import query_engine
    import os
    import numpy as np

    # Create a consistent mock embedding
    mock_embedding = np.ones((768,), dtype=np.float32)
    mock_embedding = mock_embedding / np.linalg.norm(mock_embedding)

    # Mock results that will be returned by both paths
    mock_chunks = [{
        "text": "Test chunk",
        "score": 0.9,
        "chunk_id": "c1",
        "laureate": "Test",
        "year_awarded": 2000,
        "source_type": "lecture"
    }]

    # Mock retrieve_chunks_dual_process in the correct module!
    monkeypatch.setattr("rag.dual_process_retriever.retrieve_chunks_dual_process",
                       lambda query, model_id, top_k, filters=None, score_threshold=0.2, min_return=3, max_return=None: mock_chunks)

    # Mock get_mode_aware_retriever to avoid actual retriever
    monkeypatch.setattr("rag.query_engine.get_mode_aware_retriever",
                       lambda model_id: None)

    # Test both paths
    for use_subprocess in [0, 1]:
        os.environ["NOBELLM_USE_FAISS_SUBPROCESS"] = str(use_subprocess)
        if use_subprocess:
            result = query_engine.retrieve_chunks("test query", k=5, model_id="bge-large")
        else:
            result = query_engine.retrieve_chunks(mock_embedding, k=5, model_id="bge-large")
        assert result == mock_chunks

def test_retrieve_chunks_path_consistency(monkeypatch):
    """Test that both paths produce identical results given the same input."""
    from rag import query_engine
    import os
    import numpy as np

    # Create a consistent mock embedding
    mock_embedding = np.ones((768,), dtype=np.float32)
    mock_embedding = mock_embedding / np.linalg.norm(mock_embedding)

    # Create identical mock results
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

    # Mock retrieve_chunks_dual_process in the correct module
    monkeypatch.setattr("rag.dual_process_retriever.retrieve_chunks_dual_process",
                       lambda query, model_id, top_k, filters=None, score_threshold=0.2, min_return=3, max_return=None: mock_chunks[:top_k])

    # Mock get_mode_aware_retriever to avoid actual retriever
    monkeypatch.setattr("rag.query_engine.get_mode_aware_retriever",
                       lambda model_id: None)

    # Test both paths and compare results
    results = {}
    for use_subprocess in [0, 1]:
        os.environ["NOBELLM_USE_FAISS_SUBPROCESS"] = str(use_subprocess)
        if use_subprocess:
            results[use_subprocess] = query_engine.retrieve_chunks(
                "test query",
                k=2,
                model_id="bge-large"
            )
        else:
            results[use_subprocess] = query_engine.retrieve_chunks(
                mock_embedding,
                k=2,
                model_id="bge-large"
            )

    # Verify results are identical
    assert results[0] == results[1]

def test_dual_process_large_query(monkeypatch):
    """Test that dual-process retriever handles large queries correctly."""
    from rag import dual_process_retriever
    import os
    import tempfile
    import numpy as np
    import json
    
    # Create mock results
    mock_chunks = [{
        "text": "Result",
        "score": 0.9,
        "chunk_id": "c1",
        "laureate": "Test",
        "year_awarded": 2000,
        "source_type": "lecture"
    }]
    
    # Mock model to return consistent embedding
    mock_embedding = np.ones((768,), dtype=np.float32)
    mock_embedding = mock_embedding / np.linalg.norm(mock_embedding)
    mock_model = MagicMock()
    mock_model.encode.return_value = mock_embedding
    monkeypatch.setattr("rag.dual_process_retriever.SentenceTransformer", 
                       lambda *a, **kw: mock_model)
    
    # Mock subprocess to return our results
    mock_result = MagicMock()
    mock_result.stdout = json.dumps(mock_chunks)
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)
    
    # Test with large query
    os.environ["NOBELLM_USE_FAISS_SUBPROCESS"] = "1"
    result = dual_process_retriever.retrieve_chunks_dual_process(
        "x" * 10240,  # Large query
        model_id="bge-large",
        top_k=5,
        score_threshold=0.2
    )
    
    # Verify results
    assert len(result) == 1
    assert result[0]["text"] == "Result"
    assert result[0]["score"] == 0.9
    assert all(k in result[0] for k in ["chunk_id", "laureate", "year_awarded", "source_type"])

def test_dual_process_file_io_errors(monkeypatch):
    """Test that dual-process retriever handles file I/O errors gracefully."""
    from rag import dual_process_retriever
    import os
    import numpy as np
    import json
    from unittest.mock import MagicMock

    # Mock model to return consistent embedding
    mock_embedding = np.ones((768,), dtype=np.float32)
    mock_embedding = mock_embedding / np.linalg.norm(mock_embedding)
    mock_model = MagicMock()
    mock_model.encode.return_value = mock_embedding
    monkeypatch.setattr("rag.dual_process_retriever.SentenceTransformer",
                       lambda *a, **kw: mock_model)

    # Test various file I/O errors
    error_cases = [
        (FileNotFoundError, "Results file not found"),
        (PermissionError, "Permission denied"),
        (json.JSONDecodeError, "Invalid JSON", "invalid json"),
        (IOError, "General I/O error")
    ]

    for error_class, error_msg, *args in error_cases:
        # Create a mock result that will trigger json.loads failure
        mock_result = MagicMock()
        mock_result.stdout = "dummy json"

        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)

        # For JSONDecodeError, mock json.loads to raise it
        if error_class == json.JSONDecodeError:
            monkeypatch.setattr("json.loads", lambda s: (_ for _ in ()).throw(error_class(error_msg, *args, 0)))
        else:
            monkeypatch.setattr("json.loads", lambda s: (_ for _ in ()).throw(error_class(error_msg)))

        os.environ["NOBELLM_USE_FAISS_SUBPROCESS"] = "1"
        with pytest.raises(RuntimeError) as exc_info:
            dual_process_retriever.retrieve_chunks_dual_process(
                "test query",
                model_id="bge-large",
                top_k=5,
                score_threshold=0.2
            )
        assert error_msg in str(exc_info.value), f"Expected error message '{error_msg}' not found" 