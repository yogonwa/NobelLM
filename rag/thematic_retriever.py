"""
ThematicRetriever: Modular utility for thematic query expansion, embedding, and retrieval.

This class encapsulates the logic for expanding user queries into canonical theme terms,
embedding the reformulated query, and retrieving top-k relevant chunks from the vector store.
It is designed for modularity, testability, and easy integration into the RAG pipeline.
"""
import logging
from config.theme_reformulator import ThemeReformulator
from typing import List, Dict, Any, Optional
from .utils import filter_top_chunks

logger = logging.getLogger(__name__)

class ThematicRetriever:
    """
    A retriever that expands thematic queries into multiple terms and merges results.
    Uses a base retriever (e.g., ModeAwareRetriever) for the actual retrieval.
    """

    def __init__(self, model_id: Optional[str] = None):
        """
        Initialize the thematic retriever.

        Args:
            model_id: Optional model identifier to use for the base retriever.
                     If None, uses DEFAULT_MODEL_ID from model_config.
        """
        from .query_engine import get_mode_aware_retriever
        self.base_retriever = get_mode_aware_retriever(model_id)

    def retrieve(
        self,
        query: str,
        top_k: int = 15,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.2,
        min_return: int = 5,
        max_return: int = 12
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks for a thematic query by expanding it into multiple terms.

        Args:
            query: The thematic query to expand and retrieve for
            top_k: Number of chunks to retrieve per term (default: 15)
            filters: Optional metadata filters to apply
            score_threshold: Minimum similarity score (default: 0.2)
            min_return: Minimum number of chunks to return (default: 5)
            max_return: Maximum number of chunks to return (default: 12)

        Returns:
            List of unique chunks, sorted by score, filtered by score threshold
        """
        # Expand query into thematic terms
        expanded_terms = self._expand_thematic_query(query)
        logger.info(f"[ThematicRetriever] Expanded query '{query}' into terms: {expanded_terms}")

        # Retrieve chunks for each term with consistent filtering
        all_chunks = []
        for term in expanded_terms:
            chunks = self.base_retriever.retrieve(
                term,
                top_k=top_k,
                filters=filters,
                score_threshold=score_threshold,
                min_return=min_return,
                max_return=max_return
            )
            all_chunks.extend(chunks)

        # Merge and deduplicate chunks
        unique_chunks = self._merge_chunks(all_chunks)
        logger.info(f"[ThematicRetriever] Found {len(unique_chunks)} unique chunks after merging")

        # Apply final filtering to ensure consistent output
        filtered_chunks = filter_top_chunks(
            unique_chunks,
            score_threshold=score_threshold,
            min_return=min_return,
            max_return=max_return
        )
        logger.info(f"[ThematicRetriever] Final filtered chunks: {len(filtered_chunks)}")

        return filtered_chunks

    def _expand_thematic_query(self, query: str) -> List[str]:
        """
        Expand a thematic query into multiple related terms using ThemeReformulator.
        This provides semantic expansion based on theme keywords rather than naive word splitting.

        Args:
            query: The thematic query to expand

        Returns:
            List of expanded query terms
        """
        try:
            # Use ThemeReformulator for semantic expansion with correct path
            reformulator = ThemeReformulator("config/themes.json")
            expanded_keywords = reformulator.expand_query_terms(query)
            
            if expanded_keywords:
                # Convert set to list and filter out very short terms
                terms = [kw for kw in expanded_keywords if len(kw) > 2]
                logger.info(f"[ThemeReformulator] Expanded keywords: {list(expanded_keywords)}")
                return terms if terms else [query]
            else:
                # Fallback: use original query if no theme keywords found
                logger.warning(f"[ThemeReformulator] No theme keywords found for query: {query}")
                return [query]
                
        except Exception as e:
            logger.error(f"[ThemeReformulator] Error expanding query '{query}': {e}")
            # Fallback to original query
            return [query]

    def _merge_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge and deduplicate chunks, keeping the highest score for each unique chunk.
        When scores are equal, prefer lecture chunks over ceremony speeches.

        Args:
            chunks: List of chunks to merge

        Returns:
            List of unique chunks, sorted by score (and source_type for equal scores)
        """
        # Use chunk_id as key for deduplication
        unique_chunks = {}
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id")
            if not chunk_id:
                continue
            if chunk_id not in unique_chunks or chunk["score"] > unique_chunks[chunk_id]["score"]:
                unique_chunks[chunk_id] = chunk

        # Sort by score descending, then prefer lecture chunks for equal scores
        def sort_key(chunk):
            # Primary sort by score (descending)
            score = -chunk["score"]  # Negative for descending sort
            # Secondary sort: prefer lecture chunks (0) over ceremony speeches (1)
            source_type = 1 if chunk.get("source_type") == "ceremony_speech" else 0
            return (score, source_type)

        return sorted(unique_chunks.values(), key=sort_key) 