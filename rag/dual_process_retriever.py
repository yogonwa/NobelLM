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
from rag.validation import validate_query_string, validate_filters, validate_retrieval_parameters, validate_model_id
from typing import List, Dict, Any, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

def validate_subprocess_inputs(
    query: str,
    model_id: str,
    top_k: int,
    filters: Optional[Dict[str, Any]],
    score_threshold: float,
    min_return: int,
    max_return: Optional[int]
) -> None:
    """
    Validate all inputs before passing to subprocess.
    
    Args:
        query: Query string to validate
        model_id: Model identifier to validate
        top_k: Number of results to retrieve
        filters: Optional metadata filters
        score_threshold: Minimum similarity score
        min_return: Minimum number of results to return
        max_return: Optional maximum number of results to return
        
    Raises:
        ValueError: If any input is invalid
    """
    validate_query_string(query, context="subprocess_query")
    validate_model_id(model_id, context="subprocess_model")
    validate_retrieval_parameters(
        top_k=top_k,
        score_threshold=score_threshold,
        min_return=min_return,
        max_return=max_return,
        context="subprocess_retrieval"
    )
    validate_filters(filters, context="subprocess_filters")


def handle_worker_failures(result: subprocess.CompletedProcess) -> None:
    """
    Handle subprocess failures with detailed error information.
    
    Args:
        result: CompletedProcess result from subprocess.run()
        
    Raises:
        RuntimeError: With detailed error information
    """
    if result.returncode != 0:
        error_msg = f"FAISS worker failed with return code {result.returncode}"
        
        if result.stderr:
            error_msg += f"\nStderr: {result.stderr}"
        
        if result.stdout:
            error_msg += f"\nStdout: {result.stdout}"
        
        logger.error(f"[DualProcess] {error_msg}")
        raise RuntimeError(error_msg)


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
        
    Raises:
        ValueError: If inputs are invalid
        RuntimeError: If subprocess fails
        FileNotFoundError: If worker script is missing
    """
    # Validate all inputs before subprocess execution
    validate_subprocess_inputs(
        query=query,
        model_id=model_id or "bge-large",
        top_k=top_k,
        filters=filters,
        score_threshold=score_threshold,
        min_return=min_return,
        max_return=max_return
    )
    
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
            check=False  # Don't raise exception, handle it manually
        )
        
        # Handle subprocess failures
        handle_worker_failures(result)
        
        # Parse JSON output
        try:
            chunks = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"[DualProcess] Failed to parse worker output: {e}")
            logger.error(f"[DualProcess] Raw output: {result.stdout}")
            raise RuntimeError(f"Failed to parse worker output: {e}")
        
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
        
    except subprocess.TimeoutExpired as e:
        logger.error(f"[DualProcess] Worker timed out: {e}")
        raise RuntimeError(f"FAISS worker timed out: {e}")
    except FileNotFoundError as e:
        logger.error(f"[DualProcess] Worker script not found: {e}")
        raise FileNotFoundError(f"FAISS worker script not found: {e}")
    except Exception as e:
        logger.error(f"[DualProcess] Unexpected error running worker: {e}")
        raise RuntimeError(f"Unexpected error running FAISS worker: {e}") 