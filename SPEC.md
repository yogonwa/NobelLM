# Project Specification – Nobel Laureate Speech Explorer

*Last Edited: 5/22/25*

---

## Project Overview

The **Nobel Laureate Speech Explorer** is a data-driven exploration tool designed to collect, analyze, and enable interaction with speeches and metadata from Nobel Prize laureates across all categories (initially focused on Literature). It creates a structured, queryable dataset enriched with metadata and full-text speeches to power semantic search, generative insights, and historical pattern recognition.

---

## Goals

- Build modular, extensible, and maintainable code following best practices
- Scrape and normalize NobelPrize.org metadata and speech text
- Power semantic search and LLM-based Q&A with embeddings and RAG
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
      "nobel_lecture_text": "...",
      "ceremony_speech_text": "...",
      "acceptance_speech_text": "...",
      "declined": false,
      "specific_work_cited": false
    }
  ]
}
```

---

## Outputs

- `nobel_laureates.json` – structured laureate data
- `/acceptance_speeches/{category}/` – plain text Nobel acceptance (banquet) speech files
- `/ceremony_speeches/{category}/` – ceremony speech files
- `metadata.csv` – flattened, filterable metadata
- *Optional:* embeddings, FAISS index, prompt templates
- Public-facing Streamlit UI (HF Spaces)

---

## Tech Stack

- **Language:** Python 3.11+
- **Scraping:** `requests`, `beautifulsoup4`
- **Parsing:** `PyMuPDF`, custom HTML cleaning
- **Storage:** JSON, CSV (optionally: SQLite)
- **Embedding:** `sentence-transformers` (MiniLM); upgradeable to OpenAI Embedding API
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
[FAISS Index] ←→ [Query → GPT-3.5 with retrieved context]
     ↓
[Streamlit UI]
```

---

## Embedding Strategy

- Use `sentence-transformers` locally for speed and cost-free development
- Optional upgrade to `text-embedding-3-small` via OpenAI in Phase 6
- Chunks: 300–500 words, normalized by paragraph boundaries
- Indexed with FAISS (cosine similarity)

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

## Text Cleanup Utility (New)

To ensure consistency and remove navigational clutter, all extracted text blocks (lecture, speech, press release) should be processed with a shared cleanup function.

- **Function:**
  ```python
  def clean_speech_text(text: str) -> str
  ```

- **Cleanup Rules:**
  - Strip whitespace from each line
  - Remove UI or structural noise such as:
    - "Back to top"
    - "Explore prizes and laureates"
    - Empty lines or redundant navigation text

- **Purpose:**
  - Improve clarity of saved `.txt` files
  - Ensure consistency of JSON fields for LLM embedding and search

---