"""
ThematicRetriever: Modular utility for thematic query expansion, embedding, and retrieval.

This class encapsulates the logic for expanding user queries into canonical theme terms,
embedding the reformulated query, and retrieving top-k relevant chunks from the vector store.
It is designed for modularity, testability, and easy integration into the RAG pipeline.
"""
import logging
from config.theme_reformulator import ThemeReformulator
from typing import List, Dict

logger = logging.getLogger(__name__)

class ThematicRetriever:
    """
    Encapsulates thematic query expansion, embedding, and retrieval logic.
    Use this class to handle all thematic search workflows in a modular, testable way.
    """
    def __init__(self, retriever, theme_file="config/themes.json"):
        """
        Initialize the ThematicRetriever.
        Args:
            retriever: An object with a retrieve(query, top_k, filters) method (BaseRetriever).
            theme_file: Path to the JSON file mapping themes to keywords.
        """
        self.reformulator = ThemeReformulator(theme_file)
        self.retriever = retriever

    def retrieve(self, user_query: str, top_k: int = 15, filters=None) -> List[Dict]:
        """
        Reformulate the query using theme expansion, and retrieve top-k chunks for each term.
        Args:
            user_query: The original user query string.
            top_k: Number of chunks to retrieve (default 15 for thematic search).
            filters: Optional dict of metadata filters (e.g., laureate name)
        Returns:
            List of retrieved chunk dicts.
        """
        terms = self.reformulator.expand_query_terms(user_query)
        logger.info(f"[RAG][ShapeCheck] Expanded query terms: {terms}")
        all_results = []
        for term in terms:
            chunks = self.retriever.retrieve(term, top_k, filters=filters)
            logger.info(f"[RAG][Thematic] Retrieved {len(chunks)} chunks for term '{term}'")
            logger.info(f"[RAG][Thematic] Chunk IDs for '{term}': {[c.get('chunk_id') for c in chunks]}")
            logger.info(f"[RAG][Thematic] Scores for '{term}': {[c.get('score') for c in chunks]}")
            all_results.extend(chunks)
        # Deduplicate by chunk_id
        unique_chunks = {}
        for c in all_results:
            cid = c.get('chunk_id')
            if cid and (cid not in unique_chunks or c['score'] > unique_chunks[cid]['score']):
                unique_chunks[cid] = c
        logger.info(f"[RAG][Thematic] Total unique chunks after aggregation: {len(unique_chunks)}")
        logger.info(f"[RAG][Thematic] Unique chunk IDs: {list(unique_chunks.keys())}")
        logger.info(f"[RAG][Thematic] Unique chunk scores: {[c.get('score') for c in unique_chunks.values()]}")
        return list(unique_chunks.values()) 