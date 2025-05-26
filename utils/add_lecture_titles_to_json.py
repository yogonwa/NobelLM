import argparse
import json
import os
import sys
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.cleaning import clean_speech_text, normalize_whitespace

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
LECTURE_DIR = os.path.join(DATA_DIR, 'nobel_lectures')
JSON_PATH = os.path.join(DATA_DIR, 'nobel_literature.json')


def normalize_last_name(full_name: str) -> str:
    """Normalize last name for file lookup (lowercase, ascii, remove spaces/punctuation)."""
    import unicodedata
    import re
    last = full_name.strip().split()[-1]
    last = unicodedata.normalize('NFKD', last).encode('ascii', 'ignore').decode('ascii')
    last = re.sub(r'[^a-zA-Z0-9]', '', last.lower())
    return last


def get_lecture_txt_path(year: int, full_name: str) -> str:
    """Return expected .txt file path for a laureate's lecture."""
    last = normalize_last_name(full_name)
    return os.path.join(LECTURE_DIR, f"{year}_{last}.txt")


def extract_title_from_txt(txt_path: str) -> Optional[str]:
    """Read the first non-empty line from a .txt file as the title, cleaned and normalized."""
    if not os.path.exists(txt_path):
        return None
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                return normalize_whitespace(clean_speech_text(line))
    return None


def backup_json(json_path: str) -> str:
    """Backup the JSON file with a timestamp."""
    ts = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%SZ')
    backup_path = f"{json_path}.{ts}.bak"
    shutil.copy2(json_path, backup_path)
    return backup_path


def update_lecture_titles(json_path: str, dry_run: bool = False, force: bool = False, year: Optional[int] = None, laureate_filter: Optional[str] = None) -> int:
    """Update the JSON with lecture titles from .txt files. Returns number of updates made."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    updates = 0
    for prize in data:
        if year is not None and prize.get('year_awarded') != year:
            continue
        for laureate in prize.get('laureates', []):
            if not laureate.get('lecture_delivered', False):
                continue
            if laureate_filter and laureate_filter.lower() not in laureate.get('full_name', '').lower():
                continue
            full_name = laureate['full_name']
            y = prize['year_awarded']
            txt_path = get_lecture_txt_path(y, full_name)
            title = extract_title_from_txt(txt_path)
            if not title:
                print(f"[WARN] Missing or empty title for {y} {full_name} at {txt_path}")
                continue
            print(f"[TITLE] {y} {full_name}: '{title}' (from {txt_path})")
            existing = laureate.get('nobel_lecture_title')
            if existing == title and not force:
                continue  # Already set, skip
            action = "[DRY-RUN] Would update" if dry_run else "[UPDATE]"
            print(f"{action} {y} {full_name}: '{existing}' -> '{title}'")
            if not dry_run:
                laureate['nobel_lecture_title'] = title
                laureate['last_updated'] = datetime.utcnow().isoformat()
            updates += 1
    if not dry_run and updates > 0:
        backup = backup_json(json_path)
        print(f"[INFO] Backed up original JSON to {backup}")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Updated {updates} laureate records in {json_path}")
    elif dry_run:
        print(f"[INFO] (Dry run) Would update {updates} laureate records.")
    else:
        print(f"[INFO] No updates needed.")
    return updates


def main():
    parser = argparse.ArgumentParser(description="Add Nobel lecture titles to JSON from .txt files.")
    parser.add_argument('--dry-run', action='store_true', help='Show what would change, do not write.')
    parser.add_argument('--force', action='store_true', help='Overwrite existing titles if present.')
    parser.add_argument('--year', type=int, help='Only update for a specific year.')
    parser.add_argument('--laureate', type=str, help='Only update for laureates matching this name.')
    args = parser.parse_args()

    update_lecture_titles(
        json_path=JSON_PATH,
        dry_run=args.dry_run,
        force=args.force,
        year=args.year,
        laureate_filter=args.laureate
    )

if __name__ == "__main__":
    main() 