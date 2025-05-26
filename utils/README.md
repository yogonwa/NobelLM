### extract_pdf_lectures.py

- Extracts lecture title and main text from Nobel lecture PDFs in `data/nobel_lectures_pdfs/`.
- Writes cleaned text to `data/nobel_lectures/{year}_{lastname}.txt` (title as first line).
- **Does not update `nobel_literature.json` with the lecture title.**
- This is the intended and confirmed behavior as of June 2025. 

### add_lecture_titles_to_json.py

- Adds the Nobel lecture title from each `.txt` file in `data/nobel_lectures/` to the corresponding laureate in `data/nobel_literature.json`.
- For each laureate with `lecture_delivered: true`, reads the first line of the `.txt` file as the title and updates the JSON.
- Supports `--dry-run` (show changes, do not write) and `--force` (overwrite existing titles).
- Backs up the original JSON before writing changes.
- Logs all updates, skips, and warnings for missing files or empty titles.
- Idempotent and safe to rerun; only updates missing or changed titles unless `--force` is used.
- Intended for use after extracting lecture text files from PDFs or HTML. 