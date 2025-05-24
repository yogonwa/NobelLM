"""
Extract Nobel Lecture Titles and Main Text from PDFs, Update JSON Metadata

CLI script for Nobel Laureate Speech Explorer.

- Extracts title and main text from PDFs in data/nobel_lectures_pdfs/
- Writes cleaned text to data/nobel_lectures/{year}_{lastname}.txt (title as first line)
- Updates nobel_literature.json with the extracted title (merge, not overwrite)
- Supports --limit, --files, --force, and --dry-run flags
- Logs all actions and backs up JSON before writing

Usage:
    python -m utils.extract_pdf_lectures [--limit N] [--files file1.pdf ...] [--force] [--dry-run]
"""
import os
import sys
import argparse
import logging
import json
import shutil
from datetime import datetime, timezone
from typing import List, Optional
import fitz  # PyMuPDF
import re

PDF_DIR = "data/nobel_lectures_pdfs"
TXT_DIR = "data/nobel_lectures"
JSON_PATH = "data/nobel_literature.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("extract_pdf_lectures")

def backup_json(json_path: str) -> Optional[str]:
    if not os.path.exists(json_path):
        return None
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    backup_path = f"{json_path}.{ts}.bak"
    shutil.copy2(json_path, backup_path)
    logger.info(f"Backed up {json_path} to {backup_path}")
    return backup_path

def extract_title_and_text_from_pdf(pdf_path: str, lastname: str = None) -> (Optional[str], Optional[str]):
    try:
        doc = fitz.open(pdf_path)
        title = None
        text_blocks = []
        # --- Step 1: Always try to extract title from page 1 ---
        if doc.page_count > 0:
            page1 = doc[0]
            page1_text = page1.get_text().strip()
            lines = [l.strip() for l in page1_text.splitlines() if l.strip()]
            # If lastname is provided, look for 'Lastname:' pattern
            if lastname:
                for line in lines:
                    if f"{lastname.lower()}:" in line.lower():
                        after_colon = line.split(":", 1)[-1].strip()
                        if after_colon:
                            title = after_colon
                            break
            # If not found, use first non-empty line as title if reasonable
            if not title:
                for line in lines:
                    if 3 < len(line) < 120:
                        title = line
                        break
        # --- Step 2: Main text from page 2 onward (skip short/fluff pages, remove page numbers) ---
        for i in range(1, doc.page_count):
            page = doc[i]
            page_text = page.get_text().strip()
            if not page_text or len(page_text.split()) < 20:
                continue
            # Remove lines that are just numbers (page numbers)
            filtered_lines = [l for l in page_text.splitlines() if not re.fullmatch(r"\d+", l.strip())]
            filtered_text = "\n".join(filtered_lines).strip()
            if filtered_text:
                text_blocks.append(filtered_text)
        # Fallback: If no title found, use old heuristic (first short, capitalized line in any non-fluff page)
        if not title:
            for i, page in enumerate(doc):
                page_text = page.get_text().strip()
                if not page_text or len(page_text.split()) < 20:
                    continue
                lines = [l.strip() for l in page_text.splitlines() if l.strip()]
                for line in lines[:5]:
                    if 5 < len(line) < 80 and line == line.title() and not line.isupper():
                        title = line
                        break
                if title:
                    break
        main_text = "\n\n".join(text_blocks).strip() if text_blocks else None
        logger.debug(f"Extracted title: {title}")
        logger.debug(f"Extracted text length: {len(main_text.split()) if main_text else 0}")
        return title, main_text
    except Exception as e:
        logger.error(f"Error extracting from {pdf_path}: {e}")
        return None, None

def update_json_with_title(json_path: str, year: str, lastname: str, title: str, dry_run: bool = False) -> bool:
    if not os.path.exists(json_path):
        logger.error(f"JSON file not found: {json_path}")
        return False
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    updated = False
    for rec in data:
        if str(rec.get("year_awarded")) == str(year) and lastname.lower() in rec.get("full_name", "").lower():
            old_title = rec.get("nobel_lecture_title")
            if old_title != title:
                logger.info(f"Updating title for {rec['full_name']} ({year}): '{old_title}' -> '{title}'")
                rec["nobel_lecture_title"] = title
                rec["last_updated"] = datetime.now(timezone.utc).isoformat()
                updated = True
            break
    if updated and not dry_run:
        backup_json(json_path)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return updated

def write_txt_file(txt_path: str, title: str, text: str, force: bool = False, dry_run: bool = False) -> bool:
    if os.path.exists(txt_path) and not force:
        logger.info(f"File exists, skipping (use --force to overwrite): {txt_path}")
        return False
    if dry_run:
        logger.info(f"[Dry run] Would write: {txt_path}")
        return True
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"{title}\n\n{text.strip()}\n")
    logger.info(f"Wrote: {txt_path}")
    return True

def parse_pdf_filename(filename: str) -> Optional[tuple]:
    # Expecting {year}_{lastname}.pdf
    base = os.path.splitext(filename)[0]
    parts = base.split("_", 1)
    if len(parts) != 2:
        return None
    year, lastname = parts
    return year, lastname

def main():
    parser = argparse.ArgumentParser(description="Extract lecture titles and text from Nobel PDFs.")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N PDFs.")
    parser.add_argument("--files", nargs="*", default=None, help="Only process these PDF files.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing .txt files.")
    parser.add_argument("--dry-run", action="store_true", help="Log actions but do not write files.")
    args = parser.parse_args()

    pdf_files = sorted([f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")])
    if args.files:
        pdf_files = [f for f in pdf_files if f in args.files]
    if args.limit is not None:
        pdf_files = pdf_files[:args.limit]
    if not pdf_files:
        logger.warning("No PDF files to process.")
        return

    for pdf_file in pdf_files:
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        parsed = parse_pdf_filename(pdf_file)
        if not parsed:
            logger.warning(f"Skipping unrecognized filename: {pdf_file}")
            continue
        year, lastname = parsed
        txt_path = os.path.join(TXT_DIR, f"{year}_{lastname}.txt")
        title, text = extract_title_and_text_from_pdf(pdf_path, lastname=lastname)
        if not title or not text or len(text.split()) < 50:
            logger.warning(f"Extraction failed or too short for {pdf_file}")
            continue
        write_txt_file(txt_path, title, text, force=args.force, dry_run=args.dry_run)
        updated = update_json_with_title(JSON_PATH, year, lastname, title, dry_run=args.dry_run)
        if updated:
            logger.info(f"Updated JSON for {year}_{lastname}")
    logger.info("Done.")

if __name__ == "__main__":
    main() 