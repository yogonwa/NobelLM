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

## Qdrant Vector DB Backend

The backend now supports **Qdrant** as the production vector database backend for semantic search and retrieval. The retriever selection is automatic and backend-agnostic:

- **Retriever Selection:**
    - The backend dynamically selects between FAISS (local/dev) and Qdrant (production/cloud) based on environment/configuration.
    - See `/rag/retriever.py` for the retriever factory and interface.
    - See `/rag/retriever_qdrant.py` for the Qdrant retriever implementation.
    - See `/rag/query_qdrant.py` for low-level Qdrant query logic and configuration.
- **Configuration:**
    - Set `QDRANT_URL` and `QDRANT_API_KEY` as environment variables or in your `.env` file.
    - Embedding is always performed using the configured model (via Modal or local).
- **All retrieval logic is backend-agnostic** and routed through the `BaseRetriever` interface.

**Example .env configuration:**
```
QDRANT_URL=https://your-qdrant-instance.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key
```

---

## Troubleshooting

- Ensure all required Qdrant environment variables are set (`QDRANT_URL`, `QDRANT_API_KEY`).
- If you encounter issues with Qdrant, check logs for errors and verify connectivity/configuration.
- For local development, FAISS is used by default if Qdrant is not configured.

---

## Quickstart

1. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Set up your `.env` file with Qdrant and OpenAI credentials.
3. Start the backend:
   ```bash
   uvicorn backend.app.main:app --reload --port 8000
   ```
4. Access the API at `http://localhost:8000/api/` and docs at `/docs` (if debug enabled).

---

## License

Part of the NobelLM project - see LICENSE for details. 