#!/usr/bin/env python3
"""
E2E: Weaviate Health Check Test

This test verifies:
- Weaviate connection and authentication
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
def test_weaviate_health():
    """E2E: Test Weaviate connectivity and basic functionality."""
    load_dotenv('backend/.env.production')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info("🔍 Starting Weaviate Health Check")
    weaviate_url = os.getenv('WEAVIATE_URL')
    weaviate_api_key = os.getenv('WEAVIATE_API_KEY')
    use_weaviate = os.getenv('USE_WEAVIATE', 'false').lower() == 'true'
    logger.info(f"WEAVIATE_URL: {weaviate_url}")
    logger.info(f"USE_WEAVIATE: {use_weaviate}")
    logger.info(f"WEAVIATE_API_KEY set: {bool(weaviate_api_key)}")
    if not use_weaviate:
        pytest.skip("USE_WEAVIATE is not set to 'true', skipping Weaviate tests")
    if not weaviate_api_key:
        pytest.fail("WEAVIATE_API_KEY not found in environment")
    try:
        import weaviate
        logger.info("📡 Testing Weaviate connection...")
        client = weaviate.Client(
            url=weaviate_url,
            auth_client_secret=weaviate.AuthApiKey(weaviate_api_key)
        )
        meta = client.get_meta()
        logger.info(f"✅ Weaviate connection successful! Version: {meta.get('version', 'unknown')}")
        logger.info("📡 Testing basic vector search...")
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("BAAI/bge-large-en-v1.5")
        query = "What do laureates say about the creative process?"
        embedding = model.encode(query, normalize_embeddings=True).tolist()
        result = client.query.get("SpeechChunk", [
            "chunk_id", "text", "laureate", "year_awarded"
        ]).with_near_vector({
            "vector": embedding,
            "certainty": 0.2
        }).with_additional(["score"]).with_limit(3).do()
        chunks = result["data"]["Get"]["SpeechChunk"]
        logger.info(f"✅ Query successful! Found {len(chunks)} chunks")
        assert len(chunks) > 0, "No chunks returned - check if data is loaded in Weaviate"
        logger.info("🎉 Weaviate Health Check PASSED!")
    except Exception as e:
        logger.error(f"❌ Weaviate Health Check FAILED: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        pytest.fail(f"Weaviate Health Check failed: {e}") 