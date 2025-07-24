#!/usr/bin/env python3
"""
E2E: Qdrant RAG Pipeline Integration Test

This test verifies the complete RAG pipeline with Qdrant as the vector backend:
- Environment configuration loading
- Query routing and intent classification
- Qdrant retrieval and chunk processing
- LLM prompt building and generation
- Answer compilation and source citation

This is the main end-to-end integration test for the Qdrant backend.
"""
import os
import sys
import logging
import pytest
from dotenv import load_dotenv

@pytest.mark.e2e
def test_qdrant_e2e():
    """E2E: Run end-to-end integration test with Qdrant backend."""
    load_dotenv('.env')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    query = "What do laureates say about the creative process?"
    logger.info("🚀 Starting Qdrant E2E Integration Test")
    logger.info(f"Query: {query}")
    logger.info(f"QDRANT_URL: {os.getenv('QDRANT_URL', 'NOT SET')}")
    logger.info(f"QDRANT_API_KEY set: {bool(os.getenv('QDRANT_API_KEY'))}")
    try:
        from rag.query_engine import answer_query
        logger.info("📡 Calling answer_query() with Qdrant backend...")
        result = answer_query(
            query_string=query,
            model_id="bge-large",
            score_threshold=0.2,
            min_return=3,
            max_return=10
        )
        logger.info("✅ Query completed successfully!")
        logger.info(f"Answer type: {result.get('answer_type', 'Unknown')}")
        logger.info(f"Number of sources: {len(result.get('sources', []))}")
        assert result.get('answer_type') in ('rag', 'metadata'), "Unexpected answer_type returned"
        if result.get('answer_type') == 'rag':
            logger.info("📝 Generated Answer:")
            logger.info(result.get('answer', 'No answer generated'))
            logger.info("📚 Sources:")
            for i, source in enumerate(result.get('sources', [])[:3]):
                logger.info(f"  {i+1}. {source.get('laureate', 'Unknown')} ({source.get('year_awarded', '?')})")
                logger.info(f"     Score: {source.get('score', 0):.3f}")
                logger.info(f"     Text: {source.get('text', '')[:100]}...")
            assert len(result.get('sources', [])) > 0, "No sources returned for RAG answer"
        elif result.get('answer_type') == 'metadata':
            logger.info("📊 Metadata Answer:")
            logger.info(result.get('answer', 'No metadata answer'))
        logger.info("🎉 Qdrant E2E Integration Test PASSED!")
    except Exception as e:
        logger.error(f"❌ Qdrant E2E Integration Test FAILED: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        pytest.fail(f"Qdrant E2E Integration Test failed: {e}") 