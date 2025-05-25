"""
Utility to confirm that for every Nobel literature laureate with lecture_delivered=true in data/nobel_literature.json,
there is a corresponding .txt file in data/nobel_lectures/.
Reports any missing files.
"""
import os
import json
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)

LITERATURE_JSON = os.path.join(os.path.dirname(__file__), '..', 'data', 'nobel_literature.json')
LECTURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'nobel_lectures')

def load_literature_json(path: str) -> List[Dict]:
    """
    Load the Nobel literature JSON file and return the list of laureate entries.
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def expected_filename(entry: Dict) -> str:
    """
    Given a laureate entry, return the expected lecture filename (e.g., 2024_han.txt).
    Assumes entry has 'year' and 'author_slug' fields.
    """
    year = str(entry['year'])
    author_slug = entry['author_slug']
    return f"{year}_{author_slug}.txt"

def main():
    data = load_literature_json(LITERATURE_JSON)
    missing = []
    for entry in data:
        if entry.get('lecture_delivered') is True:
            fname = expected_filename(entry)
            fpath = os.path.join(LECTURES_DIR, fname)
            if not os.path.isfile(fpath):
                missing.append(fname)
    if missing:
        logging.warning("Missing lecture files for delivered lectures:")
        for fname in missing:
            print(fname)
    else:
        logging.info("All delivered lectures have corresponding text files.")

if __name__ == "__main__":
    main() 