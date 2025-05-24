# Implementation Plan – Nobel Laureate Speech Explorer

*This document defines the concrete build phases, technical approach, and modular execution plan for the Nobel Laureate Speech Explorer. It supports development via Cursor and tracks modular milestone execution.*

*Last Edited: 5/22/25*

---

## Overall Learning Goal
- Build a full-stack, modular Retrieval-Augmented Generation (RAG) project to:
  - Learn and internalize LLM, embeddings, and vector database concepts through hands-on implementation.
  - Use Cursor AI assistant as a structured pair-programming partner.
  - Gain architectural proficiency with RAG systems, data pipelines, and lightweight UI deployment.

---

## Project Goal
- Create a public-facing tool that:
  - Scrapes NobelPrize.org for metadata, speeches, and facts (starting with Literature category).
  - Normalizes and stores data in a structured format.
  - Enables semantic search via local embeddings + FAISS.
  - Supports LLM-based Q&A via OpenAI (initial) or local models.
  - Provides a simple UI for asking and exploring queries.
  - Modular architecture supports post-MVP features like multi-category support, timeline charts, memory/context, and templated queries.

---

## Constraints and Tradeoffs
- Solo developer project; must prioritize modularity, readability, and testability.
- Local development only with CPU-compatible models; cloud deployment via Hugging Face Spaces.
- Avoid costly dependencies unless strictly necessary.
- Cursor and AI tools must work within clearly scoped tasks with named modules and reusable logic.
- Some fields such as `share` will be deferred initially and revisited post-MVP.

---

## In-Scope Features (MVP)
- Literature category data ingestion
- Text extraction of Nobel lecture and ceremony speeches
- Metadata normalization + JSON/CSV export (including rich metadata fields)
- Sentence embedding using sentence-transformers (MiniLM)
- Vector search via FAISS
- RAG pipeline to answer natural language queries using OpenAI
- Streamlit UI to enter questions and display answers
- Public deployment of MVP demo via Hugging Face Spaces
- **Extract and clean Nobel Lecture transcript and title for each laureate**

### Out-of-Scope (MVP)
- All other Nobel categories (added in Phase 5b)
- Multi-turn chat / persistent memory (MCP)
- Full UI polish, mobile-first layout, advanced filters
- Charts, timeline graphs, or clustering
- Entity detection or speech analytics
- OpenAI embedding model support (Phase 6)
- Handling `share` field for split awards (deferred)

---

## Folder Structure

```
/project-root
├── data/                # Raw data, speech text, embeddings
├── scraper/             # Scraper scripts
├── embeddings/          # Text chunking, vector generation, FAISS index
├── rag/                 # Query pipeline, LLM interfacing
├── frontend/            # Streamlit app UI
├── utils/               # Shared helpers
├── tests/               # Pytest test files
├── .cursorrules         # Cursor execution rules
├── .env.example         # Placeholder for API keys
├── requirements.txt     # Python dependencies
├── IMPLEMENTATION_PLAN.md
├── SPEC.md
├── TASKS.md
├── NOTES.md
```

Each folder should contain a `README.md` file describing:
- The folder's purpose
- Key files and what they do
- How files interact with other modules
- Expected inputs/outputs or side effects

Cursor must update these README files incrementally as it creates or modifies core logic. If new files are added, they must be documented with a short summary of their function, dependencies, and the system components they interface with.

---

## Data Schema Overview

Each record:
```json
{
  "category": "Literature",
  "year_awarded": 1984,
  "laureates": [
    {
      "full_name": "Jaroslav Seifert",
      "gender": "Male",
      "country": "Czech Republic",
      "date_of_birth": "1901-09-23",
      "date_of_death": "1986-01-10",
      "place_of_birth": "Žižkov, Austria-Hungary",
      "prize_motivation": "for his poetry which endowed with freshness...",
      "life_blurb": "...",
      "work_blurb": "...",
      "declined": false,
      "specific_work_cited": false,
      "cited_work": null,
      "lecture_delivered": true,
      "lecture_absence_reason": null
    }
  ]
}
```

---

## Phases & Milestones

### Phase 1 – Scraping & Structuring (M1)
- Scrape Nobel Literature list
- For each prize: scrape facts, lecture, and ceremony pages
- Normalize metadata into structured JSON and CSV
- Store lecture and ceremony text per laureate
- **Fetch and extract lecture title and transcript from /lecture/ pages**
- **Apply shared cleanup utility to remove navigation, footer, and UI noise from text fields**
- **Output:** `/data/nobel_literature.json`, `/data/acceptance_speeches/*.txt`, `metadata.csv`

### Phase 2 – Embedding & Indexing (M2)
- Chunk speech text into 300–500 word blocks
- Generate sentence embeddings (MiniLM)
- Save embeddings as JSON
- Build and persist FAISS index
- **Output:** `/data/literature_embeddings.json`, `/data/faiss_index/`

### Phase 3 – RAG Pipeline (M3)
- Implement query-to-embedding conversion
- Retrieve top-N passages from FAISS
- Construct prompt and call OpenAI (text-davinci or GPT-3.5)
- Return answer and source reference
- **Output:** `query_engine.py`, returns JSON or text response

### Phase 4 – UI & Deployment (M4)
- Build Streamlit interface for input and output
- Optional dropdown for category or metadata filtering (static for now)
- Deploy app using Hugging Face Spaces (via GitHub repo)
- **Output:** `app.py`, live public UI

#### Phase 4b – Chunking & Embedding Prep Strategy

- Prepare chunking logic for all three speech types:
  - `nobel_lecture` (full lecture text)
  - `acceptance_speech` (banquet/acceptance remarks)
  - `ceremony_speech` (committee's justification)
- Tag each chunk with:
  - `source_type` (e.g., nobel_lecture, acceptance_speech, ceremony_speech)
  - `category`
  - `laureate`
  - `year_awarded`
- Store both `raw_text` (original, minimally processed) and `clean_text` (for embedding/audit).
- Keep structured metadata fields (e.g., gender, country, declined) as top-level properties for each chunk.
- **Do not embed metadata inside the unstructured text string.**
- **Output:** Chunked `.jsonl` or `.json` file with tagged, cleaned segments

### Phase 5 – Post-MVP Foundations (M5)
- Add MCP scaffolding: session memory via `st.session_state` or dict
- Introduce `prompt_templates.json` for auto-suggested queries

### Phase 5b – Expand to Other Categories
- Extend scraper and schema normalization for Peace, Physics, etc.
- Validate that RAG pipeline and metadata structure remains compatible

### Phase 6 – Explore OpenAI Embedding Migration
- Replace local MiniLM embeddings with OpenAI's `text-embedding-3-small`
- Update chunk pipeline to stream token-efficient embedding calls

---

## Inputs / Outputs Reference

| Phase | Input                | Output                                      |
|-------|----------------------|---------------------------------------------|
| M1    | NobelPrize.org       | nobel_literature.json, text files, metadata.csv, **/data/nobel_lectures/{year}_{lastname}.txt** (plain text transcript of Nobel lecture, extracted from PDF), **/data/ceremony_speeches/{year}.txt** (ceremony speech), **/data/acceptance_speeches/{year}_{lastname}.txt** (acceptance speech) |
| M2    | Text files           | JSON embeddings, FAISS index                |
| M3    | User query, index    | GPT-3.5 response, citation                  |
| M4    | Streamlit app        | Live public UI on HF Spaces                 |
| M5    | Session, prior query logs | Query suggestions, context filtering   |
| M5b   | Additional category URLs | New JSON and embeddings for other prize types |
| M6    | OpenAI model call    | Updated embedding flow                      |

---

## Cursor Guidance (Execution Principles)
- Use `.cursorrules` as governing file for naming, style, structure
- Always refer to `TASKS.md` for next step
- Never duplicate existing utilities
- Default to modular code split across scoped files (one concern per module)
- All inputs/outputs of each function should be typed and documented
- When creating or editing core functionality, update or create a `README.md` in that folder to describe:
  - Purpose of the folder
  - Description of newly added files or modules
  - How the files interface with other modules
  - Any reusable functions or exported utilities
- **When scraping lecture or speech content:**
  - Use fallback-aware DOM logic from `speech_extraction.py`
  - Always clean the output using `clean_speech_text()` before writing to file or saving in JSON
  - Do not rely solely on class-based selectors like `.article-body` — include fallbacks like `main`, `div.content`

## Unit Testing Extraction Functions
- Add unit tests for `extract_life_and_work_blurbs`, `infer_gender_from_text`, and `extract_metadata` in `scraper/scrape_literature.py`.
- Place tests in `/tests/test_scraper.py`.
- Use static HTML snippets as fixtures.
- Cover normal and edge cases for each function.

- All extraction and cleaning logic is finalized and robust. All debug prints have been removed.
- `normalize_whitespace` is used for punctuation and whitespace normalization on all extracted text.
- Outputs are clean, production-ready, and suitable for embedding, search, and UI display.

---

## June 2025 Update
- Schema now includes `lecture_delivered` and `lecture_absence_reason` fields per laureate.
- Scraping pipeline avoids noisy files and records absence reasons in the JSON.
- Utility script for noisy file cleanup is implemented (`utils/find_noisy_lectures.py`).
- All scraping and cleaning tasks (Tasks 1–13b) are complete and robust.
- Task 14 (incremental update/merge for `nobel_literature.json`) is planned and referenced in TASKS.md and NOTES.md.
- Codebase and documentation are current as of June 2025.

## June 2025 Update – Incremental Update/Merge Implemented

- The scraper now performs incremental updates to `nobel_literature.json` by merging new/updated records by `(year_awarded, full_name)`.
- Old values are preserved for missing fields; no overwrite with null.
- Logs a warning if a non-null field is overwritten.
- Each laureate record gets a `last_updated` ISO 8601 timestamp.
- Old file is backed up with a timestamp before writing.
- Implemented in `scraper/scrape_literature.py` as of June 2025.

## June 2025 – Detailed Plan for Task 13b: PDF Lecture Extraction & JSON Update

- Iterate over all PDFs in `data/nobel_lectures_pdfs/`.
- Use heuristics to skip noise/fluff pages (copyright, title, very short pages). Do not always skip the first N pages.
- Extract the lecture title using patterns (e.g., `Name: Title`, or a short, capitalized line on a content page).
- Concatenate and clean the main essay content from the first signal page onward.
- Write the title as the first line of the `.txt` file in `data/nobel_lectures/{year}_{lastname}.txt`.
- Load `nobel_literature.json`, find the matching laureate by `year_awarded` and `full_name`, and update/add the `nobel_lecture_title` field only (merge, do not overwrite other fields). Optionally update `last_updated`.
- Back up the old JSON file with a timestamp before writing.
- Log extraction results, skipped pages, detected titles, and any issues.
- Allow a `--force` flag to overwrite existing `.txt` files. Optionally allow deletion of PDFs after extraction.
- Use known PDFs as test fixtures for validation. Log empty or unreadable pages for review.

This plan ensures robust, idempotent, and production-ready extraction and metadata update for Nobel lecture PDFs.

---
