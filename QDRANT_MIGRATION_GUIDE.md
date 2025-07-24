# Qdrant Migration Guide for NobelLM (Docker Strategy)

---

## Progress Checklist (as of 2025-07-24)

- [x] Data migration script created and committed to git (`scripts/migrate_to_qdrant.py`)
- [x] Embeddings and metadata uploaded to Qdrant Cloud (UUIDv5 IDs, .env for credentials)
- [ ] Refactor retriever and query modules for Qdrant
- [ ] Update retriever factory and backend config for Qdrant
- [ ] Update backend dependency injection and health check for Qdrant
- [ ] Replace Weaviate scripts with Qdrant equivalents
- [ ] Update and run E2E tests for Qdrant
- [ ] Update documentation and READMEs for Qdrant
- [ ] Remove Weaviate client from requirements (after full cutover)

_Note: The migration script uses UUIDv5 for Qdrant Cloud compatibility and loads credentials from .env._

---

## 1. Preparation

- **Inventory Weaviate Usage:**
  - Review all files that reference Weaviate: `rag/retriever_weaviate.py`, `rag/query_weaviate.py`, `rag/retriever.py`, `backend/app/config.py`, `backend/app/deps.py`, `backend/app/main.py`, `weaviate_search.py`, `tests/e2e/test_weaviate_health.py`, `tests/e2e/test_weaviate_e2e.py`, and documentation files.
- **Backup Data:**
  - Export all vectors and metadata from Weaviate or use your existing embedding files.

---

## 2. Install Qdrant (Docker)

- **Install Docker:**
  - Download and install Docker Desktop for your OS: https://www.docker.com/products/docker-desktop/
  - Start Docker Desktop and ensure it is running.
- **Pull the Qdrant Docker Image:**
  - `docker pull qdrant/qdrant`
- **Run Qdrant in a Docker Container:**
  - ```sh
    docker run -p 6333:6333 -p 6334:6334 \
      -v "$(pwd)/qdrant_storage:/qdrant/storage:z" \
      qdrant/qdrant
    ```
  - This exposes the REST API at `localhost:6333` and persists data in the `qdrant_storage` directory.
- **Access the Qdrant Web UI:**
  - Open [http://localhost:6333/dashboard](http://localhost:6333/dashboard) in your browser.

---

## 3. Data Migration

- **Prepare Data:**
  - Ensure your embeddings and metadata are in a format compatible with Qdrant: `{ "id": ..., "vector": [...], "payload": { ... } }`
- **Import Data:**
  - Use the Qdrant Python client to connect to the running Docker instance:
    ```python
    from qdrant_client import QdrantClient
    client = QdrantClient(url="http://localhost:6333")
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
  - Document new environment variables and configuration for Qdrant, including Docker usage.

---

## 8. Rollback Plan

- **Keep Weaviate Code:**
  - Retain Weaviate-related code and data until Qdrant is fully validated in production.
- **Be Ready to Revert:**
  - If any critical issues arise, revert to Weaviate by switching back the retriever and config.

---

## 9. Production Cutover

- **Switch Environment Variables/Configs** to point to Qdrant (Docker host/port).
- **Monitor** for errors or performance issues.
- **Decommission Weaviate** only after Qdrant is stable.

---

## References

- [Qdrant Python Client Docs](https://qdrant.tech/documentation/quick_start/)
- [Qdrant Data Model](https://qdrant.tech/documentation/concepts/data_model/)
- [Qdrant vs. Weaviate Comparison](https://qdrant.tech/documentation/comparisons/weaviate/)
- [Qdrant Docker Quickstart](https://qdrant.tech/documentation/quick_start/#run-qdrant-with-docker)

---

**This guide is tailored for the NobelLM project and assumes Docker is the primary method for running Qdrant locally and in production. Adapt as needed for your specific deployment and workflow.** 