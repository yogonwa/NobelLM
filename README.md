---
title: NobelLM
emoji: 📚
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.32.0
app_file: app.py
pinned: false
---

# NobelLM

**Semantic search + Retrieval-Augmented Generation (RAG) for Nobel Prize speeches**

---

## 🚨 Migration Notice (June 2025)

- The Streamlit UI (Hugging Face Spaces) is now deprecated.
- The canonical frontend is now a modern React + Vite + TypeScript app in `/frontend`.
- All new features, bugfixes, and deployments should target the React frontend.
- See `/frontend/README.md` for setup and usage.

---

## 🔄 Modal Embedding Service (June 2025)

NobelLM now uses a **unified, environment-aware embedding service** for all user queries:

- **Production:** All queries are embedded via a dedicated Modal microservice (see `modal_embedder.py`).
- **Development:** Embedding is performed locally using the BGE-Large model.
- **No more embedding in Weaviate or Fly API.**
- The embedding logic is centralized in `rag/modal_embedding_service.py` and used by all retrievers.
- The system automatically detects the environment and routes embedding requests accordingly, with robust fallback logic.

**Benefits:**
- Consistent, scalable, and cost-effective embedding in production
- No need to run large models locally in prod containers
- Simplified architecture and maintenance

See [`rag/README.md`](rag/README.md) for technical details and extension/testing instructions.

---

## Project Overview

NobelLM is a modular, full-stack GenAI project that:
- Scrapes and normalizes NobelPrize.org metadata and speeches (starting with the Literature category)
- Embeds speech content using sentence-transformers (MiniLM or BGE-Large, model-aware)
- Supports natural language Q&A via RAG using OpenAI's GPT-3.5
- Exposes a modern React UI powered by Vite and Tailwind CSS
- **Production deployment is via Fly.io**

---

## Architecture

- **Backend:** FastAPI (Python) with RAG pipeline
    - **Vector DB:** Supports both FAISS (default, local/dev) and Weaviate (production, cloud-native)
    - **Retriever Selection:** The backend dynamically selects between FAISS and Weaviate based on environment/configuration. See `/rag/retriever.py` and `/rag/retriever_weaviate.py` for details.
    - **RAG Logic:** Modular, model-aware, and backend-agnostic. All retrieval is routed through a unified interface.
    - **Weaviate Integration:** See `/rag/query_weaviate.py` and `/rag/retriever_weaviate.py` for Weaviate-specific logic and configuration.
- **Frontend:** React + Vite + TypeScript (see `/frontend`)
- **Deployment:** Dockerized, Fly.io for production

---

## Weaviate Vector DB Support

- **Production deployments** now support Weaviate as a vector database backend for semantic search and retrieval.
- **Configuration:**
    - Set `USE_WEAVIATE=1` (or equivalent) in your backend config or environment to enable Weaviate.
    - Required environment variables: `WEAVIATE_URL`, `WEAVIATE_API_KEY` (see `/rag/query_weaviate.py`).
    - Embedding is always performed locally using the configured model (not via Weaviate inference module).
- **Fallback:** If Weaviate is not enabled/configured, the backend uses FAISS (in-process or subprocess for Mac/Intel).
- **All retrieval logic is backend-agnostic** and routed through the `BaseRetriever` interface.

---

## Quickstart

See `/frontend/README.md` for frontend setup and `/backend/README.md` for backend setup.

---

## License

Part of the NobelLM project - see LICENSE for details.
