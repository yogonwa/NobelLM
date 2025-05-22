# Scraper Module – Nobel Laureate Speech Explorer

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
- `nobel_lecture_text`: Full Nobel lecture text (if available)
- `ceremony_speech_text`: Full ceremony speech text (if available)
- `declined`: Whether the prize was declined
- `specific_work_cited`: Whether a specific work was cited

## Outputs
- `nobel_literature.json`: Structured laureate metadata and speech content
- `literature_speeches/`: Nobel lecture text files
- `ceremony_speeches/`: Ceremony speech text files

## Notes
- All scripts are designed to be idempotent and modular.
- `country` is inferred from the last part of `place_of_birth`.
- See `TASKS.md` for the latest task progress and instructions.

---

All scripts in this folder follow project conventions for modularity, logging, and idempotency. See `.cursorrules` for style and architectural guidelines. 