"""
Test script for the NobelLM Query Engine.

Demonstrates the canonical answer_query() function with various query types and model configurations.
"""
import logging
from rag.query_engine import answer_query, build_prompt

def source_to_chunk(source):
    # Use the text_snippet as the 'text' field for prompt reconstruction
    return {**source, "text": source["text_snippet"]}

def main():
    """Run a series of test queries demonstrating the RAG pipeline."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Test queries
    queries = [
        # Factual query (should try metadata first)
        "When did Toni Morrison win the Nobel Prize?",
        # Thematic query
        "What are common themes in Nobel lectures?",
        # Hybrid query (thematic + laureate)
        "What did Gabriel García Márquez say about solitude?",
        # Generative query
        "Write a speech in the style of Bob Dylan.",
    ]

    # Test with default model
    logger.info("\n=== Testing with default model ===")
    for q in queries:
        logger.info(f"\nQuery: {q}")
        response = answer_query(q)
        logger.info(f"Answer type: {response['answer_type']}")
        logger.info(f"Answer: {response['answer']}")
        if response['sources']:
            logger.info(f"Found {len(response['sources'])} sources")
            for s in response['sources'][:2]:  # Show first 2 sources
                logger.info(f"- {s['laureate']} ({s['year_awarded']}): {s['text_snippet']}")

    # Test with MiniLM
    logger.info("\n=== Testing with MiniLM ===")
    for q in queries:
        logger.info(f"\nQuery: {q}")
        response = answer_query(q, model_id="miniLM")
        logger.info(f"Answer type: {response['answer_type']}")
        logger.info(f"Answer: {response['answer']}")
        if response['sources']:
            logger.info(f"Found {len(response['sources'])} sources")
            for s in response['sources'][:2]:  # Show first 2 sources
                logger.info(f"- {s['laureate']} ({s['year_awarded']}): {s['text_snippet']}")

if __name__ == "__main__":
    main() 