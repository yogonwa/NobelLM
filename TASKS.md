# TASKS – Nobel Laureate Speech Explorer  
_Last updated: 2025-06-21_

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

## Task 0 – FastAPI Migration (Phase 2) **[COMPLETE]**

**Goal**: Migrate from Streamlit to FastAPI + Vite architecture for production deployment.

**Status**: Complete. FastAPI backend is fully functional with RAG pipeline integration.

**Target Files**: 
- `backend/app/main.py` - FastAPI application entry point
- `backend/app/routes.py` - API route handlers
- `backend/app/deps.py` - Dependency injection
- `backend/app/config.py` - Environment configuration
- `backend/requirements.txt` - Python dependencies

**Input**: Existing RAG pipeline and FAISS index
**Output**: 
- ✅ FastAPI server with endpoints: `/`, `/api/health`, `/api/query`, `/api/models`
- ✅ Pydantic request/response models with validation
- ✅ RAG pipeline integration with dependency injection
- ✅ Environment configuration management
- ✅ Comprehensive error handling and logging

**Technical Achievements**:
- Fixed Pydantic import issues (updated to pydantic-settings)
- Resolved function signature mismatches in RAG integration
- Avoided Streamlit caching conflicts with direct FAISS/model loading
- Implemented proper async/await patterns for FastAPI

**Next**: Phase 3 - Docker Environment Setup

---

## Task 1 – Scrape Literature Prize Winner URLs **[COMPLETE]**

**Goal**: Scrape the master list of Nobel Literature winners and extract structured links to each winner's `/facts/` page.

**Status**: Complete. URLs were manually curated and are now stored in `nobel_literature_facts_urls.json`.

**Target File**: `nobel_literature_facts_urls.json`  
**Input**: Manually curated list  
**Output**: `nobel_literature_facts_urls.json` – list of full URLs to laureate `/facts/` pages

---

## Task 2 – Scrape Laureate Metadata, Lecture, and Ceremony Speech **[COMPLETE]**

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

## Task 4 – Chunk and Tag Speech Text for Embedding **[COMPLETE]**

**Status:** Complete. Implemented in `embeddings/chunk_literature_speeches.py`.

**Completion Note:**
- All three speech types (nobel_lecture, acceptance_speech, ceremony_speech) and short fields (prize_motivation, life_blurb, work_blurb) are chunked and tagged as specified.
- Each chunk includes a unique `chunk_id` and all required metadata fields, with a single `text` field (no raw/clean distinction).
- Output written to `data/chunks_literature_labeled.jsonl`.
- See `embeddings/chunk_literature_speeches.py` and `embeddings/README.md` for details.

---

## Task 5 – Generate Embeddings  **[COMPLETE]**
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

## Task 6 – Build FAISS Index **[COMPLETE]**
- **File:** `embeddings/build_index.py`
- **Goal:** Build and persist FAISS vector store
- **Input:** `literature_embeddings.json`
- **Output:** `data/faiss_index/`
- **Instructions:**
  - Use cosine similarity index
  - Write reusable `load_index()` and `query_index()` functions
  - Ensure `build_index()` is CLI-runnable
  - Update `embeddings/README.md` to describe indexing and search API
  - **Note:** The script sets `OMP_NUM_THREADS=1` at startup for macOS stability (prevents segfaults with FAISS/PyTorch). See README for troubleshooting.

---

## Task 7 – Implement Query Engine **[COMPLETE]**

**Goal:** Given a user question, return a GPT-based answer using retrieved chunks from the Nobel Literature corpus.

**Status:** Complete. The query engine is implemented, tested, and documented. It supports dry run mode, metadata filtering, and robust error handling. See `rag/query_engine.py` and `rag/README.md` for usage and API details.

**Input:** User query, FAISS index
**Output:** JSON with answer and sources

---

## Task 8 – Build Streamlit UI **[COMPLETE]**
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

## Task 11 – Scrape Nobel Lecture (Title + Transcript) **[COMPLETE]**

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

## Task 12 – Clean Up Navigation & Footer Noise in All Scraped Text **[COMPLETE]**

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

## Task 13b – Extract Text from Nobel Lecture PDFs **[COMPLETE]**

**Goal:**
Extract clean plaintext transcripts and lecture titles from previously downloaded Nobel lecture PDFs, and write the cleaned text to `.txt` files. **The script does not update the corresponding laureate entry in `nobel_literature.json` with the extracted title. This is the intended and confirmed behavior.**

**Implementation Steps:**
1. **Iterate over PDFs:** For each `.pdf` in `data/nobel_lectures_pdfs/`, extract `year` and `lastname` from the filename.
2. **Heuristic Page Filtering:** Use content heuristics to skip noise/fluff pages (e.g., copyright, title, very short pages). Do not always skip the first N pages.
3. **Title Extraction:** Detect the lecture title using patterns (e.g., `Name: Title`, or a short, capitalized line). Extract the title as a separate field.
4. **Text Extraction:** Concatenate the main essay content from the first signal page onward. Clean the text with `clean_speech_text()`.
5. **Write .txt File:** Write the title as the first line of the `.txt` file in `data/nobel_lectures/{year}_{lastname}.txt`, followed by the essay content.
6. **Logging:** Log extraction results, skipped pages, detected titles, and any issues.
7. **Optional Flags:** Allow a `--force` flag to overwrite existing `.txt` files. Optionally allow deletion of PDFs after extraction.
8. **Testing:** Use known PDFs (e.g., Glück, Ishiguro, Han) as test fixtures. Validate line count, formatting, and presence of content. Log empty or unreadable pages for review.

**Note:** The script does **not** update `nobel_literature.json` with the lecture title. This is the intended and confirmed behavior as of June 2025.

This ensures robust, idempotent, and production-ready extraction and plaintext output for Nobel lecture PDFs.

---

## Task 14 – Incremental Update for Nobel Literature JSON **[COMPLETE]**

**Goal:**
Prevent full overwrite of `nobel_literature.json` on each scrape. Instead, merge new/updated records into the existing file.

**Status:** Complete. Implemented in `scraper/scrape_literature.py` as of June 2025.

**Implementation:**
- Loads existing JSON if present
- Merges new/updated records by `(year_awarded, full_name)`
- Preserves old values for any fields missing in the new scrape (does not overwrite with null)
- Logs a warning if a non-null field is overwritten
- Adds/updates a `last_updated` ISO 8601 timestamp per laureate
- Backs up the old file with a timestamp before writing (e.g., `nobel_literature.json.2025-06-10T12-00-00Z.bak`)
- Writes the merged result

This ensures that manual corrections and additional metadata are preserved, and that partial or repeated scrapes are safe and idempotent.

## Task 15 – Add Nobel Lecture Title to JSON from Extracted Text Files **[COMPLETE]**

**Status:** Complete. Implemented as `utils/add_lecture_titles_to_json.py` (June 2025).

**Goal:**
For each laureate who delivered a Nobel lecture, add the lecture title to their entry in `nobel_literature.json` by extracting the first line from the corresponding `.txt` file in `data/nobel_lectures/`.

**Implementation:**
- Script: `utils/add_lecture_titles_to_json.py` (CLI, documented in `utils/README.md`)
- For each laureate with `lecture_delivered: true`, reads the first line of the `.txt` file as the title and updates the JSON.
- Supports `--dry-run` and `--force` flags, year/name filters, and logs all actions.
- Backs up the original JSON before writing changes.
- Idempotent and safe to rerun; only updates missing or changed titles unless `--force` is used.
- Prints found titles to the terminal as it runs.

**Completion Note:**
Task 15 is complete. The script is implemented, tested, and documented. All lecture titles can now be safely and incrementally added to the main JSON file from extracted text files.

---

## Task 16 – Cost Monitoring **[COMPLETE]**

**Status:** Complete.

**Goal:**
Track and log token usage and estimated cost for each OpenAI API call.

**File:**
`rag/query_engine.py`

**Input:**
User query, retrieved chunks, prompt, OpenAI response

**Output:**
Logged JSON per query with token count and cost estimate

**Instructions:**
- Use `tiktoken` to estimate prompt token count before the API call.
- Read `completion_tokens` from the OpenAI response for output count.
- Calculate estimated cost using a model-based rate table (e.g., $0.0015/1K for gpt-3.5).
- Log total tokens, breakdown (prompt vs completion), model, and estimated $USD.
- Include user query and chunk count in the log output.
- Write logs in structured JSON (to stdout or a rotating file).
- Guard against missing `OPENAI_API_KEY` and handle errors cleanly.
- Support dry_run mode with mocked token and cost values.

### Task NN – Support Scoped Thematic Queries **[COMPLETE]**

**File(s)**:  
- `rag/intent_classifier.py`  
- `rag/query_router.py`  
- `embeddings/chunk_text.py` (if chunk metadata needs adjustment)

**Goal**:  
Handle hybrid queries where a thematic concept is asked **within the scope of a specific laureate**, e.g.:

> "What did Toni Morrison say about justice?"

This should retrieve only chunks authored by **Toni Morrison**, while still using the **thematic prompt template**.

---

**Inputs**:  
- User query (e.g., `"What did Toni Morrison say about justice?"`)

**Outputs**:  
- Uses thematic prompt template  
- Retrieves top-k chunks **only from the scoped laureate**

---

**Steps**:

1. **Update Intent Classifier**
   - If a query includes both a thematic keyword **and** a known laureate name, add a new key:
     ```python
     {
       "intent": "thematic",
       "scoped_entity": "Toni Morrison"
     }
     ```
   - Use laureate name list from `nobel_literature.json` or metadata schema.

2. **Update Query Router**
   - If `intent == "thematic"` and `"scoped_entity"` is present:
     - Set `retrieval_config.filters = {"laureate": scoped_entity}`
     - Use thematic prompt template (no change)

3. **Verify Retrieval Layer**
   - Ensure that chunk metadata includes `"laureate"` name (full or normalized)
   - If missing, update `chunk_text.py` to embed this field in every chunk

4. **Testing**
   - Add test queries like:
     - `"What did Gabriel García Márquez say about solitude?"`
     - `"What did Bob Dylan say about music?"`
   - Confirm that:
     - Retrieval is limited to that laureate
     - Output remains thematically formatted

5. **Docs**
   - Update `rag/README.md` to describe the new hybrid routing behavior.

---

**Completion Note:**
- Intent classifier now detects both full and last name laureate scoping for thematic queries and returns a `scoped_entity`.
- Query router applies laureate filter for such queries and uses the thematic prompt template.
- Retrieval and prompt logic updated to support hybrid queries.
- Comprehensive tests and documentation added.
- All requirements for scoped thematic queries are met and verified.
