# Scraper Module – Nobel Laureate Speech Explorer

---

## June 2025 Update
- Schema now includes `lecture_delivered` (bool) and `lecture_absence_reason` (string/null) per laureate.
- Scraping pipeline avoids noisy files and records absence reasons in the JSON.
- Utility script for noisy file cleanup is implemented (`utils/find_noisy_lectures.py`).
- All scraping and cleaning tasks are complete and robust.
- See TASKS.md and NOTES.md for incremental update/merge plan (in progress).

---

# Extraction functions in this module are tested in /tests/test_scraper.py

This folder contains scripts for collecting and structuring Nobel Prize data from NobelPrize.org. All scraping logic for metadata, speeches, and facts is organized here.

## Task 1 – Literature Prize Winner URLs (Complete)
- The extraction of laureate `/facts/` URLs was completed via manual curation.
- The canonical list is now stored in `nobel_literature_facts_urls.json`.
- Previous scripts for scraping and HTML dumping have been removed.

## Task 2 – Scrape Laureate Metadata, Lecture, and Ceremony Speech
- The pipeline will now use `nobel_literature_facts_urls.json` as the input for all laureate `/facts/` URLs.
- See `TASKS.md` for details on required fields and outputs.

## Output Schema (per laureate)
- `full_name`: Laureate's full name
- `date_of_birth`: Date of birth
- `date_of_death`: Date of death (nullable)
- `place_of_birth`: Place of birth (city, country, etc.)
- `country`: Inferred from `place_of_birth`
- `gender`: Gender, inferred from pronouns in life blurb
- `prize_motivation`: Prize motivation text
- `life_blurb`: Life summary
- `work_blurb`: Work summary
- `language`: Primary language (from facts page)
- `declined`: Whether the prize was declined
- `specific_work_cited`: Whether a specific work was cited
- `cited_work`: Cited work (if specific_work_cited is true)
- `lecture_delivered`: Whether a Nobel lecture was delivered (bool)
- `lecture_absence_reason`: Reason if no lecture was delivered (string/null)
- Optionally: `nobel_lecture_file`, `ceremony_file`, `acceptance_file` (paths to text files)

## Outputs
- `data/nobel_literature.json`: Structured list of laureates and their metadata, including all fields above
- `data/nobel_lectures/{year}_{lastname}.txt`: Nobel lecture transcript files (one per laureate, extracted from PDF or HTML)
- `data/ceremony_speeches/{year}.txt`: Ceremony speech files (one per year)
- `data/acceptance_speeches/{year}_{lastname}.txt`: Acceptance (banquet) speech files (one per laureate)

## Notes
- All scripts are designed to be idempotent and modular.
- `country` is inferred from the last part of `place_of_birth`.
- See `TASKS.md` for the latest task progress and instructions.

# Testing
Extraction/parsing logic is covered by unit tests in /tests/test_scraper.py. Run `pytest` from the project root to execute tests.

---

All scripts in this folder follow project conventions for modularity, logging, and idempotency. See `.cursorrules` for style and architectural guidelines.

## Speech Types
- **Ceremony Speech:** Official presentation speech by the Swedish Academy (by year)
- **Acceptance Speech:** Laureate's own banquet/acceptance speech (by laureate)
- **Nobel Lecture:** Laureate's formal lecture (by laureate)

## Text Cleanup
All extracted text (lecture, ceremony, acceptance) is processed with a shared utility:
- `clean_speech_text()` removes navigation, UI, and boilerplate noise.
- `normalize_whitespace()` ensures no extra spaces before punctuation, collapses whitespace, and normalizes newlines for clean, readable output.

All debug prints have been removed from the extraction pipeline. Outputs are now robust, production-ready, and suitable for downstream embedding and search.

## Schema Example
```
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
      "language": "Czech",
      "declined": false,
      "specific_work_cited": false,
      "cited_work": null,
      "lecture_delivered": true,
      "lecture_absence_reason": null,
      "nobel_lecture_file": "data/nobel_lectures/1984_seifert.txt",
      "ceremony_file": "data/ceremony_speeches/1984.txt",
      "acceptance_file": "data/acceptance_speeches/1984_seifert.txt"
    }
  ]
}
```

## How to Run
Run the scraper from the project root using:
```
python -m scraper.scrape_literature
```

To run the noisy file cleanup utility:
```
python -m utils.find_noisy_lectures
python -m utils.find_noisy_lectures --delete
```

## Incremental Update & Merge for nobel_literature.json (June 2025)

The scraper now performs robust incremental updates to `nobel_literature.json`:
- Loads existing JSON if present
- Merges new/updated records by `(year_awarded, full_name)`
- Preserves old values for any fields missing in the new scrape (does not overwrite with null)
- Logs a warning if a non-null field is overwritten
- Adds/updates a `last_updated` ISO 8601 timestamp per laureate
- Backs up the old file with a timestamp before writing (e.g., `nobel_literature.json.2025-06-10T12-00-00Z.bak`)
- Writes the merged result

This ensures that manual corrections and additional metadata are preserved, and that partial or repeated scrapes are safe and idempotent. 