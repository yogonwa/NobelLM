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
2. Nobel lecture transcript (`/lecture/` page, save as .txt only)
3. Ceremony speech transcript (by year, from `/ceremony-speech/` page, save as .txt only)

**Target File**: `scraper/scrape_literature.py` (to be replaced/updated)  
**Input**: `nobel_literature_facts_urls.json`  
**Output**:
- `data/nobel_literature.json` – structured list of laureates and metadata (no speech text fields)
- `data/acceptance_speeches/*.txt` – one file per laureate's acceptance (banquet) speech
- `data/ceremony_speeches/*.txt` – one file per ceremony speech
- `data/nobel_lectures/*.txt` – one file per laureate's lecture (from PDF extraction)

### Details:
- Load laureate URLs from `nobel_literature_facts_urls.json` (not scraped dynamically)
- For each `/facts/` page, extract all required fields
- Fetch and save lecture and ceremony speech text as .txt files only
- Include error handling for missing/404 pages
- Write structured laureate dicts to `nobel_literature.json` (metadata only)
- Write plain text speeches to file
- Update `scraper/README.md` with schema description and file outputs
- Whitespace and punctuation normalization is handled by `normalize_whitespace`.
- All debug prints have been removed from the extraction pipeline.
- Outputs are robust and production-ready.

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

## Task 4 – Chunk and Tag Speech Text for Embedding

- Parse all three text types for each laureate:
  - `nobel_lecture` (full lecture text)
  - `acceptance_speech` (banquet/acceptance remarks)
  - `ceremony_speech` (committee's justification)
- Chunk each text into ~300–500 word blocks, using paragraph boundaries.
  - Ensure no mid-sentence cuts.
- For each chunk, tag with:
  - `source_type` (nobel_lecture, acceptance_speech, ceremony_speech)
  - `laureate`
  - `year_awarded`
  - `category`
- Include structured metadata fields as top-level properties (e.g., `gender`, `country`, etc.).
- Store both `raw_text` (original) and `clean_text` (for embedding/audit) for each chunk.
- **Output:** `data/chunks_literature_labeled.jsonl` (primary, newline-delimited) and optionally `data/chunks_literature_labeled.json` (array version)
  - *Best practice:* Use explicit, consistent, and scope-aware naming that aligns with your modular system.
  - **Preferred Naming Convention:**
    - `data/chunks_literature_labeled.jsonl`
      - `chunks` → prepped text for embedding
      - `literature` → category scope (future-proofing for other categories)
      - `labeled` → includes metadata tags (e.g., source_type, gender)
      - `.jsonl` → newline-delimited, standard for embeddings/streaming
- **Implementation:** Extend the existing chunk logic in `embeddings/`.
- **Update:** `embeddings/README.md` to document the chunking and tagging process.

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
- **Goal:** Add documentation for extraction function unit tests
- **Instructions:**
  - Add unit tests for extraction functions in `scraper/scrape_literature.py` (see `/tests/test_scraper.py`)

---

## Task 11 – Scrape Nobel Lecture (Title + Transcript)

**Status**: Complete. Implemented in speech_extraction.py and scrape_literature.py.

**File:** `scraper/scrape_literature.py`
**Goal:** For each laureate, fetch and extract their Nobel Lecture page
**Input:**  
  - URL: `https://www.nobelprize.org/prizes/literature/{year}/{lastname}/lecture/`
**Output:**  
  - **JSON fields:**  
    - `nobel_lecture_title` (from `<h2.article-header__title>`)
    - `nobel_lecture_text` (from `<div.article-body>`, cleaned)
  - **Plain text file:**  
    - `data/nobel_lectures/{year}_{lastname}.txt`

---

## Task 12 – Clean Up Navigation & Footer Noise in All Scraped Text

**Status**: Complete. Implemented as clean_speech_text in speech_extraction.py and used throughout scraping pipeline.

**File:** `scraper/speech_extraction.py`
**Goal:** Improve output quality by removing common page UI noise in scraped speech text
**Applies To:**  
  - Nobel lectures
  - Ceremony speeches
  - Press releases
**Instructions:**
  - Add a shared function:  
    ```python
    def clean_speech_text(text: str) -> str
    ```
  - Filter out lines like:
    - "Back to top"
    - "Explore prizes and laureates"
    - Empty lines or repeated boilerplate
  - **Example logic:**
    ```python
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line and not line.lower().startswith("back to top")]
    return "\n".join(lines).strip()
    ```
  - Apply this cleanup before saving any `.txt` speech file or inserting text into JSON
  - Ensure consistent formatting across outputs

---

## Task 13a – Download English Nobel Lecture PDFs **[COMPLETE]**

**Goal:** For each laureate, locate and download the English-language Nobel lecture PDF (if available). Save to `data/nobel_lectures_pdfs/{year}_{lastname}.pdf`. Log success or failure. No text extraction at this stage.

**Status:** Complete. The pipeline attempts to find and download the English PDF for each laureate's lecture page. If not found, logs the absence and falls back to HTML extraction. No text extraction from PDF is performed at this stage.

---

## Task 13b – Extract Text from Nobel Lecture PDFs
- **File:** `scripts/extract_pdf_lectures.py` (new standalone script)
- **Tool:** pdfplumber

**Goal:**
Extract clean plaintext transcripts from previously downloaded Nobel lecture PDFs.

**Directions:**
- Iterate through `.pdf` files in `data/nobel_lectures_pdfs/`
- Use pdfplumber to open each file and extract text (joined across pages)
- Clean the text with `clean_speech_text()`
- Save to: `data/nobel_lectures/{year}_{lastname}.txt`
- (Optional) Delete the `.pdf` after successful extraction

**Output:**
- Text files in: `data/nobel_lectures/`
- Optional cleanup of `data/nobel_lectures_pdfs/`
- Console log of extracted file count and any errors

**Test Guidance:**
- Use a few known English PDFs (e.g. Glück, Ishiguro) as test fixtures
- Validate line count, formatting, and presence of content
- Log empty or unreadable pages for review

---

## Task 14 – Incremental Update for Nobel Literature JSON

**Goal:**
Prevent full overwrite of `nobel_literature.json` on each scrape. Instead, merge new/updated records into the existing file.

**Motivation:**
- See NOTES.md section on Data Overwrite vs. Incremental Update.
- Avoids loss of manual corrections or additional metadata.
- Supports partial re-scrapes and robust downstream workflows.

**Implementation Outline:**
- On scrape, load existing JSON if present.
- For each new record, update or add to the existing data (by year and laureate name).
- Write back the merged result.
- Optionally, backup the old file before writing.
- Add/update a `last_updated` timestamp per record.

**Target File:** `scraper/scrape_literature.py`
**Status:** TODO

---

# Progress Update (June 2025)
- Tasks 1–13b are COMPLETE. The codebase now robustly handles missing/empty lectures, and the utility script for noisy file cleanup is in place.
- Task 14 (incremental update/merge for nobel_literature.json) is the next major improvement (TODO).

---