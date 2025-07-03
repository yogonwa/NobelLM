# Backend (FastAPI)

**Important:** Always run the backend from the NobelLM project root directory. This ensures that the `rag` module and other top-level packages are importable by Python.

**Example (development):**

```bash
cd /path/to/NobelLM
uvicorn backend.app.main:app --reload --port 8000
```

**If you run from within the `backend/` directory, you will get an error like:**

```
ModuleNotFoundError: No module named 'rag'
```

**Troubleshooting:**
- Always run commands from the NobelLM root.
- Alternatively, set the `PYTHONPATH` to the project root:
  ```bash
  PYTHONPATH=$(pwd) uvicorn backend.app.main:app --reload --port 8000
  ```
- This is required for all scripts that import from top-level packages like `rag`, `embeddings`, etc. 

---

## Weaviate Vector DB Backend

The backend now supports **Weaviate** as a production vector database backend for semantic search and retrieval. The retriever selection is automatic and backend-agnostic:

- **Retriever Selection:**
    - The backend dynamically selects between FAISS and Weaviate based on environment/configuration.
    - See `/rag/retriever.py` for the retriever factory and interface.
    - See `/rag/retriever_weaviate.py` for the Weaviate retriever implementation.
    - See `/rag/query_weaviate.py` for low-level Weaviate query logic and configuration.
- **Configuration:**
    - Enable Weaviate by setting the appropriate config/env vars (e.g., `USE_WEAVIATE=1`, `WEAVIATE_URL`, `WEAVIATE_API_KEY`).
    - Embedding is always performed locally using the configured model (not via Weaviate inference module).
    - If Weaviate is not enabled/configured, the backend falls back to FAISS (in-process or subprocess for Mac/Intel).
- **All retrieval logic is backend-agnostic** and routed through the `BaseRetriever` interface.

---

## Troubleshooting

- Ensure all required Weaviate environment variables are set (`WEAVIATE_URL`, `WEAVIATE_API_KEY`).
- If you encounter issues with Weaviate, check logs for errors and verify connectivity/configuration.
- For local development or if Weaviate is unavailable, the backend will automatically use FAISS.

--- 