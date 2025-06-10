"""
Global threading configuration for NobelLM.

Sets environment variables to prevent Mac/Intel subprocess crashes
and ensures consistent threading behavior across the application.
"""
import os
import logging

logger = logging.getLogger(__name__)

def configure_threading():
    """Configure threading environment variables for FAISS/PyTorch stability."""
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    
    # Optional: log the configuration
    logger.info(f"[Global Threading] OMP_NUM_THREADS={os.environ['OMP_NUM_THREADS']}, MKL_NUM_THREADS={os.environ['MKL_NUM_THREADS']}")

# Auto-configure on import
configure_threading() 