---
title: NobelLM
emoji: 📚
colorFrom: blue
colorTo: indigo
sdk: streamlit
app_file: app.py
pinned: false
---



# NobelLM



**Semantic search + Retrieval-Augmented Generation (RAG) for Nobel Prize speeches**  
Explore the words of Nobel laureates through embeddings, vector search, and a lightweight Streamlit UI.

---

## 🎯 Project Overview

NobelLM is a modular, full-stack GenAI project that:

- Scrapes and normalizes NobelPrize.org metadata and speeches (starting with the Literature category)
- Embeds speech content using sentence-transformers (MiniLM)
- Supports natural language Q&A via RAG using OpenAI's GPT-3.5
- Exposes a simple interactive UI powered by Streamlit
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


## ⚙️ Tech Stack

- **Language**: Python 3.11+
- **Scraping**: `requests`, `beautifulsoup4`
- **Text Parsing**: `PyMuPDF`, custom HTML/text cleaning
- **Embeddings**: `sentence-transformers` (MiniLM model), upgradeable to OpenAI `text-embedding-3-small`
- **Vector Store**: `FAISS` (cosine similarity, local CPU)
- **Frontend**: `Streamlit` (hosted on Hugging Face Spaces)
- **Testing**: `pytest`
- **Deployment**: GitHub + Hugging Face Spaces

---

## 📌 Roadmap

| Phase | Description |
|-------|-------------|
| **M1** | Scrape and normalize Nobel Literature data |
| **M2** | Generate text chunks and sentence embeddings |
| **M3** | Build FAISS index and RAG query pipeline |
| **M4** | Launch public Streamlit UI |
| **M5** | Add prompt templates and memory scaffolding |
| **M5b** | Extend pipeline to other Nobel Prize categories |
| **M6** | Migrate embedding generation to OpenAI API |

See [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md) and [`TASKS.md`](./TASKS.md) for detailed milestones.

---

## 🚀 Getting Started

1. **Clone the repo**  
   ```bash
   git clone https://github.com/yourusername/NobelLM.git
   cd NobelLM
Create a virtual environment

bash
Copy code
python -m venv venv
source venv/bin/activate  # or 'venv\Scripts\activate' on Windows
Install dependencies

bash
Copy code
pip install -r requirements.txt
Set up environment variables

bash
Copy code
cp .env.example .env
# Add your OpenAI API key to the .env file
Run an example module

bash
Copy code
python -m scraper.scrape_literature
📄 License
This project is for educational and exploratory purposes only. Source data is publicly available and usage falls under fair use.

✍️ Author
Built by Joe Gonwa as a structured learning project in GenAI and RAG systems.
Feedback, PRs, and suggestions are always welcome!

## Testing
Unit tests for extraction/parsing logic (e.g., HTML parsing, gender inference) are in `/tests/test_scraper.py`. Run `pytest` from the project root.

- Unit tests for the metadata handler should use the flat laureate structure.
- Integration tests should cover both factual (metadata) and RAG queries.

**Backend responses now always include an `answer_type` field, which the frontend uses to render metadata vs RAG answers appropriately.**

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

## 🧪 TODO: Thematic Pipeline Test Coverage

Below is a checklist of recommended tests for the thematic search and routing pipeline. Use this as a guide for robust, staff-level test coverage. Implement each as a separate test file or function as appropriate.

### 1. IntentClassifier (Unit)
- **Purpose:** Ensure queries are correctly classified as factual, thematic, or generative.
- **Implementation:**
  - Test with factual, thematic, and generative queries.
  - Test precedence rules (generative > thematic > factual).
  - Test case insensitivity and fallback behavior.

### 2. ThemeReformulator (Unit)
- **Purpose:** Ensure theme extraction and expansion works, including lemmatization.
- **Implementation:**
  - Test extract_theme_keywords and expand_query_terms for exact, lemmatized, and multi-theme matches.
  - Test with synonyms, plurals, and unrelated queries.

### 3. ThematicRetriever (Unit/Mock)
- **Purpose:** Ensure reformulated query is used for embedding and retrieval.
- **Implementation:**
  - Mock embedder and retriever; check that expanded terms are used.
  - Test fallback to original query if no terms found.
  - Assert logging of user and reformulated queries.

### 4. QueryRouter (Integration)
- **Purpose:** Ensure correct routing, logging, and config for thematic queries.
- **Implementation:**
  - Test that thematic queries are routed correctly and logs include expanded terms.
  - Assert correct prompt template and retrieval config.

### 5. PromptTemplateSelector (Unit)
- **Purpose:** Ensure correct template is returned and can be formatted.
- **Implementation:**
  - Test for each intent; format with sample context and query.

### 6. Chunk Formatting Utility (Unit)
- **Purpose:** Ensure all chunk metadata is included in LLM prompt context.
- **Implementation:**
  - Test with all fields present, missing fields, and custom templates.

### 7. End-to-End Thematic Query (Integration)
- **Purpose:** Ensure the full pipeline works from user query to LLM prompt.
- **Implementation:**
  - Simulate a thematic query; assert correct intent, expanded terms, chunk formatting, and prompt template.
  - Use dry run mode to check prompt content without calling LLM.

### 8. Logging and Error Handling (Unit/Integration)
- **Purpose:** Ensure logs are written and errors are handled gracefully.
- **Implementation:**
  - Use pytest caplog to check logs for user and reformulated queries.
  - Test missing theme file, missing metadata, and other edge cases.

---

**Implementation Guidance:**
- Place unit tests in `tests/` with clear, descriptive names (e.g., `test_theme_reformulator.py`).
- Use static fixtures and mocks for dependencies (embedder, retriever, etc.).
- Add docstrings and comments to all test functions.
- Run tests with `pytest` and ensure all pass before merging changes.
