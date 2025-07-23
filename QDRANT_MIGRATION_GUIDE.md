# Qdrant Migration Guide for NobelLM

This guide provides a step-by-step process to migrate the NobelLM project from Weaviate to Qdrant as the vector database backend. It covers code changes, configuration, testing, and documentation updates.

---

## 1. Preparation

- **Inventory Weaviate Usage:**
  - Review all files that reference Weaviate: `rag/retriever_weaviate.py`, `rag/query_weaviate.py`, `rag/retriever.py`, `backend/app/config.py`, `backend/app/deps.py`, `backend/app/main.py`, `weaviate_search.py`, `tests/e2e/test_weaviate_health.py`, `tests/e2e/test_weaviate_e2e.py`, and documentation files.
- **Backup Data:**
  - Export all vectors and metadata from Weaviate or use your existing embedding files.

---

## 2. Install Qdrant

- **Install Qdrant Client:**
  - `pip install qdrant-client`
- **Run Qdrant Locally (No Docker Needed):**
  - Download the Qdrant binary for your OS: https://qdrant.tech/documentation/quick_start/#run-qdrant-without-docker
  - Start Qdrant: `./qdrant` (or the appropriate command for your OS)

---

## 3. Data Migration

- **Prepare Data:**
  - Ensure your embeddings and metadata are in a format compatible with Qdrant: `{ "id": ..., "vector": [...], "payload": { ... } }`
- **Import Data:**
  - Use the Qdrant Python client to create a collection and upload your vectors and payloads.
  - Example:
    ```python
    from qdrant_client import QdrantClient
    client = QdrantClient("localhost", port=6333)
    client.recreate_collection(
        collection_name="nobellm",
        vectors_config={"size": 1024, "distance": "Cosine"}
    )
    # Batch upload vectors and payloads here
    ```
  - See Qdrant docs: https://qdrant.tech/documentation/tutorials/quick_start/

---

## 4. Code Refactor

- **Create Qdrant Retriever:**
  - Copy `rag/retriever_weaviate.py` to `rag/retriever_qdrant.py` and refactor to use Qdrant client and logic.
- **Create Qdrant Query Module:**
  - Copy `rag/query_weaviate.py` to `rag/query_qdrant.py` and refactor for Qdrant.
- **Update Retriever Factory:**
  - In `rag/retriever.py`, update the factory to return your new `QdrantRetriever`.
- **Update Backend Config:**
  - In `backend/app/config.py`, add Qdrant config variables (host, port, API key if needed).
- **Update Dependency Injection:**
  - In `backend/app/deps.py`, add logic to initialize and use Qdrant.
- **Update Health Check:**
  - In `backend/app/main.py`, update the health check endpoint to test Qdrant connectivity and run a test query.
- **Replace Standalone Scripts:**
  - Replace `weaviate_search.py` with a Qdrant equivalent if schema inspection is needed.

---

## 5. Update Tests

- **E2E Health Test:**
  - Copy `tests/e2e/test_weaviate_health.py` to `test_qdrant_health.py` and update for Qdrant.
- **E2E Pipeline Test:**
  - Copy `tests/e2e/test_weaviate_e2e.py` to `test_qdrant_e2e.py` and update for Qdrant.

---

## 6. Update Requirements

- **Add Qdrant Client:**
  - Add `qdrant-client` to your requirements files.
- **Remove Weaviate Client:**
  - Remove `weaviate-client` from requirements once migration is complete.

---

## 7. Update Documentation

- **README Files:**
  - Update all references to Weaviate in `README.md`, `backend/README.md`, `rag/README.md`, and any other docs.
  - Document new environment variables and configuration for Qdrant.

---

## 8. Rollback Plan

- **Keep Weaviate Code:**
  - Retain Weaviate-related code and data until Qdrant is fully validated in production.
- **Be Ready to Revert:**
  - If any critical issues arise, revert to Weaviate by switching back the retriever and config.

---

## 9. Production Cutover

- **Switch Environment Variables/Configs** to point to Qdrant.
- **Monitor** for errors or performance issues.
- **Decommission Weaviate** only after Qdrant is stable.

---

## References

- [Qdrant Python Client Docs](https://qdrant.tech/documentation/quick_start/)
- [Qdrant Data Model](https://qdrant.tech/documentation/concepts/data_model/)
- [Qdrant vs. Weaviate Comparison](https://qdrant.tech/documentation/comparisons/weaviate/)

---

**This guide is tailored for the NobelLM project. Adapt as needed for your specific deployment and workflow.** 