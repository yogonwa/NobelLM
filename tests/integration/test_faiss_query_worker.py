"""
Integration test for faiss_query_worker subprocess.

Tests that:
- The subprocess returns correct results
- Filters are applied correctly
- score_threshold / min_return / max_return are respected
"""

import subprocess
import json
import numpy as np
from pathlib import Path
import pytest
import sys

# Use this instead of load_chunk_metadata:
from rag.metadata_utils import load_laureate_metadata

@pytest.fixture(scope="module")
def test_query_embedding():
    """Simple test embedding."""
    vec = np.random.rand(768).astype(np.float32)
    vec /= np.linalg.norm(vec)
    return vec.tolist()

@pytest.fixture(scope="module")
def test_metadata():
    """Load example laureate metadata."""
    return load_laureate_metadata()

def run_faiss_worker_subprocess(
    query: str,
    model_id: str = "bge-large",
    top_k: int = 5,
    score_threshold: float = 0.2,
    min_return: int = 3,
    max_return: int = None,
    filters: dict = None
):
    """Run faiss_query_worker.py as subprocess with given args."""
    worker_path = Path(__file__).parent.parent / "rag/faiss_query_worker.py"
    if not worker_path.exists():
        raise FileNotFoundError(f"Worker script not found at {worker_path}")

    cmd = [
        sys.executable,
        str(worker_path),
        "--query", query,
        "--top_k", str(top_k),
        "--score_threshold", str(score_threshold),  # <--- CORRECT NAME
        "--min_return", str(min_return),
        "--model_id", model_id
    ]
    if max_return:
        cmd.extend(["--max_return", str(max_return)])
    if filters:
        cmd.extend(["--filters", json.dumps(filters)])

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    chunks = json.loads(result.stdout)
    return chunks

def test_faiss_worker_returns_valid_chunks(test_query_embedding, test_metadata):
    """Test basic end-to-end FAISS worker subprocess run."""
    query = "What did Toni Morrison say about justice?"
    chunks = run_faiss_worker_subprocess(query)

    assert isinstance(chunks, list)
    assert len(chunks) > 0
    first_chunk = chunks[0]
    # Basic schema checks
    assert "text" in first_chunk
    assert "score" in first_chunk
    assert "chunk_id" in first_chunk
    assert "laureate" in first_chunk
    assert "year_awarded" in first_chunk

def test_faiss_worker_filters_applied(test_query_embedding, test_metadata):
    """Test that filters are passed correctly and filter results."""
    query = "What did Toni Morrison say about justice?"
    filters = {"laureate": "Toni Morrison"}

    chunks = run_faiss_worker_subprocess(query, filters=filters)

    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["laureate"] == "Toni Morrison"

def test_faiss_worker_score_threshold(test_query_embedding, test_metadata):
    """Test that score_threshold is respected."""
    query = "What did Toni Morrison say about justice?"
    threshold = 0.5

    chunks = run_faiss_worker_subprocess(query, score_threshold=threshold)

    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["score"] >= threshold

def test_faiss_worker_min_max_return(test_query_embedding, test_metadata):
    """Test min_return and max_return behavior."""
    query = "What did Toni Morrison say about justice?"
    min_return = 2
    max_return = 4

    chunks = run_faiss_worker_subprocess(
        query, min_return=min_return, max_return=max_return
    )

    assert len(chunks) >= min_return
    assert len(chunks) <= max_return
