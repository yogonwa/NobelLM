# Project Specification – Nobel Laureate Speech Explorer

*Last Edited: 6/13/25*

---

## Project Overview

The **Nobel Laureate Speech Explorer** is a data-driven exploration tool designed to collect, analyze, and enable interaction with speeches and metadata from Nobel Prize laureates across all categories (initially focused on Literature). It creates a structured, queryable dataset enriched with metadata and full-text speeches to power semantic search, generative insights, and historical pattern recognition.

---

## Goals

- Build modular, extensible, and maintainable code following best practices
- Scrape and normalize NobelPrize.org metadata and speech text
- Power semantic search and LLM-based Q&A with embeddings and RAG (COMPLETE)
- Enable user exploration through a simple public UI
- Lay foundations for post-MVP features (filtering, charts, memory)

---

## Inputs and Data Sources

- **Master List (Literature):**  
  [https://www.nobelprize.org/prizes/lists/all-nobel-prizes-in-literature/all/](https://www.nobelprize.org/prizes/lists/all-nobel-prizes-in-literature/all/)
- **Facts Page:**  
  `https://www.nobelprize.org/prizes/{category}/{year}/{lastname}/facts/`
- **Lecture Page:**  
  `https://www.nobelprize.org/prizes/{category}/{year}/{lastname}/speech/`
- **Award Speech:**  
  `https://www.nobelprize.org/prizes/{category}/{year}/ceremony-speech/`

---

## Core Data Schema (Example)

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
      "cited_work": null
      // Optionally: "lecture_file": "data/nobel_lectures/1984_seifert.txt",
      // Optionally: "ceremony_file": "data/ceremony_speeches/1984.txt",
      // Optionally: "acceptance_file": "data/acceptance_speeches/1984_seifert.txt"
    }
  ]
}
```

---

## Outputs

- `nobel_laureates.json` – structured laureate data (metadata only, with optional file references)
- `/nobel_lectures/{year}_{lastname}.txt` – plain text Nobel lecture transcript files (from PDF extraction)
- `/ceremony_speeches/{year}.txt` – ceremony speech files
- `/acceptance_speeches/{year}_{lastname}.txt` – acceptance (banquet) speech files
- `metadata.csv` – flattened, filterable metadata
- *Optional:* embeddings, FAISS index, prompt templates
- Public-facing Streamlit UI (HF Spaces)

---

## Tech Stack

- **Language:** Python 3.11+
- **Scraping:** `requests`, `beautifulsoup4`
- **Parsing:** `PyMuPDF`, custom HTML cleaning
- **Storage:** JSON, CSV (optionally: SQLite)
- **Embedding:** `sentence-transformers` (MiniLM, BGE); upgradeable to OpenAI Embedding API
- **Vector Store:** FAISS (local CPU)
- **Frontend:** Streamlit (hosted via Hugging Face Spaces)

---

## Architecture Diagram

```
[NobelPrize.org]
     ↓
[Scraper (category-aware)]
     ↓
[Parser / Normalizer] → [JSON + .txt + metadata.csv]
     ↓
[Chunker + Embedding Model (MiniLM)]
     ↓
[FAISS Index] ←→ [Query → GPT-3.5 with retrieved context] (COMPLETE)
     ↓
[Streamlit UI]
```

---

## Embedding Strategy

- Use `sentence-transformers` locally for speed and cost-free development
- Optional upgrade to `text-embedding-3-small` via OpenAI in Phase 6
- Chunks: Model-aware, token-based chunking (using the tokenizer for the selected model, e.g., 500 tokens for BGE-Large, 250 for MiniLM)
- Optional token overlap between chunks for context continuity (last N tokens of previous chunk are prepended to the next chunk)
- Indexed with FAISS (cosine similarity)
- **macOS Note:** The codebase sets `OMP_NUM_THREADS=1` at startup to prevent segmentation faults when using FAISS and PyTorch together. This is handled automatically as of June 2025.
- **Outputs:**
  - Model-specific chunked JSONL: `/data/chunks_literature_labeled_{model}.jsonl`
  - Model-specific embeddings JSON: `/data/literature_embeddings_{model}.json` (JSON array, each object contains chunk metadata and embedding vector)

### Model-Aware, Config-Driven Pipeline (NEW)

All chunking, embedding, indexing, and RAG operations are now **model-aware and config-driven**. The embedding model, FAISS index, and chunk metadata paths are centrally managed in `rag/model_config.py`:

- To switch models (e.g., BGE-Large vs MiniLM), pass `--model` to any CLI tool, or set `model_id` in your code or UI.
- All file paths, model names, and embedding dimensions are set in one place.
- Consistency checks ensure the loaded model and index match in dimension, preventing silent errors.
- Enables easy A/B testing and reproducibility.

**Example:**
```bash
python -m embeddings.chunk_literature_speeches --model bge-large
python -m embeddings.embed_texts --model bge-large
python -m embeddings.build_index --model bge-large
```

**To add a new model:**
- Add its config to `rag/model_config.py`.
- All downstream code and scripts will pick it up automatically.

---

## Stretch Goals

- Prompt suggestion engine (Claude-style examples)
- Memory/context provider for session-aware follow-ups
- Timeline or cluster visualization by theme, decade, or demographic
- Gender/region topic analysis
- Per-year or per-laureate comparison UX
- RAG evaluation logging (e.g. with Weights & Biases)
- Support for additional categories (Peace, Physics, etc.) in Phase 5b

---

## Deployment Strategy

- Local dev with virtualenv
- Public hosting via Hugging Face Spaces
- `.env` for OpenAI key (optional: HF token for gated models)

---

## License

All source data is public and usage falls under fair use. This is an educational and exploratory AI application.

---

## Notes

- Metadata schema includes rich fields like birth/death dates, motivation, blurbs
- `share` field will be deferred for future inclusion

# Testing
Extraction logic (HTML parsing, gender inference, metadata extraction) is covered by unit tests in `/tests/test_scraper.py`.

---

## Nobel Lecture Extraction (New)

Nobel lectures are a distinct content type from ceremony or banquet speeches and must be handled separately.

- **URL Structure:**
  - `https://www.nobelprize.org/prizes/literature/{year}/{lastname}/lecture/`

- **DOM Extraction Strategy:**
  - **Title:** Extract from `<h2 class="article-header__title">`
  - **Transcript:** Found within `<div class="article-body">`
  - Remove embedded video blocks (`.article-video`), social sharing tools (`.article-tools`), `footer`, and `nav`
  - Clean trailing boilerplate or copyright

- **Output Fields:**
  ```json
  {
    "nobel_lecture_title": "The Nobel Lecture by Jon Fosse",
    "nobel_lecture_text": "Full cleaned transcript here..."
  }
  ```

- **Persistence:**
  - Save transcript to `/data/nobel_lectures/{year}_{lastname}.txt`
  - Include both fields in `nobel_literature.json` output

---

## Text Cleanup Utility (Updated)

All extracted text blocks (lecture, speech, press release) are processed with:
- `clean_speech_text(text: str) -> str`: Removes navigation, UI, and boilerplate noise.
- `normalize_whitespace(text: str) -> str`: Collapses whitespace, removes extra spaces before punctuation, and normalizes newlines for clean, readable output.

All outputs are now robust, debug-free, and suitable for embedding and search.

---

## June 2025 Update
- The schema now includes `lecture_delivered` (bool) and `lecture_absence_reason` (string/null) per laureate.
- The scraping pipeline is robust to missing/empty lectures and does not create noisy files.
- Utility script `utils/find_noisy_lectures.py` is available for cleanup and maintenance.
- Incremental update/merge for `nobel_literature.json` is planned (see NOTES.md and TASKS.md).
- All outputs are clean, deduplicated, and ready for embedding/search.
- Codebase and documentation are up to date as of June 2025.

---

## June 2025 Update – Incremental Update/Merge for Nobel Literature JSON

- The scraper now merges new/updated records into `nobel_literature.json` by `(year_awarded, full_name)`.
- Old values are preserved for missing fields; no overwrite with null.
- Logs a warning if a non-null field is overwritten.
- Each laureate record gets a `last_updated` ISO 8601 timestamp.
- Old file is backed up with a timestamp before writing.
- Implemented in `scraper/scrape_literature.py` as of June 2025.