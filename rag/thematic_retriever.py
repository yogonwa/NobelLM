"""
ThematicRetriever: Modular utility for thematic query expansion, embedding, and retrieval.

This class encapsulates the logic for expanding user queries into canonical theme terms,
embedding the reformulated query, and retrieving top-k relevant chunks from the vector store.
It is designed for modularity, testability, and easy integration into the RAG pipeline.

Enhanced in Phase 3B with weighted retrieval using similarity-based ranked expansion.
"""
import logging
import math
from config.theme_reformulator import ThemeReformulator
from typing import List, Dict, Any, Optional, Tuple
from .utils import filter_top_chunks

logger = logging.getLogger(__name__)

class ThematicRetriever:
    """
    A retriever that expands thematic queries into multiple terms and merges results.
    Uses a base retriever (e.g., ModeAwareRetriever) for the actual retrieval.
    
    Enhanced with weighted retrieval using similarity-based ranked expansion.
    """

    def __init__(self, model_id: Optional[str] = None, similarity_threshold: float = 0.3):
        """
        Initialize the thematic retriever.

        Args:
            model_id: Optional model identifier to use for the base retriever.
                     If None, uses DEFAULT_MODEL_ID from model_config.
            similarity_threshold: Minimum similarity score for term expansion (default: 0.3)
        """
        from .query_engine import get_mode_aware_retriever
        self.base_retriever = get_mode_aware_retriever(model_id)
        self.similarity_threshold = similarity_threshold
        self.reformulator = ThemeReformulator("config/themes.json", model_id=model_id or "bge-large")

    def retrieve(
        self,
        query: str,
        top_k: int = 15,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.2,
        min_return: int = 5,
        max_return: int = 12,
        use_weighted_retrieval: bool = True
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
            use_weighted_retrieval: Whether to use weighted retrieval with ranked terms (default: True)

        Returns:
            List of unique chunks, sorted by score, filtered by score threshold
        """
        if use_weighted_retrieval:
            # Use enhanced weighted retrieval with ranked terms
            return self._weighted_retrieval(
                query=query,
                top_k=top_k,
                filters=filters,
                score_threshold=score_threshold,
                min_return=min_return,
                max_return=max_return
            )
        else:
            # Use legacy expansion method for backward compatibility
            return self._legacy_retrieval(
                query=query,
                top_k=top_k,
                filters=filters,
                score_threshold=score_threshold,
                min_return=min_return,
                max_return=max_return
            )

    def _weighted_retrieval(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]],
        score_threshold: float,
        min_return: int,
        max_return: int
    ) -> List[Dict[str, Any]]:
        """
        Perform weighted retrieval using similarity-based ranked expansion.
        
        Args:
            query: The thematic query to expand and retrieve for
            top_k: Number of chunks to retrieve per term
            filters: Optional metadata filters to apply
            score_threshold: Minimum similarity score
            min_return: Minimum number of chunks to return
            max_return: Maximum number of chunks to return
            
        Returns:
            List of unique chunks with weighted scores
        """
        # Get ranked expansion terms with similarity scores
        ranked_terms = self._expand_thematic_query_ranked(query)
        logger.info(f"[ThematicRetriever] Weighted retrieval for query '{query}' with {len(ranked_terms)} ranked terms")
        
        if not ranked_terms:
            logger.warning(f"[ThematicRetriever] No ranked terms found for query: {query}")
            return []
        
        # Retrieve chunks for each ranked term with weighted scoring
        all_chunks = []
        for term, similarity_score in ranked_terms:
            chunks = self.base_retriever.retrieve(
                term,
                top_k=top_k,
                filters=filters,
                score_threshold=score_threshold,
                min_return=min_return,
                max_return=max_return
            )
            
            # Apply exponential weight scaling to chunk scores
            weighted_chunks = self._apply_term_weights(chunks, similarity_score, term)
            all_chunks.extend(weighted_chunks)
            
            logger.debug(f"[ThematicRetriever] Retrieved {len(chunks)} chunks for term '{term}' (weight: {similarity_score:.3f})")
        
        # Merge weighted chunks and apply final filtering
        unique_chunks = self._merge_weighted_chunks(all_chunks)
        logger.info(f"[ThematicRetriever] Found {len(unique_chunks)} unique chunks after weighted merging")
        
        # Apply final filtering to ensure consistent output
        filtered_chunks = filter_top_chunks(
            unique_chunks,
            score_threshold=score_threshold,
            min_return=min_return,
            max_return=max_return
        )
        logger.info(f"[ThematicRetriever] Final filtered chunks: {len(filtered_chunks)}")
        
        return filtered_chunks

    def _legacy_retrieval(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]],
        score_threshold: float,
        min_return: int,
        max_return: int
    ) -> List[Dict[str, Any]]:
        """
        Legacy retrieval method for backward compatibility.
        
        Args:
            query: The thematic query to expand and retrieve for
            top_k: Number of chunks to retrieve per term
            filters: Optional metadata filters to apply
            score_threshold: Minimum similarity score
            min_return: Minimum number of chunks to return
            max_return: Maximum number of chunks to return
            
        Returns:
            List of unique chunks, sorted by score
        """
        # Expand query into thematic terms using legacy method
        expanded_terms = self._expand_thematic_query_legacy(query)
        logger.info(f"[ThematicRetriever] Legacy retrieval for query '{query}' with terms: {expanded_terms}")

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

    def _expand_thematic_query_ranked(self, query: str) -> List[Tuple[str, float]]:
        """
        Expand a thematic query into ranked terms using similarity-based expansion.
        
        Args:
            query: The thematic query to expand
            
        Returns:
            List of (term, similarity_score) tuples, sorted by score descending
        """
        try:
            # Use enhanced ThemeReformulator for ranked expansion
            ranked_terms = self.reformulator.expand_query_terms_ranked(
                query=query,
                similarity_threshold=self.similarity_threshold
            )
            
            if ranked_terms:
                logger.info(f"[ThemeReformulator] Ranked expansion: {ranked_terms[:3]}... (total: {len(ranked_terms)})")
                return ranked_terms
            else:
                # Fallback: use original query if no ranked terms found
                logger.warning(f"[ThemeReformulator] No ranked terms found for query: {query}")
                return [(query, 1.0)]
                
        except Exception as e:
            logger.error(f"[ThemeReformulator] Error in ranked expansion for query '{query}': {e}")
            # Fallback to original query
            return [(query, 1.0)]

    def _expand_thematic_query_legacy(self, query: str) -> List[str]:
        """
        Legacy expansion method for backward compatibility.
        
        Args:
            query: The thematic query to expand
            
        Returns:
            List of expanded query terms
        """
        try:
            # Use ThemeReformulator for semantic expansion with correct path
            expanded_keywords = self.reformulator.expand_query_terms(query)
            
            if expanded_keywords:
                # Convert set to list and filter out very short terms
                terms = [kw for kw in expanded_keywords if len(kw) > 2]
                logger.info(f"[ThemeReformulator] Legacy expansion: {list(expanded_keywords)}")
                return terms if terms else [query]
            else:
                # Fallback: use original query if no theme keywords found
                logger.warning(f"[ThemeReformulator] No theme keywords found for query: {query}")
                return [query]
                
        except Exception as e:
            logger.error(f"[ThemeReformulator] Error in legacy expansion for query '{query}': {e}")
            # Fallback to original query
            return [query]

    def _expand_thematic_query(self, query: str) -> List[str]:
        """
        Backward compatibility method - delegates to legacy expansion.
        
        Args:
            query: The thematic query to expand
            
        Returns:
            List of expanded query terms
        """
        return self._expand_thematic_query_legacy(query)

    def _apply_term_weights(self, chunks: List[Dict[str, Any]], term_weight: float, source_term: str) -> List[Dict[str, Any]]:
        """
        Apply exponential weight scaling to chunk scores based on term similarity.
        
        Args:
            chunks: List of chunks to weight
            term_weight: Similarity score for the source term (0.0 to 1.0)
            source_term: The term that generated these chunks
            
        Returns:
            List of chunks with boosted scores
        """
        weighted_chunks = []
        
        for chunk in chunks:
            # Create a copy to avoid modifying the original
            weighted_chunk = chunk.copy()
            
            # Apply exponential weight scaling: exp(2 * normalized_score)
            # This gives higher weight to more similar terms
            boost_factor = math.exp(2 * term_weight)
            weighted_chunk["score"] = chunk["score"] * boost_factor
            
            # Add source term attribution for debugging
            weighted_chunk["source_term"] = source_term
            weighted_chunk["term_weight"] = term_weight
            weighted_chunk["boost_factor"] = boost_factor
            
            weighted_chunks.append(weighted_chunk)
        
        if chunks:
            logger.debug(f"[ThematicRetriever] Applied weight {term_weight:.3f} (boost: {boost_factor:.3f}) to {len(chunks)} chunks from term '{source_term}'")
        else:
            logger.debug(f"[ThematicRetriever] No chunks to apply weight {term_weight:.3f} for term '{source_term}'")
        
        return weighted_chunks

    def _merge_weighted_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge and deduplicate weighted chunks, keeping the highest weighted score for each unique chunk.
        When scores are equal, prefer lecture chunks over ceremony speeches.
        
        Args:
            chunks: List of weighted chunks to merge
            
        Returns:
            List of unique chunks, sorted by weighted score (and source_type for equal scores)
        """
        # Use chunk_id as key for deduplication
        unique_chunks = {}
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id")
            if not chunk_id:
                continue
                
            # Keep the chunk with the highest weighted score
            if chunk_id not in unique_chunks or chunk["score"] > unique_chunks[chunk_id]["score"]:
                unique_chunks[chunk_id] = chunk

        # Sort by weighted score descending, then prefer lecture chunks for equal scores
        def sort_key(chunk):
            # Primary sort by weighted score (descending)
            score = -chunk["score"]  # Negative for descending sort
            # Secondary sort: prefer lecture chunks (0) over ceremony speeches (1)
            source_type = 1 if chunk.get("source_type") == "ceremony_speech" else 0
            return (score, source_type)

        sorted_chunks = sorted(unique_chunks.values(), key=sort_key)
        
        # Log merge statistics
        total_source_terms = len(set(chunk.get("source_term", "unknown") for chunk in sorted_chunks))
        avg_weight = sum(chunk.get("term_weight", 0) for chunk in sorted_chunks) / len(sorted_chunks) if sorted_chunks else 0
        
        logger.info(f"[ThematicRetriever] Merged {len(chunks)} chunks into {len(sorted_chunks)} unique chunks")
        logger.debug(f"[ThematicRetriever] Merge stats: {total_source_terms} source terms, avg weight: {avg_weight:.3f}")
        
        return sorted_chunks

    def _merge_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Legacy merge method for backward compatibility.
        
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