# TASKS – Nobel Laureate Speech Explorer  
_Last updated: 2025-05-22_

This file defines modular, numbered tasks for Cursor to execute. Each task includes:

- Task description
- Target file(s)
- Inputs and outputs
- Cursor-specific instructions

Cursor must always:
- Read and follow `.cursorrules`
- Update the relevant folder's `README.md` with a summary of new files or logic added
- Avoid editing outside the task's scope

---

## Task 1 – Scrape Literature Prize Winner URLs **[COMPLETE]**

**Goal**: Scrape the master list of Nobel Literature winners and extract structured links to each winner's `/facts/` page.

**Status**: Complete. URLs were manually curated and are now stored in `nobel_literature_facts_urls.json`.

**Target File**: `nobel_literature_facts_urls.json`  
**Input**: Manually curated list  
**Output**: `nobel_literature_facts_urls.json` – list of full URLs to laureate `/facts/` pages

---

## Task 2 – Scrape Laureate Metadata, Lecture, and Ceremony Speech

**Goal**: For each prize winner URL (`/facts/` page), scrape:
1. Laureate metadata
2. Nobel lecture transcript (`/speech/` page)
3. Ceremony speech transcript (by year, from `/ceremony-speech/` page)

**Target File**: `scraper/scrape_literature.py` (to be replaced/updated)  
**Input**: `nobel_literature_facts_urls.json`  
**Output**:
- `data/nobel_literature.json` – structured list of laureates and metadata
- `data/literature_speeches/*.txt` – one file per lecture
- `data/ceremony_speeches/*.txt` – one file per ceremony speech

### Details:
- Load laureate URLs from `nobel_literature_facts_urls.json` (not scraped dynamically)
- For each `/facts/` page, extract all required fields
- Fetch and save lecture and ceremony speech text as before
- Include error handling for missing/404 pages
- Write structured laureate dicts to `nobel_literature.json`
- Write plain text speeches to file
- Update `scraper/README.md` with schema description and file outputs

---

_Next: See Tasks 3–10 for embedding, indexing, querying, and UI development._

---

## Task 3 – Generate Metadata CSV
- **File:** `scraper/export_metadata.py`
- **Goal:** Convert JSON to tabular metadata
- **Input:** `nobel_literature.json`
- **Output:** `data/metadata.csv`
- **Instructions:**
  - Each row = one laureate
  - Columns: year, name, country, gender, category, specific_work_cited
  - Update `scraper/README.md` to document this transformation step

---

## Task 4 – Chunk Speech Text
- **File:** `embeddings/chunk_text.py`
- **Goal:** Load text files and break into paragraph-based or token-size chunks (300–500 words)
- **Input:** `/data/literature_speeches/*.txt`
- **Output:** JSON structure with chunk IDs, text, metadata
- **Instructions:**
  - Design for future compatibility with multiple categories
  - Include source filename and chunk index in each entry
  - Prefer paragraph boundaries when possible
  - Optionally support overlapping chunks (sliding window) for better context retention
  - Update `embeddings/README.md` with a description of this chunking logic

---

## Task 5 – Generate Embeddings
- **File:** `embeddings/embed_texts.py`
- **Goal:** Generate sentence embeddings using sentence-transformers (MiniLM)
- **Input:** Output from Task 4
- **Output:** `data/literature_embeddings.json`
- **Instructions:**
  - Use MiniLM (`all-MiniLM-L6-v2`)
  - Save one embedding per chunk
  - Write reusable function `generate_embedding(text)`
  - Add explanation comment about why this model is used and where it's from (Hugging Face)
  - Update `embeddings/README.md` to document model and embedding output format

---

## Task 6 – Build FAISS Index
- **File:** `embeddings/build_index.py`
- **Goal:** Build and persist FAISS vector store
- **Input:** `literature_embeddings.json`
- **Output:** `data/faiss_index/`
- **Instructions:**
  - Use cosine similarity index
  - Write reusable `load_index()` and `query_index()` functions
  - Ensure `build_index()` is CLI-runnable
  - Update `embeddings/README.md` to describe indexing and search API

---

## Task 7 – Implement Query Engine
- **File:** `rag/query_engine.py`
- **Goal:** Given a question, return GPT-based answer using retrieved chunks
- **Input:** User query, FAISS index
- **Output:** JSON with answer, sources
- **Instructions:**
  - Retrieve top 3 chunks from FAISS
  - Format a prompt string using those chunks (include a comment with template)
  - Call OpenAI GPT-3.5 using API key in `.env`
  - Handle empty or failed responses gracefully
  - Update `rag/README.md` to document the interface and behavior of `query_engine.py`

---

## Task 8 – Build Streamlit UI
- **File:** `frontend/app.py`
- **Goal:** Simple form to enter query and show answer + source citations
- **Input:** User query
- **Output:** Web interface with input and response view
- **Instructions:**
  - Use `st.text_input`, `st.button`, and `st.markdown`
  - Display top retrieved text chunks with source metadata (e.g., name, year)
  - Optionally include a dropdown or collapsible section for example queries
  - Update `frontend/README.md` to describe the UI and entry point

---

## Task 9 – Write Tests for Scraper
- **File:** `tests/test_scraper.py`
- **Goal:** Unit tests for Tasks 1–3
- **Input:** Scraper functions
- **Output:** Passing test file
- **Instructions:**
  - Use `pytest`
  - Mock HTTP requests with example HTML files if needed
  - Verify output shapes, error handling, and edge cases
  - Update `tests/README.md` to list tested modules and coverage

---

## Task 10 – Write README for /scraper
- **File:** `scraper/README.md`