"""
Theme Embeddings Infrastructure for NobelLM RAG Pipeline

This module pre-computes and manages embeddings for all theme keywords defined in config/themes.json.
It provides model-aware embedding storage, validation, and caching for efficient similarity computation.

Key Features:
- Model-aware: Supports different embedding dimensions (bge-large: 1024d, miniLM: 384d)
- Caching: Efficient storage and retrieval of pre-computed embeddings
- Validation: Ensures embedding consistency and dimension matching
- Health checks: Validates embedding quality and model compatibility

Usage:
    from config.theme_embeddings import ThemeEmbeddings
    
    # Initialize for specific model
    theme_embeddings = ThemeEmbeddings("bge-large")
    
    # Get embedding for a theme keyword
    embedding = theme_embeddings.get_theme_embedding("justice")
    
    # Get all theme embeddings
    all_embeddings = theme_embeddings.get_all_embeddings()

Author: NobelLM Team
"""
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from sentence_transformers import SentenceTransformer
from rag.model_config import get_model_config, MODEL_CONFIGS
from rag.cache import get_model

logger = logging.getLogger(__name__)

class ThemeEmbeddings:
    """
    Manages pre-computed embeddings for theme keywords with model-aware storage and validation.
    """
    
    def __init__(self, model_id: str = "bge-large"):
        """
        Initialize ThemeEmbeddings for the specified model.
        
        Args:
            model_id: Model identifier (e.g., "bge-large", "miniLM")
            
        Raises:
            ValueError: If model_id is not supported
            FileNotFoundError: If themes.json is not found
        """
        if model_id not in MODEL_CONFIGS:
            raise ValueError(f"Model '{model_id}' not supported. Available: {list(MODEL_CONFIGS.keys())}")
        
        self.model_id = model_id
        self.config = get_model_config(model_id)
        self.embedding_dim = self.config["embedding_dim"]
        
        # Load themes
        self.themes = self._load_themes()
        
        # Initialize embeddings cache
        self._embeddings_cache: Dict[str, np.ndarray] = {}
        self._is_initialized = False
        
        # Pre-compute embeddings
        self._initialize_embeddings()
    
    def _load_themes(self) -> Dict[str, List[str]]:
        """
        Load themes from config/themes.json.
        
        Returns:
            Dictionary mapping theme names to keyword lists
            
        Raises:
            FileNotFoundError: If themes.json is not found
        """
        theme_path = Path("config/themes.json")
        if not theme_path.exists():
            raise FileNotFoundError(f"Theme file not found: {theme_path}")
        
        with theme_path.open("r", encoding="utf-8") as f:
            themes = json.load(f)
        
        logger.info(f"Loaded {len(themes)} themes with {sum(len(keywords) for keywords in themes.values())} total keywords")
        return themes
    
    def _initialize_embeddings(self):
        """
        Pre-compute embeddings for all theme keywords.
        First tries to load from disk, falls back to computing if not found.
        Uses cached model to avoid reloading.
        """
        if self._is_initialized:
            return
        
        logger.info(f"Initializing theme embeddings for model '{self.model_id}' (dim: {self.embedding_dim})")
        
        # Try to load from disk first
        if self._load_embeddings_from_disk():
            logger.info(f"Loaded {len(self._embeddings_cache)} theme embeddings from disk")
            self._is_initialized = True
            self._run_health_checks()
            return
        
        # Fallback to computing embeddings
        logger.info("Theme embeddings not found on disk, computing...")
        self._compute_and_save_embeddings()
    
    def _get_embeddings_file_path(self) -> Path:
        """
        Get the file path for storing theme embeddings.
        
        Returns:
            Path to the embeddings file for this model
        """
        embeddings_dir = Path("data/theme_embeddings")
        embeddings_dir.mkdir(exist_ok=True)
        return embeddings_dir / f"theme_embeddings_{self.model_id}.npz"
    
    def _load_embeddings_from_disk(self) -> bool:
        """
        Load theme embeddings from disk if they exist.
        
        Returns:
            True if embeddings were loaded successfully, False otherwise
        """
        embeddings_file = self._get_embeddings_file_path()
        
        if not embeddings_file.exists():
            logger.info(f"Theme embeddings file not found: {embeddings_file}")
            return False
        
        try:
            logger.info(f"Loading theme embeddings from {embeddings_file}")
            
            # Load embeddings from .npz file
            data = np.load(embeddings_file, allow_pickle=True)
            
            # Extract keywords and embeddings
            keywords = data['keywords'].tolist()
            embeddings = data['embeddings']
            
            # Validate dimensions
            if embeddings.shape[1] != self.embedding_dim:
                logger.warning(f"Embedding dimension mismatch in file: expected {self.embedding_dim}, got {embeddings.shape[1]}")
                return False
            
            # Store in cache
            for keyword, embedding in zip(keywords, embeddings):
                self._embeddings_cache[keyword] = embedding.astype(np.float32)
            
            logger.info(f"Successfully loaded {len(self._embeddings_cache)} theme embeddings from disk")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load theme embeddings from disk: {e}")
            return False
    
    def _compute_and_save_embeddings(self):
        """
        Compute theme embeddings and save them to disk.
        """
        try:
            # Get cached model
            model = get_model(self.model_id)
            
            # Collect all unique keywords
            all_keywords = set()
            for keywords in self.themes.values():
                all_keywords.update(keywords)
            
            # Convert to list for batch processing
            keyword_list = list(all_keywords)
            logger.info(f"Computing embeddings for {len(keyword_list)} unique keywords")
            
            # Batch embed all keywords
            embeddings = model.encode(
                keyword_list,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True
            )
            
            # Validate embeddings
            if embeddings.shape[1] != self.embedding_dim:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {self.embedding_dim}, got {embeddings.shape[1]}"
                )
            
            # Store in cache
            for keyword, embedding in zip(keyword_list, embeddings):
                self._embeddings_cache[keyword] = embedding.astype(np.float32)
            
            # Save to disk
            self._save_embeddings_to_disk(keyword_list, embeddings)
            
            self._is_initialized = True
            logger.info(f"Successfully computed and saved {len(self._embeddings_cache)} theme embeddings")
            
            # Run health checks
            self._run_health_checks()
            
        except Exception as e:
            logger.error(f"Failed to compute theme embeddings: {e}")
            raise
    
    def _save_embeddings_to_disk(self, keywords: List[str], embeddings: np.ndarray):
        """
        Save theme embeddings to disk.
        
        Args:
            keywords: List of keywords corresponding to embeddings
            embeddings: Numpy array of embeddings
        """
        embeddings_file = self._get_embeddings_file_path()
        
        try:
            logger.info(f"Saving theme embeddings to {embeddings_file}")
            
            # Save as .npz file (compressed numpy format)
            np.savez_compressed(
                embeddings_file,
                keywords=np.array(keywords),
                embeddings=embeddings.astype(np.float32)
            )
            
            logger.info(f"Successfully saved theme embeddings to {embeddings_file}")
            
        except Exception as e:
            logger.error(f"Failed to save theme embeddings to disk: {e}")
            raise
    
    def force_recompute_embeddings(self):
        """
        Force recomputation of theme embeddings and save to disk.
        Useful for updating embeddings when themes.json changes.
        """
        logger.info("Forcing recomputation of theme embeddings...")
        
        # Clear cache
        self._embeddings_cache.clear()
        self._is_initialized = False
        
        # Remove existing file
        embeddings_file = self._get_embeddings_file_path()
        if embeddings_file.exists():
            embeddings_file.unlink()
            logger.info(f"Removed existing embeddings file: {embeddings_file}")
        
        # Recompute and save
        self._compute_and_save_embeddings()
    
    def _run_health_checks(self):
        """
        Run health checks on initialized embeddings.
        """
        logger.info("Running theme embedding health checks...")
        
        # Check embedding dimensions
        for keyword, embedding in self._embeddings_cache.items():
            if embedding.shape[0] != self.embedding_dim:
                logger.error(f"Invalid embedding dimension for '{keyword}': {embedding.shape[0]} != {self.embedding_dim}")
                raise ValueError(f"Embedding dimension mismatch for keyword '{keyword}'")
        
        # Check for zero vectors
        zero_count = 0
        for keyword, embedding in self._embeddings_cache.items():
            if np.allclose(embedding, 0):
                zero_count += 1
                logger.warning(f"Zero embedding detected for keyword '{keyword}'")
        
        if zero_count > 0:
            logger.warning(f"Found {zero_count} zero embeddings out of {len(self._embeddings_cache)} total")
        
        # Check embedding norms (should be ~1.0 for normalized embeddings)
        norms = [np.linalg.norm(emb) for emb in self._embeddings_cache.values()]
        mean_norm = np.mean(norms)
        std_norm = np.std(norms)
        
        logger.info(f"Embedding norms - Mean: {mean_norm:.4f}, Std: {std_norm:.4f}")
        
        if mean_norm < 0.9 or mean_norm > 1.1:
            logger.warning(f"Unusual embedding norm mean: {mean_norm:.4f} (expected ~1.0)")
        
        logger.info("Theme embedding health checks completed")
    
    def get_theme_embedding(self, keyword: str) -> Optional[np.ndarray]:
        """
        Get embedding for a specific theme keyword.
        
        Args:
            keyword: The theme keyword to get embedding for
            
        Returns:
            Embedding vector as numpy array, or None if keyword not found
        """
        if not self._is_initialized:
            raise RuntimeError("Theme embeddings not initialized")
        
        return self._embeddings_cache.get(keyword)
    
    def get_all_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Get all theme embeddings.
        
        Returns:
            Dictionary mapping keywords to embeddings
        """
        if not self._is_initialized:
            raise RuntimeError("Theme embeddings not initialized")
        
        return self._embeddings_cache.copy()
    
    def get_theme_keywords(self) -> List[str]:
        """
        Get list of all theme keywords.
        
        Returns:
            List of all theme keywords
        """
        return list(self._embeddings_cache.keys())
    
    def get_themes(self) -> Dict[str, List[str]]:
        """
        Get the original theme mapping.
        
        Returns:
            Dictionary mapping theme names to keyword lists
        """
        return self.themes.copy()
    
    def validate_keyword(self, keyword: str) -> bool:
        """
        Check if a keyword has a valid embedding.
        
        Args:
            keyword: The keyword to validate
            
        Returns:
            True if keyword has valid embedding, False otherwise
        """
        if not self._is_initialized:
            return False
        
        embedding = self._embeddings_cache.get(keyword)
        if embedding is None:
            return False
        
        # Check for zero vector
        if np.allclose(embedding, 0):
            return False
        
        # Check dimension
        if embedding.shape[0] != self.embedding_dim:
            return False
        
        return True
    
    def get_embedding_stats(self) -> Dict[str, any]:
        """
        Get statistics about the embeddings.
        
        Returns:
            Dictionary with embedding statistics
        """
        if not self._is_initialized:
            return {"error": "Embeddings not initialized"}
        
        embeddings = list(self._embeddings_cache.values())
        norms = [np.linalg.norm(emb) for emb in embeddings]
        
        return {
            "model_id": self.model_id,
            "embedding_dim": self.embedding_dim,
            "total_keywords": len(self._embeddings_cache),
            "total_themes": len(self.themes),
            "mean_norm": float(np.mean(norms)),
            "std_norm": float(np.std(norms)),
            "min_norm": float(np.min(norms)),
            "max_norm": float(np.max(norms)),
            "zero_embeddings": sum(1 for emb in embeddings if np.allclose(emb, 0))
        } 