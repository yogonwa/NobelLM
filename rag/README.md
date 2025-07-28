# Query Engine – NobelLM RAG

**Status: COMPLETE as of July 2025.**

This module provides a modular, extensible, and testable interface for querying the Nobel Literature corpus using retrieval-augmented generation (RAG).

## Architecture

The RAG pipeline is designed to work with the modern NobelLM architecture:
- **Frontend**: React TypeScript application (`/frontend`)
- **Backend**: FastAPI service (`/backend`)
- **RAG Engine**: This module provides the core retrieval and generation logic

---

## Qdrant Vector DB Backend (July 2025)

NobelLM supports **Qdrant** as the production vector database backend for semantic search and retrieval. The retriever selection is automatic and backend-agnostic:

- **Retriever Selection:**
    - The RAG pipeline dynamically selects between FAISS (local/dev) and Qdrant (production/cloud) based on environment/configuration.
    - See [`rag/retriever.py`](./retriever.py) for the retriever factory and interface.
    - See [`rag/retriever_qdrant.py`](./retriever_qdrant.py) for the Qdrant retriever implementation.
    - See [`rag/query_qdrant.py`](./query_qdrant.py) for low-level Qdrant query logic and configuration.
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

## 📂 RAG Module File/Class Overview

| File                      | Main Classes/Functions         | Description                                                                                 |
|---------------------------|-------------------------------|---------------------------------------------------------------------------------------------|
| `query_engine.py`         | `answer_query`                | Canonical entry point for the RAG pipeline. Routes queries via QueryRouter, handles all retrieval modes safely. |
| `query_router.py`         | `QueryRouter`, `IntentClassifier`, `PromptTemplateSelector` | Classifies queries, selects retrieval config, prompt template, and routes to metadata/RAG.   |
| `thematic_retriever.py`   | `ThematicRetriever`           | Expands thematic queries, embeds, and retrieves relevant chunks.                             |
| `retriever.py`            | `BaseRetriever`, `InProcessRetriever`, `SubprocessRetriever`, `query_index` | Retrieves top-k chunks from FAISS index, supports mode-aware (in-process/subprocess) logic. |
| `retriever_qdrant.py`     | `QdrantRetriever`             | Qdrant-based retriever, implements `BaseRetriever` interface for backend-agnostic retrieval. |
| `query_qdrant.py`         | `query_qdrant`, `get_qdrant_client` | Low-level Qdrant query logic and client configuration.                                       |
| `dual_process_retriever.py`| `retrieve_chunks_dual_process`| Subprocess-based FAISS retrieval for Mac/Intel safety.                                      |
| `faiss_index.py`          | `load_index`, `reload_index`, `health_check` | Loads, reloads, and checks FAISS index integrity.                                           |
| `model_config.py`         | `get_model_config`            | Central config for model names, paths, embedding dims.                                      |
| `intent_classifier.py`    | `IntentClassifier`            | Rule-based classifier for factual/thematic/generative queries.                              |

---

## Features
- Embeds user queries using a **model-aware, config-driven approach** (BGE-Large or MiniLM, easily swappable)
- Retrieves top-k relevant chunks from the correct FAISS index (model-specific) or Qdrant collection
- Supports metadata filtering (e.g., by country, source_type)
- Constructs prompts for GPT-3.5
- Calls OpenAI API (with dry run mode)
- Returns answer and source metadata

---

## Qdrant Configuration

- Set `QDRANT_URL` and `QDRANT_API_KEY` in your environment or `.env` file.
- The retriever factory will automatically use Qdrant in production/cloud environments.
- For local development, FAISS is used by default.

---

## Quickstart

See [`/backend/README.md`](../backend/README.md) for backend setup and [`/frontend/README.md`](../frontend/README.md) for frontend setup.

---

## License

Part of the NobelLM project - see LICENSE for details. 