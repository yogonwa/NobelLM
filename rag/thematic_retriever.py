"""
ThematicRetriever: Modular utility for thematic query expansion, embedding, and retrieval.

This class encapsulates the logic for expanding user queries into canonical theme terms,
embedding the reformulated query, and retrieving top-k relevant chunks from the vector store.
It is designed for modularity, testability, and easy integration into the RAG pipeline.
"""
import logging
from config.theme_reformulator import ThemeReformulator

logger = logging.getLogger(__name__)

class ThematicRetriever:
    """
    Encapsulates thematic query expansion, embedding, and retrieval logic.
    Use this class to handle all thematic search workflows in a modular, testable way.
    """
    def __init__(self, embedder, retriever, theme_file="config/themes.json"):
        """
        Initialize the ThematicRetriever.
        Args:
            embedder: An object with a get_embedding(text) method (e.g., wraps MiniLM or OpenAI embedder).
            retriever: An object with a get_top_k_chunks(embedding, top_k, threshold=None) method.
            theme_file: Path to the JSON file mapping themes to keywords.
        """
        self.reformulator = ThemeReformulator(theme_file)
        self.embedder = embedder
        self.retriever = retriever

    def retrieve(self, user_query: str, top_k: int = 15, filters=None):
        """
        Reformulate the query using theme expansion, embed, and retrieve top-k chunks.
        Logs both the original and reformulated query string for transparency.
        Args:
            user_query: The original user query string.
            top_k: Number of chunks to retrieve (default 15 for thematic search).
            filters: Optional dict of metadata filters (e.g., laureate name)
        Returns:
            List of retrieved chunk dicts.
        """
        # Expand the query to all related theme terms
        terms = self.reformulator.expand_query_terms(user_query)
        if terms:
            search_string = " ".join(terms)
        else:
            search_string = user_query  # fallback to original query
        # Log both the original and reformulated query
        logger.info(f"ThematicRetriever: user_query='{user_query}' | reformulated='{search_string}'")
        # Embed and retrieve
        query_embedding = self.embedder.get_embedding(search_string)
        chunks = self.retriever.get_top_k_chunks(query_embedding, top_k=top_k, threshold=None, filters=filters)
        return chunks 