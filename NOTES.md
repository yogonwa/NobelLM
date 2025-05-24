# Design Notes and Open Questions – Nobel Laureate Speech Explorer

*Last Edited: 5/22/25*

This document tracks decisions, assumptions, and open questions that arise during implementation. Use it as a living reference to align future tasks, architectural choices, and stretch goals.

---

## Prompt Design (RAG)
- **Decision:** Use minimal wrapping — retrieved chunks will be inserted directly into prompt.
- No strict citation format in MVP (e.g., no footnote linking). Keep answers readable.
- **Chunks retrieved:** Top 3 based on cosine similarity.
- **Optional Later:** Add quote-level references or sentence-level source mapping.

---

## Speech Text Cleanup
- **Decision:** Store both raw and cleaned versions.
  - `raw_text`: extracted HTML with minimal processing
  - `clean_text`: cleaned plain text for embedding
- **Cleaning strategy:** Remove line breaks, HTML tags, and translator annotations (as feasible).
- Add cleaning logic as a helper in `utils/cleaning.py`

---

## Error Handling
- **Scraper:**
  - Log errors and skip laureates when page structure is broken or missing.
  - Avoid crashing the full pipeline.
- **LLM/OpenAI:**
  - Raise error with meaningful message if OpenAI API call fails.
  - Consider exponential backoff/retry strategy later.

---

## CLI vs Module Execution
- **Decision:** Each module will have a basic CLI entry point (optional argparse).
- **Format:**
  ```python
  if __name__ == "__main__":
      main()
  ```
- This enables quick manual runs while keeping testable logic in functions.

---

## UI Design (Open)
- **Unresolved:** How interactive vs minimalist should the MVP Streamlit app be?
  - **Option A:** One input box + answer + sources (Claude-style)
  - **Option B:** Add filters (category, year, gender) or search history
- **Tentative Decision:** Start with Option A for MVP, with scaffolding to expand UI later.
- **Design Tip:** Include a section for pre-filled example queries for UX guidance.

---

## Metadata Fields
- **Confirmed:** Additional metadata will be included in `nobel_literature.json` and `metadata.csv`, including:
  - `date_of_birth`, `date_of_death`, `place_of_birth`
  - `prize_motivation`, `life_blurb`, `work_blurb`
- **Deferred:** `share` field will not be normalized yet due to structural ambiguity.

---

## Post-MVP Considerations

### Phase 5b – Additional Categories
- Reuse the literature pipeline for Peace and other categories
- Ensure data schema stays consistent

### Phase 6 – Embedding Migration (OpenAI)
- Evaluate `text-embedding-3-small` vs MiniLM
- Switch from local to OpenAI via `.env` and conditional logic

### Phase 6+ – Long-Term Explorations
- Prompt suggestion engine (Claude-style autosuggestions)
- Timeline visualization by decade or theme
- Topic modeling (e.g., BERTopic, KeyBERT)
- Session memory or persistent chat context
- RAG benchmarking or logging using Weights & Biases

---

Update this file as new questions emerge or implementation decisions are made.

- Extraction/parsing logic is now covered by unit tests in `/tests/test_scraper.py`.
- Whitespace and punctuation normalization is handled by `normalize_whitespace`.
- All debug prints have been removed from the extraction pipeline.
- Outputs are clean, robust, and ready for downstream use.

## RAG Chunking Strategy – Text + Metadata
We extract three types of unstructured text per laureate:

nobel_lecture: Full lecture text (primary source)

acceptance_speech: Brief remarks upon accepting the prize

ceremony_speech: The committee's justification for the award

✅ Inclusion in RAG
All 3 should be embedded, but:

Keep them tagged with a source_type field for context control.

Chunk independently using paragraph-aware logic.

Embed only the cleaned version, but store raw_text separately for audit/debug purposes.

🔍 Chunk Structure
Each chunk should be a JSON object like:
{
  "laureate": "Jaroslav Seifert",
  "year_awarded": 1984,
  "category": "Literature",
  "source_type": "nobel_lecture",
  "text": "Excerpt from the lecture…",
  "chunk_id": "1984_seifert_nobel_lecture_3"
}
🧹 Preprocessing Checklist
Step	Action
HTML stripping	Remove tags from all text sources
Whitespace fix	Normalize line breaks, tabs, spacing
Sentence integrity	Avoid mid-sentence breaks while chunking
Store raw version	Keep raw_text alongside clean_text

🔢 Structured Metadata Usage
Metadata like gender, birthplace, or declined should:

Be stored as separate fields per chunk

Power future filtering and faceted search

Be used in prompt scaffolding (e.g., "From the Czech poet...")

❌ Do not embed metadata inside the unstructured text string.

---

## Data Overwrite vs. Incremental Update (Metadata Integrity)

**Problem:**
Currently, each run of the scraper overwrites the entire `nobel_literature.json` file. This is risky for production/embedding workflows because:
- Any manual corrections or additional metadata are lost.
- Partial re-scrapes (e.g., for a single year) wipe out the rest of the data.
- No history or backup is maintained.

**Solution Idea:**
- Implement an incremental update/merge approach:
  - Load existing JSON if present.
  - Update or add only the records for laureates being scraped.
  - Write back the merged result, preserving all other data.
- Optionally, backup the old file before writing.
- Add a `last_updated` timestamp to each record for traceability.

**Benefits:**
- Robustness for embedding and search pipelines.
- Safe for partial or repeated scrapes.
- Preserves manual edits and metadata.
- Enables future features like versioning or audit trails.

---

## Incremental Update/Merge for Nobel Literature JSON (June 2025)

- The scraper now merges new/updated records into `nobel_literature.json` by `(year_awarded, full_name)`.
- Old values are preserved for any fields missing in the new scrape (no overwrite with null).
- A warning is logged if a non-null field is overwritten.
- Each laureate record gets a `last_updated` ISO 8601 timestamp.
- Before writing, the old file is backed up with a timestamp (e.g., `nobel_literature.json.2025-06-10T12-00-00Z.bak`).
- This logic is implemented in `scraper/scrape_literature.py` as of June 2025.
- Ensures safe, idempotent, and robust updates for downstream workflows and manual corrections.

---

## Recent Updates (June 2025)

- **Schema Extended:**
  - Each laureate now includes `lecture_delivered` (bool) and `lecture_absence_reason` (string/null) in `nobel_literature.json`.
  - This enables downstream filtering and robust metadata for embedding/search.
- **Noisy File Cleanup:**
  - Utility script `utils/find_noisy_lectures.py` detects and (optionally) deletes noisy/empty/placeholder lecture files.
  - Scraper logic now prevents creation of such files and records absence reasons in the JSON.
- **Incremental Update Plan:**
  - See below for the plan to merge new/updated records into the JSON instead of overwriting (Task 14, in progress).
- **Pipeline Robustness:**
  - The scraping pipeline is now robust to missing, empty, or non-existent lectures. All outputs are clean, deduplicated, and ready for downstream use.

---

## Task 13b – PDF Lecture Extraction & JSON Update (Implementation Notes)

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

This ensures robust, idempotent, and production-ready extraction and metadata update for Nobel lecture PDFs.