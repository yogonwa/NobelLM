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

[![Hugging Face Spaces](https://img.shields.io/badge/Live%20Demo-Hugging%20Face%20Spaces-blue?logo=huggingface)](https://huggingface.co/spaces/yogonwa/nobelLM)

# NobelLM

**Semantic search + Retrieval-Augmented Generation (RAG) for Nobel Prize speeches**  
Explore the words of Nobel laureates through embeddings, vector search, and a lightweight Streamlit UI.

---

## 🎯 Project Overview

NobelLM is a modular, full-stack GenAI project that:

- Scrapes and normalizes NobelPrize.org metadata and speeches (starting with the Literature category)
- Embeds speech content using sentence-transformers (MiniLM or BGE-Large, model-aware)
- Supports natural language Q&A via RAG using OpenAI's GPT-3.5
- Exposes a simple interactive UI powered by Streamlit
- **Is publicly deployed and accessible via Hugging Face Spaces: [Live Demo](https://huggingface.co/spaces/yogonwa/nobelLM)**
- Deploys publicly via Hugging Face Spaces

This project is designed for learning, modularity, and extensibility.

---

## 🧠 Key Features

- 🗂 Structured metadata and full-text speech extraction
- 🔎 Local embedding + FAISS vector search
- 🤖 RAG-powered question answering with GPT-3.5
- ⚡️ Fast, robust factual Q&A from a flat laureate metadata structure (see below)
- 🖥 Streamlit interface for live semantic search
- 🚀 Public deployment via Hugging Face Spaces
- 📦 **Model-aware, token-based chunking with optional overlap for context continuity**
- 🧩 **Embeddings generated for each chunk using BGE-Large or MiniLM; outputs are model-specific**
- 🛠️ **Centralized model config for easy model switching and reproducibility**

## Pre-retrieval Metadata Filtering

NobelLM now supports **pre-retrieval metadata filtering** at the retrieval layer. This means that any filter (e.g., by gender, country, source_type) is applied to the chunk metadata before vector search (FAISS), ensuring only relevant chunks are searched. This improves efficiency, explainability, and privacy.

- Filters can be passed as a dictionary (e.g., {"gender": "female", "country": "USA"}) to any query.
- Filtering is supported in both in-process and subprocess retrieval modes.
- Any metadata field present in the chunk index can be used for filtering.
- The output schema is privacy-preserving: only public fields (e.g., chunk_id, text_snippet) are returned in answers.

See `tests/README.md` and `tests/test_coverage_plan.md` for integration test coverage.

---

## 🗺️ Architecture Overview

View the interactive RAG pipeline architecture diagram here:  
[NobelLM RAG Pipeline – Mermaid Chart](https://www.mermaidchart.com/app/projects/f11ebb0b-c097-43bd-80d5-e9740319bf5e/diagrams/4ac34c1b-cea0-40b8-a1d3-10014bbcf904/version/v0.1/edit)

---

## ⚙️ Tech Stack

- **Language**: Python 3.11+
- **Scraping**: `requests`, `beautifulsoup4`
- **Text Parsing**: `PyMuPDF`, custom HTML/text cleaning
- **Embeddings**: `sentence-transformers` (MiniLM or BGE-Large, model-aware chunking), upgradeable to OpenAI `text-embedding-3-small`
- **Vector Store**: `FAISS` (cosine similarity, local CPU)
- **Frontend**: `Streamlit` (hosted on Hugging Face Spaces)
- **Testing**: `pytest`
- **Deployment**: GitHub + Hugging Face Spaces

---

## 📁 Folder Structure

```text
NobelLM/
├── data/                 # Raw and processed data (JSON, CSV, text, embeddings)
├── scraper/              # NobelPrize.org scraping scripts
├── embeddings/           # Chunking and vector embedding logic
├── rag/                  # Retrieval-augmented generation pipeline
├── frontend/             # Streamlit UI app
├── utils/                # Shared helpers (e.g., cleaning)
├── tests/                # Pytest test modules
├── .env.example          # Environment variable template
├── requirements.txt      # Project dependencies
├── IMPLEMENTATION_PLAN.md
├── SPEC.md
├── TASKS.md
├── NOTES.md
├── .cursorrules          # Cursor AI execution rules
```

---

## 🚀 Getting Started

1. **Clone the repo**  
   ```bash
   git clone https://github.com/yourusername/NobelLM.git
   cd NobelLM
   ```
2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or 'venv\Scripts\activate' on Windows
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Add your OpenAI API key to the .env file
   ```
5. **Run an example module**
   ```bash
   python -m scraper.scrape_literature
   ```

---

## 🛠️ Model-Aware Configuration

All chunking, embedding, indexing, and RAG operations are now **model-aware and config-driven**. The embedding model, FAISS index, and chunk metadata paths are centrally managed in [`rag/model_config.py`](./rag/model_config.py):

- To switch models (e.g., BGE-Large vs MiniLM), pass `--model` to any CLI tool, or set `model_id` in your code or UI.
- All file paths, model names, and embedding dimensions are set in one place.
- Consistency checks ensure the loaded model and index match in dimension, preventing silent errors.
- Enables easy A/B testing and reproducibility.

**Example:**
```python
from rag.query_engine import query
from rag.model_config import DEFAULT_MODEL_ID

# Query using the default model (BGE-Large)
response = query("What do laureates say about justice?", dry_run=True)

# Query using MiniLM
response = query("What do laureates say about justice?", dry_run=True, model_id="miniLM")
```

**To add a new model:**
- Add its config to `rag/model_config.py`.
- All downstream code and scripts will pick it up automatically.

## 🧩 Mode-Agnostic Retriever Layer (June 2025 Refactor)

**New as of June 2025:** NobelLM now uses a modern, mode-agnostic retriever abstraction for all chunk retrieval, both factual and thematic.

- All retrieval is routed through a `BaseRetriever` interface, with two main implementations:
  - `InProcessRetriever`: Runs embedding and FAISS search in-process (Linux/prod, default).
  - `SubprocessRetriever`: Runs FAISS search in a subprocess for Mac/Intel safety (set `NOBELLM_USE_FAISS_SUBPROCESS=1`).
- A factory function (`get_mode_aware_retriever`) selects the correct backend based on environment.
- The interface is always `retrieve(query: str, top_k: int, filters: dict) -> List[dict]`.
- Thematic and factual queries both use this interface—no more shape/type bugs or mode-specific logic in callers.
- **Extensible:** You can add new backends (e.g., ElasticSearch, hybrid, remote API) by subclassing `BaseRetriever` and updating the factory.

**Example usage:**
```python
from rag.retriever import get_mode_aware_retriever
retriever = get_mode_aware_retriever(model_id)
chunks = retriever.retrieve("What did laureates say about justice?", top_k=10)
```

This refactor makes the pipeline robust, testable, and future-ready for multi-backend or hybrid search.

---

## 🔎 RAG Pipeline Overview

All retrieval-augmented generation (RAG) logic is implemented in [`rag/README.md`](rag/README.md). See that file for:
- File/class overview
- Full pipeline architecture diagram
- API usage and configuration
- Query router, intent classification, and thematic search details

---

## 🔍 Thematic Search & Query Reformulation

### Thematic Query Expansion

For queries about themes (e.g., "What do laureates say about justice?"), the system uses a two-step process:

1. **ThemeReformulator** (see `config/theme_reformulator.py`):
   - Loads a mapping of canonical themes to keywords (see `config/themes.json`).
   - Lemmatizes both the user query and the theme keywords using spaCy for robust matching.
   - Expands the query to include all related terms for each detected theme.

2. **ThematicRetriever** (see `rag/thematic_retriever.py`):
   - Reformulates the query using the expanded set of theme keywords.
   - Embeds the reformulated query and retrieves the top-k most relevant chunks from the vector store.
   - Logs both the original and reformulated query for transparency.

**Example:**

User query: `"What do laureates say about morality?"`

- ThemeReformulator expands to: `justice fairness law morality rights equality injustice`
- ThematicRetriever embeds this expanded string for semantic search, improving recall and relevance.

### Modularity & Testability
- Thematic logic is encapsulated in dedicated, testable classes.
- Easy to extend with new themes, keywords, or retrieval strategies.
- Logging and docstrings throughout for transparency and maintainability.

### Usage Example
```python
from rag.thematic_retriever import ThematicRetriever
from config.theme_reformulator import ThemeReformulator

# Instantiate with your embedder and retriever
reformulator = ThemeReformulator("config/themes.json")
thematic_retriever = ThematicRetriever(embedder, retriever)

query = "What do laureates say about morality?"
chunks = thematic_retriever.retrieve(query, top_k=15)
# Use chunks for prompt construction, etc.
```

---

## Testing
Unit tests for extraction/parsing logic (e.g., HTML parsing, gender inference) are in `/tests/test_scraper.py`. Run `pytest` from the project root.

- Unit tests for the metadata handler should use the flat laureate structure.
- Integration tests should cover both factual (metadata) and RAG queries.
- All model switching and config logic is covered by tests in the relevant modules.

**Backend responses now always include an `answer_type` field, which the frontend uses to render metadata vs RAG answers appropriately.**

---

## 📌 Roadmap

| Phase | Description |
|-------|-------------|
| **M1** | Scrape and normalize Nobel Literature data |
| **M2** | Generate text chunks and sentence embeddings (model-aware, token-based, with optional overlap; supports BGE-Large and MiniLM) |
| **M3** | Build FAISS index and RAG query pipeline (model-aware) |
| **M4** | Launch public Streamlit UI |
| **M5** | Add prompt templates and memory scaffolding |
| **M5b** | Extend pipeline to other Nobel Prize categories |
| **M6** | Migrate embedding generation to OpenAI API |

See [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md) and [`SPEC.md`](./SPEC.md) for detailed milestones.

---

## 📄 License
This project is for educational and exploratory purposes only. Source data is publicly available and usage falls under fair use.

---

✍️ Author
Built by Joe Gonwa as a structured learning project in GenAI and RAG systems.
Feedback, PRs, and suggestions are always welcome!

## 📚 Further Reading & Related Documentation

| Document                                 | Description                                                      |
|-------------------------------------------|------------------------------------------------------------------|
| [RAG README.md](rag/README.md)            | RAG pipeline details, file/class overview, and architecture.     |
| [SPEC.md](SPEC.md)                        | Master project specification, schema, data sources, and goals.   |
| [tests/README.md](tests/README.md)        | Detailed test coverage, environment notes, and test philosophy.  |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Milestones, phases, and planned features.                |
| [META_ANALYSIS.md](META_ANALYSIS.md)      | Strategy, design notes, and meta-level analysis.                 |
