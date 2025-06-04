import os
import json
import tempfile
import subprocess
import numpy as np
import faiss
import pytest

@pytest.mark.slow
def test_faiss_query_worker_with_filters():
    """
    Integration test: Runs faiss_query_worker.py as a subprocess with a real tiny FAISS index, metadata, and filters.
    Asserts that only chunks matching the filter are returned.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Create tiny FAISS index (3 vectors, 2D)
        dim = 2
        index = faiss.IndexFlatIP(dim)
        vectors = np.array([[1, 0], [0, 1], [1, 1]], dtype=np.float32)
        faiss.normalize_L2(vectors)
        index.add(vectors)
        index_path = os.path.join(tmpdir, "index.faiss")
        faiss.write_index(index, index_path)

        # 2. Write metadata JSONL (3 chunks, with gender field)
        metadata = [
            {"chunk_id": "c0", "gender": "female", "text": "A"},
            {"chunk_id": "c1", "gender": "male", "text": "B"},
            {"chunk_id": "c2", "gender": "female", "text": "C"},
        ]
        metadata_path = os.path.join(tmpdir, "chunk_metadata.jsonl")
        with open(metadata_path, "w", encoding="utf-8") as f:
            for m in metadata:
                f.write(json.dumps(m) + "\n")

        # 3. Write query embedding (2D vector)
        query_emb = np.array([1, 0], dtype=np.float32)
        query_emb = query_emb / np.linalg.norm(query_emb)
        emb_path = os.path.join(tmpdir, "query_embedding.npy")
        np.save(emb_path, query_emb)

        # 4. Write filters.json
        filters = {"gender": "female"}
        filters_path = os.path.join(tmpdir, "filters.json")
        with open(filters_path, "w", encoding="utf-8") as f:
            json.dump(filters, f)

        # 5. No need to patch model config anymore
        model_id = "bge-large"

        try:
            # 6. Call faiss_query_worker.py as subprocess, setting PYTHONPATH
            results_path = os.path.join(tmpdir, "retrieval_results.json")
            cmd = [
                "python", "rag/faiss_query_worker.py",
                "--model", model_id,
                "--dir", tmpdir,
                "--filters", filters_path,
                "--index_path", index_path,
                "--metadata_path", metadata_path
            ]
            env = os.environ.copy()
            env["PYTHONPATH"] = os.getcwd()
            result = subprocess.run(cmd, check=True, env=env, capture_output=True, text=True)
            print("STDOUT:\n", result.stdout)
            print("STDERR:\n", result.stderr)

            # 7. Read and check results
            with open(results_path, "r", encoding="utf-8") as f:
                results = json.load(f)
            # Only chunks with gender == "female" should be returned
            assert all(r["gender"] == "female" for r in results)
            # Should return at least one result
            assert len(results) > 0
            # Should not return any male chunk
            assert all(r["chunk_id"] != "c1" for r in results)
        finally:
            pass  # No config to restore 