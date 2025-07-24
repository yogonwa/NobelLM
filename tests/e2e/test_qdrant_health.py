#!/usr/bin/env python3
"""
E2E: Qdrant Health Check Test

This test verifies:
- Qdrant connection and authentication
- Basic vector search functionality
- Data availability and quality
- Environment configuration

Use this for quick health checks and CI/CD validation.
"""
import os
import sys
import logging
import pytest
from dotenv import load_dotenv

@pytest.mark.e2e
def test_qdrant_health():
    """E2E: Test Qdrant connectivity and basic functionality."""
    load_dotenv('.env')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info("🔍 Starting Qdrant Health Check")
    qdrant_url = os.getenv('QDRANT_URL')
    qdrant_api_key = os.getenv('QDRANT_API_KEY')
    logger.info(f"QDRANT_URL: {qdrant_url}")
    logger.info(f"QDRANT_API_KEY set: {bool(qdrant_api_key)}")
    if not qdrant_url or not qdrant_api_key:
        pytest.fail("QDRANT_URL and QDRANT_API_KEY must be set in the environment")
    try:
        from qdrant_client import QdrantClient
        logger.info("📡 Testing Qdrant connection...")
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        collections = client.get_collections()
        logger.info(f"✅ Qdrant connection successful! Collections: {collections}")
        logger.info("📡 Testing basic vector search...")
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("BAAI/bge-large-en-v1.5")
        query = "What do laureates say about the creative process?"
        embedding = model.encode(query, normalize_embeddings=True).tolist()
        results = client.search(
            collection_name="nobellm_bge_large",
            query_vector=embedding,
            limit=3,
            with_payload=True
        )
        logger.info(f"✅ Query successful! Found {len(results)} results")
        assert len(results) > 0, "No results returned - check if data is loaded in Qdrant"
        logger.info("🎉 Qdrant Health Check PASSED!")
    except Exception as e:
        logger.error(f"❌ Qdrant Health Check FAILED: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        pytest.fail(f"Qdrant Health Check failed: {e}") 