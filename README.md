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
- **Frontend:** React + Vite + TypeScript (see `/frontend`)
- **Deployment:** Dockerized, Fly.io for production

---

## Quickstart

See `/frontend/README.md` for frontend setup and `/backend/README.md` for backend setup.

---

## License

Part of the NobelLM project - see LICENSE for details.
