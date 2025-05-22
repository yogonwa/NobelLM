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

