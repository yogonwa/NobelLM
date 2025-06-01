"""
Utility script to clean up ceremony speech text files in data/ceremony_speeches.
Removes content from the line containing 'to cite this section' (case-insensitive) onward.
Only rewrites files if changed. Logs actions and summary.
"""
import os
import logging
from typing import List
import re

FOLDER = "data/ceremony_speeches"
CUTOFF_TEXT = "to cite this section"  # case-insensitive match
PRESENTATION_PATTERN = re.compile(r"^Presentation Speech by.*", re.IGNORECASE)
TRANSLATION_PATTERN = re.compile(r"^translation from.*", re.IGNORECASE)
GREETINGS_PATTERNS = [
    re.compile(r"^your majesties.*", re.IGNORECASE),
    re.compile(r"^your royal highnesses.*", re.IGNORECASE),
    re.compile(r"^ladies and gentlemen.*", re.IGNORECASE),
]

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

def clean_file(path: str) -> bool:
    """
    Cleans a ceremony speech file by removing content from the cutoff text onward,
    and removes lines matching presentation, translation, or greeting patterns.
    Returns True if the file was changed and rewritten, False otherwise.
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cleaned_lines: List[str] = []
    for line in lines:
        if CUTOFF_TEXT in line.lower():
            break  # stop here, discard this line and everything after
        if PRESENTATION_PATTERN.match(line.strip()):
            continue
        if TRANSLATION_PATTERN.match(line.strip()):
            continue
        if any(pat.match(line.strip()) for pat in GREETINGS_PATTERNS):
            continue
        cleaned_lines.append(line)

    if len(cleaned_lines) < len(lines):
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(cleaned_lines)
        logging.info(f"Cleaned: {os.path.basename(path)}")
        return True
    logging.debug(f"Skipped (no change): {os.path.basename(path)}")
    return False

def main() -> None:
    """
    Cleans all .txt files in the ceremony speeches folder.
    Logs a summary of cleaned and skipped files.
    """
    cleaned = 0
    skipped = 0

    for fname in os.listdir(FOLDER):
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(FOLDER, fname)
        try:
            if clean_file(path):
                cleaned += 1
            else:
                skipped += 1
        except Exception as e:
            logging.error(f"Error processing {fname}: {e}")

    logging.info(f"\n✅ Cleanup complete: {cleaned} files cleaned, {skipped} skipped.")

if __name__ == "__main__":
    main() 