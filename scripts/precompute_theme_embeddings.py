#!/usr/bin/env python3
"""
Pre-compute Theme Embeddings Script

This script pre-computes and saves theme embeddings for all supported models
to avoid on-demand computation during runtime.

Usage:
    python scripts/precompute_theme_embeddings.py

This will create:
    data/theme_embeddings/theme_embeddings_bge-large.npz
    data/theme_embeddings/theme_embeddings_miniLM.npz

Author: NobelLM Team
"""
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.theme_embeddings import ThemeEmbeddings
from rag.model_config import MODEL_CONFIGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Pre-compute theme embeddings for all supported models."""
    logger.info("Starting theme embedding pre-computation...")
    
    # Get all supported models
    models = list(MODEL_CONFIGS.keys())
    logger.info(f"Found {len(models)} supported models: {models}")
    
    for model_id in models:
        try:
            logger.info(f"Processing model: {model_id}")
            
            # Initialize ThemeEmbeddings (this will compute and save)
            theme_embeddings = ThemeEmbeddings(model_id)
            
            # Get stats
            stats = theme_embeddings.get_embedding_stats()
            logger.info(f"Model {model_id} stats: {stats}")
            
            # Verify file was created
            embeddings_file = theme_embeddings._get_embeddings_file_path()
            if embeddings_file.exists():
                file_size = embeddings_file.stat().st_size / (1024 * 1024)  # MB
                logger.info(f"Embeddings saved to {embeddings_file} ({file_size:.2f} MB)")
            else:
                logger.error(f"Embeddings file not found: {embeddings_file}")
                
        except Exception as e:
            logger.error(f"Failed to process model {model_id}: {e}")
            continue
    
    logger.info("Theme embedding pre-computation completed!")


if __name__ == "__main__":
    main() 