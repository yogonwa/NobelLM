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