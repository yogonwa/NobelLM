"""
ThemeReformulator: Utility for mapping user queries to canonical themes and expanded keyword sets.

This module loads a theme-to-keywords mapping, lemmatizes both the keywords and user queries using spaCy,
and provides methods to extract canonical themes and expand queries for robust thematic search.

Enhanced in Phase 3A with similarity-based ranked expansion for improved retrieval quality.
"""
import json
import re
import logging
import spacy
import numpy as np
from pathlib import Path
from typing import Set, List, Tuple, Optional
from config.theme_embeddings import ThemeEmbeddings
from config.theme_similarity import compute_theme_similarities
from rag.cache import get_model

logger = logging.getLogger(__name__)

class ThemeReformulator:
    """
    Maps user queries to canonical themes and expanded keyword sets using lemmatization.
    Enhanced with similarity-based ranked expansion for improved retrieval quality.
    Use this for robust thematic search and query normalization.
    """
    def __init__(self, theme_file: str = "themes.json", model_id: str = "bge-large"):
        """
        Initialize the ThemeReformulator.
        Args:
            theme_file: Path to the JSON file mapping themes to keywords.
            model_id: Model identifier for theme embeddings (default: "bge-large").
        Loads and lemmatizes all keywords for robust matching.
        """
        self.nlp = spacy.load("en_core_web_sm")
        self.model_id = model_id

        # Load theme → keywords
        theme_path = Path(theme_file)
        if not theme_path.exists():
            raise FileNotFoundError(f"Theme file not found: {theme_file}")
        with theme_path.open("r", encoding="utf-8") as f:
            self.theme_map_raw = json.load(f)

        # Lemmatize all keywords into normalized map
        self.theme_map = {}
        self.keyword_to_themes = {}

        for theme, keywords in self.theme_map_raw.items():
            lemmatized_keywords = {self.lemmatize_word(kw) for kw in keywords}
            # Store both original and lemmatized keywords
            all_keywords = set(keywords) | lemmatized_keywords
            self.theme_map[theme] = list(all_keywords)
            for lemma_kw in lemmatized_keywords:
                self.keyword_to_themes.setdefault(lemma_kw, set()).add(theme)
            for orig_kw in keywords:
                self.keyword_to_themes.setdefault(self.lemmatize_word(orig_kw), set()).add(theme)

        # Initialize theme embeddings (lazy loading)
        self._theme_embeddings = None
        self._embedding_model = None

    def _get_theme_embeddings(self) -> ThemeEmbeddings:
        """Get theme embeddings instance (lazy loading)."""
        if self._theme_embeddings is None:
            self._theme_embeddings = ThemeEmbeddings(self.model_id)
        return self._theme_embeddings

    def _get_embedding_model(self):
        """Get embedding model instance (lazy loading)."""
        if self._embedding_model is None:
            self._embedding_model = get_model(self.model_id)
        return self._embedding_model

    def lemmatize_word(self, word: str) -> str:
        """
        Lemmatize a single word using spaCy.
        Args:
            word: The word to lemmatize.
        Returns:
            The lemmatized form of the word.
        """
        return self.nlp(word.lower())[0].lemma_

    def lemmatize_query(self, query: str) -> Set[str]:
        """
        Lemmatize all tokens in a user query.
        Args:
            query: The user query string.
        Returns:
            Set of lemmatized tokens.
        """
        return {token.lemma_ for token in self.nlp(query.lower())}

    def extract_theme_keywords(self, query: str) -> Set[str]:
        """
        Lemmatize user query and match against lemmatized keywords.
        Args:
            query: The user query string.
        Returns:
            Set of matched lemmatized keywords present in the query.
        """
        lemmatized_tokens = self.lemmatize_query(query)
        return {
            kw for kw in self.keyword_to_themes
            if kw in lemmatized_tokens
        }

    def expand_query_terms(self, query: str) -> Set[str]:
        """
        Return full set of keywords from any matched themes.
        Args:
            query: The user query string.
        Returns:
            Set of all lemmatized keywords from matched themes.
        """
        matched_keywords = self.extract_theme_keywords(query)
        expanded = set()
        for kw in matched_keywords:
            for theme in self.keyword_to_themes[kw]:
                expanded.update(self.theme_map[theme])
        return expanded

    def extract_themes(self, query: str) -> Set[str]:
        """
        Extract canonical themes from a query by matching against theme keywords.
        Args:
            query: The user query string.
        Returns:
            Set of matched canonical theme names.
        """
        matched_keywords = self.extract_theme_keywords(query)
        themes = set()
        for kw in matched_keywords:
            themes.update(self.keyword_to_themes[kw])
        return themes

    # === Phase 3A Enhanced Methods ===

    def expand_query_terms_ranked(
        self, 
        query: str, 
        similarity_threshold: float = 0.3,
        max_results: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """
        Expand query terms using similarity-based ranking and quality filtering.
        
        This method provides intelligent semantic expansion by:
        1. Extracting theme keywords from the query
        2. Computing similarity between query and theme keywords
        3. Ranking and pruning expansions based on similarity threshold
        4. Returning ranked list of (keyword, score) tuples
        
        Args:
            query: The user query string
            similarity_threshold: Minimum similarity score to include (default: 0.3)
            max_results: Maximum number of results to return (default: None, return all)
            
        Returns:
            List of (keyword, score) tuples, sorted by score descending
            
        Raises:
            ValueError: If similarity computation fails
            RuntimeError: If theme embeddings are not available
        """
        logger.info(f"Starting ranked expansion for query: '{query}' (threshold: {similarity_threshold})")
        
        try:
            # Get theme-focused embedding for the query
            query_embedding = self._get_theme_focused_embedding(query)
            
            # Compute similarities with all theme keywords
            similarities = compute_theme_similarities(
                query_embedding=query_embedding,
                model_id=self.model_id,
                similarity_threshold=similarity_threshold,
                max_results=max_results
            )
            
            # Convert to ranked list
            ranked_expansions = list(similarities.items())
            
            # Log expansion results
            logger.info(
                f"Ranked expansion completed",
                extra={
                    "query": query,
                    "threshold": similarity_threshold,
                    "total_expansions": len(ranked_expansions),
                    "top_expansions": ranked_expansions[:3] if ranked_expansions else []
                }
            )
            
            return ranked_expansions
            
        except Exception as e:
            logger.error(f"Ranked expansion failed for query '{query}': {e}")
            # Fallback to original expansion method
            logger.info(f"Falling back to original expansion method")
            original_expansions = self.expand_query_terms(query)
            return [(kw, 1.0) for kw in original_expansions]

    def _get_theme_focused_embedding(self, query: str) -> np.ndarray:
        """
        Get theme-focused embedding for a query using hybrid keyword extraction.
        
        This method implements intelligent embedding by:
        1. First trying to extract theme keywords from the query
        2. If theme keywords found: embed only those keywords for focused similarity
        3. If no theme keywords: use preprocessed query (remove stopwords)
        4. Fallback to full query if preprocessing fails
        
        Args:
            query: The user query string
            
        Returns:
            Normalized query embedding as numpy array
        """
        # Step 1: Try to extract theme keywords
        theme_keywords = self.extract_theme_keywords(query)
        
        if theme_keywords:
            # Use theme keywords for focused embedding
            logger.debug(f"Using theme keywords for embedding: {theme_keywords}")
            text_to_embed = " ".join(theme_keywords)
        else:
            # Step 2: Use preprocessed query
            preprocessed_query = self._preprocess_query_for_themes(query)
            if preprocessed_query:
                logger.debug(f"Using preprocessed query for embedding: '{preprocessed_query}'")
                text_to_embed = preprocessed_query
            else:
                # Step 3: Fallback to full query
                logger.debug(f"Using full query for embedding: '{query}'")
                text_to_embed = query
        
        # Get embedding
        model = self._get_embedding_model()
        embedding = model.encode([text_to_embed], normalize_embeddings=True)[0]
        
        logger.debug(f"Generated embedding with shape: {embedding.shape}")
        return embedding

    def _preprocess_query_for_themes(self, query: str) -> str:
        """
        Preprocess query for theme embedding by removing stopwords and non-thematic content.
        
        Args:
            query: The user query string
            
        Returns:
            Preprocessed query string, or empty string if preprocessing fails
        """
        try:
            # Parse query with spaCy
            doc = self.nlp(query.lower())
            
            # Extract meaningful tokens (not stopwords, not punctuation)
            meaningful_tokens = [
                token.text for token in doc
                if not token.is_stop and not token.is_punct and not token.is_space
            ]
            
            # Filter out very short tokens
            meaningful_tokens = [token for token in meaningful_tokens if len(token) > 2]
            
            if meaningful_tokens:
                preprocessed = " ".join(meaningful_tokens)
                logger.debug(f"Preprocessed query: '{query}' -> '{preprocessed}'")
                return preprocessed
            else:
                logger.debug(f"Preprocessing resulted in empty query for: '{query}'")
                return ""
                
        except Exception as e:
            logger.warning(f"Query preprocessing failed for '{query}': {e}")
            return ""

    def _rank_and_prune_expansions(
        self, 
        expansions: Set[str], 
        similarities: dict, 
        threshold: float
    ) -> List[Tuple[str, float]]:
        """
        Rank and prune expansions based on similarity scores.
        
        Args:
            expansions: Set of expansion keywords
            similarities: Dictionary mapping keywords to similarity scores
            threshold: Minimum similarity threshold
            
        Returns:
            List of (keyword, score) tuples, sorted by score descending
        """
        # Filter expansions by threshold
        filtered_expansions = [
            (kw, score) for kw, score in similarities.items()
            if kw in expansions and score >= threshold
        ]
        
        # Sort by score descending
        ranked_expansions = sorted(filtered_expansions, key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Ranked and pruned {len(expansions)} expansions to {len(ranked_expansions)} above threshold {threshold}")
        
        return ranked_expansions

    def get_expansion_stats(self, query: str) -> dict:
        """
        Get statistics about query expansion for debugging and monitoring.
        
        Args:
            query: The user query string
            
        Returns:
            Dictionary with expansion statistics
        """
        try:
            # Original expansion
            original_expansions = self.expand_query_terms(query)
            
            # Ranked expansion
            ranked_expansions = self.expand_query_terms_ranked(query, similarity_threshold=0.3)
            
            # Theme keywords
            theme_keywords = self.extract_theme_keywords(query)
            
            # Preprocessed query
            preprocessed = self._preprocess_query_for_themes(query)
            
            return {
                "query": query,
                "original_expansion_count": len(original_expansions),
                "ranked_expansion_count": len(ranked_expansions),
                "theme_keywords_found": len(theme_keywords),
                "theme_keywords": list(theme_keywords),
                "preprocessed_query": preprocessed,
                "used_preprocessing": bool(preprocessed and not theme_keywords),
                "top_ranked_expansions": ranked_expansions[:5] if ranked_expansions else []
            }
            
        except Exception as e:
            logger.error(f"Failed to get expansion stats for query '{query}': {e}")
            return {"error": str(e)} 