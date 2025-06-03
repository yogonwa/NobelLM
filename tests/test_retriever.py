import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# --- Tests for retriever.py ---

def test_retrieve_with_valid_filters(monkeypatch):
    """Test retriever with valid filters and embedding (mocked FAISS and metadata)."""
    from rag import retriever
    # Mock FAISS index and metadata
    mock_index = MagicMock()
    mock_index.search.return_value = (np.array([[0.9, 0.8, 0.7]]), np.array([[0, 1, 2]]))
    mock_metadata = [
        {"text": "A", "laureate": "X", "year_awarded": 2000},
        {"text": "B", "laureate": "Y", "year_awarded": 2001},
        {"text": "C", "laureate": "Z", "year_awarded": 2002},
    ]
    monkeypatch.setattr(retriever, "load_index_and_metadata", lambda model_id: (mock_index, mock_metadata))
    emb = np.ones((768,), dtype=np.float32)
    results = retriever.query_index(emb, model_id="bge-large", top_k=3, min_score=0.1)
    assert len(results) == 3
    assert all(0.7 <= r["score"] <= 0.9 for r in results)
    assert results[0]["rank"] == 0


def test_retrieve_with_zero_vector():
    """Test retriever with a zero vector embedding (should raise ValueError)."""
    from rag import retriever
    emb = np.zeros((768,), dtype=np.float32)
    with pytest.raises(ValueError):
        retriever.query_index(emb, model_id="bge-large", top_k=3, min_score=0.1)

# --- Tests for dual_process_retriever.py ---

def test_dual_process_retriever_success(monkeypatch):
    """Test dual_process_retriever returns results (mock subprocess and file I/O)."""
    from rag import dual_process_retriever
    mock_results = [{"text": "A", "score": 0.9}]
    # Patch SentenceTransformer.encode
    monkeypatch.setattr("rag.dual_process_retriever.SentenceTransformer", MagicMock())
    monkeypatch.setattr("rag.dual_process_retriever.SentenceTransformer.encode", lambda self, q, normalize_embeddings: np.ones((768,), dtype=np.float32))
    # Patch subprocess.run
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: None)
    # Patch file I/O
    class DummyFile:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def read(self): return '[{"text": "A", "score": 0.9}]'
        def write(self, *a, **kw): return None
    monkeypatch.setattr("builtins.open", lambda *a, **kw: DummyFile())
    monkeypatch.setattr("json.load", lambda f: mock_results)
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
    mock_index = MagicMock()
    # Only return top_k results from .search()
    mock_index.search.return_value = (np.array([[0.95, 0.85, 0.75]]), np.array([[0, 1, 2]]))
    mock_metadata = [
        {"text": f"Chunk {i}", "laureate": f"L{i}", "year_awarded": 2000 + i} for i in range(3)
    ]
    monkeypatch.setattr(retriever, "load_index_and_metadata", lambda model_id: (mock_index, mock_metadata))
    emb = np.ones((768,), dtype=np.float32)
    results = retriever.query_index(emb, model_id="bge-large", top_k=3, min_score=0.1)
    assert len(results) == 3
    assert results[0]["text"] == "Chunk 0"
    assert results[1]["text"] == "Chunk 1"
    assert results[2]["text"] == "Chunk 2"
    assert all("score" in r for r in results)
    assert all("rank" in r for r in results)

def test_query_index_with_missing_index(monkeypatch):
    """Test that query_index raises FileNotFoundError if the index file is missing."""
    from rag import retriever
    # Patch load_index_and_metadata to raise FileNotFoundError
    monkeypatch.setattr(retriever, "load_index_and_metadata", lambda model_id: (_ for _ in ()).throw(FileNotFoundError("Index file not found")))
    emb = np.ones((768,), dtype=np.float32)
    with pytest.raises(FileNotFoundError):
        retriever.query_index(emb, model_id="bge-large", top_k=3, min_score=0.1) 