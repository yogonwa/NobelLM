# TASKS – Nobel Laureate Speech Explorer

*Last Edited: 5/22/25*

This file contains modular, numbered tasks for Cursor to execute. Each task includes:
- **Description**
- **Target file(s)**
- **Inputs and expected outputs**
- **Cursor-specific guidance**

**Cursor must always:**
- Read and follow the `.cursorrules` file
- Update `README.md` in the target folder with a brief summary of new files or interfaces added
- Avoid editing outside the specified files or scope

---

## Task 1 – Scrape Literature Prize URLs
- **File:** `scraper/scrape_literature.py`
- **Goal:** Scrape the list page to extract links for all Nobel Literature prize entries
- **Input:** [Nobel Literature List](https://www.nobelprize.org/prizes/lists/all-nobel-prizes-in-literature/all/)
- **Output:** List of prize detail page URLs (store in `literature_prize_links.json` or return from a function)
- **Instructions:**
  - Use `requests` + `BeautifulSoup`
  - Store list in a variable named `literature_prize_links`
  - Output should be reusable in later tasks
  - Update `scraper/README.md` to describe the purpose and output of this script

---

## Task 2 – Scrape Laureate Facts & Speeches
- **File:** `scraper/scrape_literature.py`
- **Goal:** For each prize URL, scrape:
  - Facts page (e.g. name, country, year, category)
  - Nobel Lecture and Ceremony Speech pages
- **Input:** URLs from Task 1
- **Output:** `data/nobel_literature.json` and `/data/literature_speeches/*.txt`
- **Instructions:**
  - Store structured metadata per laureate
  - Normalize gender, category, and speech fields
  - Write each speech as a separate `.txt` file (named by year + name)
  - Update `scraper/README.md` to include this task's data output and structure

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
- **Goal:** Summarize folder purpose, file roles, and cross-module interactions
- **Instructions:**
  - Describe each file created so far
  - Explain CLI or function entry points
  - Mention outputs and how they are used downstream
  - Include references to `nobel_literature.json`, `metadata.csv`, and speech file generation


