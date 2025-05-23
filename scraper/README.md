# Scraper Module – Nobel Laureate Speech Explorer

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
- `nobel_lecture_text`: Full Nobel lecture text (if available)
- `ceremony_speech_text`: Full ceremony speech text (if available)
- `acceptance_speech_text`: Full acceptance speech text (if available)
- `declined`: Whether the prize was declined
- `specific_work_cited`: Whether a specific work was cited
- `cited_work`: Cited work (if specific_work_cited is true)

## Outputs
- `data/nobel_literature.json`: Structured list of laureates and their metadata, including:
  - full_name, gender, country, date_of_birth, date_of_death, place_of_birth, prize_motivation, life_blurb, work_blurb, language, nobel_lecture_title, nobel_lecture_text, ceremony_speech_text, acceptance_speech_text, declined, specific_work_cited, cited_work
- `data/nobel_lectures/{year}_{lastname}.txt`: Nobel lecture transcript files (one per laureate)
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

All text is cleaned using the shared `clean_speech_text()` utility.

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
      "nobel_lecture_title": "...",
      "nobel_lecture_text": "...",
      "ceremony_speech_text": "...",
      "acceptance_speech_text": "...",
      "declined": false,
      "specific_work_cited": false,
      "cited_work": null
    }
  ]
}
```

## How to Run
Run `python scraper/scrape_literature.py` from the project root. All outputs will be written to the `data/` directory. 