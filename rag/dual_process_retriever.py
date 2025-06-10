"""
Dual-Process Retriever for NobelLM RAG

Implements subprocess-based FAISS retrieval for Mac/Intel compatibility.
This function is used when NOBELLM_USE_FAISS_SUBPROCESS=1 is set.
"""
import tempfile
import os
import subprocess
import json
import numpy as np
import logging
import sys
from sentence_transformers import SentenceTransformer
from rag.model_config import get_model_config
from typing import List, Dict, Any, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

def retrieve_chunks_dual_process(
    query: str,
    model_id: str = None,
    top_k: int = 5,
    filters: Dict[str, Any] = None,
    score_threshold: float = 0.2,
    min_return: int = 3,
    max_return: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve chunks using a subprocess for FAISS search.
    This is the safe path for Mac/Intel environments.

    Args:
        query: The query string
        model_id: Optional model identifier
        top_k: Number of chunks to retrieve (default: 5)
        filters: Optional metadata filters
        score_threshold: Minimum similarity score (default: 0.2)
        min_return: Minimum number of chunks to return (default: 3)
        max_return: Optional maximum number of chunks to return

    Returns:
        List of chunks, filtered by score threshold
    """
    # Get the path to the worker script
    worker_path = Path(__file__).parent / "faiss_query_worker.py"
    if not worker_path.exists():
        raise FileNotFoundError(f"Worker script not found at {worker_path}")

    # Build command with all parameters
    cmd = [
        sys.executable,
        str(worker_path),
        "--query", query,
        "--top_k", str(top_k),
        "--score_threshold", str(score_threshold),
        "--min_return", str(min_return)
    ]
    if model_id:
        cmd.extend(["--model_id", model_id])
    if max_return:
        cmd.extend(["--max_return", str(max_return)])
    if filters:
        cmd.extend(["--filters", json.dumps(filters)])

    # Run worker in subprocess
    logger.info(f"[DualProcess] Running worker with command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        chunks = json.loads(result.stdout)
        
        # Log score distribution
        if chunks:
            scores = [c["score"] for c in chunks]
            logger.info(
                f"[DualProcess] Retrieved {len(chunks)} chunks — "
                f"mean score: {np.mean(scores):.3f}, stddev: {np.std(scores):.3f}, "
                f"min: {min(scores):.3f}, max: {max(scores):.3f}"
            )
        else:
            logger.warning("[DualProcess] No chunks returned from worker")
            
        return chunks
        
    except subprocess.CalledProcessError as e:
        logger.error(f"[DualProcess] Worker failed: {e.stderr}")
        raise RuntimeError(f"FAISS worker failed: {e.stderr}")
    except json.JSONDecodeError as e:
        logger.error(f"[DualProcess] Failed to parse worker output: {e}")
        raise RuntimeError("Failed to parse worker output") 