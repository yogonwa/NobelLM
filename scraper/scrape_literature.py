"""
Nobel Literature Laureate Scraper

This script scrapes and normalizes metadata and speech text for Nobel Prize in Literature laureates.

Inputs:
- data/nobel_literature_facts_urls.json: List of laureate /facts/ page URLs (pre-curated)

Outputs:
- data/nobel_literature.json: Structured list of laureates and their metadata, including:
    - full_name, gender, country, date_of_birth, date_of_death, place_of_birth, prize_motivation, life_blurb, work_blurb, language, nobel_lecture_title, nobel_lecture_text, ceremony_speech_text, acceptance_speech_text, declined, specific_work_cited, cited_work
- data/literature_speeches/{year}_{lastname}.txt: Nobel lecture text files (one per laureate)
- data/ceremony_speeches/{year}.txt: Ceremony speech text files (one per year)
- data/nobel_lectures/{year}_{lastname}.txt: Nobel lecture title and transcript files (one per laureate)
- data/acceptance_speeches/{year}_{lastname}.txt: Acceptance (banquet) speech text files (one per laureate)

Main Logic:
- Loads laureate URLs from the input JSON
- For each laureate, scrapes metadata, life/work blurbs, and infers gender/country
- Fetches and saves Nobel lecture, ceremony speech, and acceptance (banquet) speech text
- Handles missing or 404 pages with logging and error handling
- Writes all results to a structured JSON file and plain text files

Extraction functions in this module are unit tested in /tests/test_scraper.py
"""
import os
import json
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
import logging
import re
from scraper.speech_extraction import extract_nobel_lecture, find_english_pdf_url, download_pdf
from utils.cleaning import clean_speech_text
import argparse
from datetime import datetime

FACTS_INPUT_JSON = "data/nobel_literature_facts_urls.json"
OUTPUT_JSON = "data/nobel_literature.json"
SPEECH_DIR = "data/literature_speeches"
CEREMONY_DIR = "data/ceremony_speeches"
NOBEL_LECTURE_DIR = "data/nobel_lectures"
ACCEPTANCE_SPEECH_DIR = "data/acceptance_speeches"
NOBEL_LECTURE_PDF_DIR = "data/nobel_lectures_pdfs"

os.makedirs(SPEECH_DIR, exist_ok=True)
os.makedirs(CEREMONY_DIR, exist_ok=True)
os.makedirs(NOBEL_LECTURE_DIR, exist_ok=True)
os.makedirs(ACCEPTANCE_SPEECH_DIR, exist_ok=True)
os.makedirs(NOBEL_LECTURE_PDF_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_date_field(field: str) -> Optional[str]:
    match = re.search(r"(\d{1,2} \w+ \d{4})", field)
    if match:
        try:
            return datetime.strptime(match.group(1), "%d %B %Y").date().isoformat()
        except ValueError:
            return None
    return None

def clean_motivation_text(text: str) -> str:
    text = text.replace(""", '"').replace(""", '"')
    text = re.sub(r",([^\s])", r", \1", text)  # fix ",A" to ", A"
    return text.strip()

def deduplicate_blurb(text: str) -> str:
    paras = text.split('\n\n')
    seen = set()
    unique = []
    for para in paras:
        norm = para.strip()
        if norm and norm not in seen:
            seen.add(norm)
            unique.append(norm)
    return '\n\n'.join(unique)

def extract_life_and_work_blurbs(soup: BeautifulSoup) -> Dict[str, str]:
    blurbs = {"life_blurb": "", "work_blurb": ""}
    for section in soup.find_all("div", class_="description border-top"):
        heading = section.find("h3")
        if heading:
            title = heading.get_text(strip=True).lower()
            if title in ["life", "work"]:
                blurb = " ".join(
                    p.get_text(strip=True) for p in section.find_all("p") if p.get_text(strip=True)
                )
                # Split into paragraphs by double newlines, deduplicate, and join
                blurb = deduplicate_blurb(blurb.replace("\n", "\n\n"))
                blurbs[f"{title}_blurb"] = blurb
    return blurbs

def infer_gender_from_text(text: str) -> Optional[str]:
    """Infer gender from text by searching for male/female pronouns as whole words."""
    text = text.lower()
    if re.search(r'\b(he|his)\b', text):
        return "Male"
    elif re.search(r'\b(she|her)\b', text):
        return "Female"
    return None

def extract_metadata(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    data = {
        "date_of_birth": None,
        "date_of_death": None,
        "place_of_birth": None,
        "prize_motivation": None,
        "language": None,
    }

    dob_tag = soup.select_one("p.born-date")
    if dob_tag:
        dob_text = dob_tag.get_text(strip=True).replace("Born: ", "")
        parts = dob_text.split(", ", 1)
        data["date_of_birth"] = parse_date_field(dob_text)
        if len(parts) > 1:
            data["place_of_birth"] = parts[1].strip()

    dod_tag = soup.select_one("p.dead-date")
    if dod_tag:
        dod_text = dod_tag.get_text(strip=True).replace("Died: ", "").strip()
        data["date_of_death"] = parse_date_field(dod_text)

    for p in soup.select("div.content p"):
        text = p.get_text(strip=True)
        if "Prize motivation:" in text:
            raw_motivation = text.replace("Prize motivation:", "").strip(' "').strip()
            data["prize_motivation"] = clean_motivation_text(raw_motivation)
        elif "Language:" in text:
            data["language"] = text.replace("Language:", "").strip()

    return data

def infer_country(place_of_birth: str | None) -> str | None:
    if place_of_birth and "," in place_of_birth:
        return place_of_birth.split(",")[-1].strip()
    return place_of_birth.strip() if place_of_birth else None

def scrape_facts_page(url: str) -> Dict:
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Failed to fetch {url}")
        return {}
    soup = BeautifulSoup(response.text, "html.parser")
    blurbs = extract_life_and_work_blurbs(soup)
    meta = extract_metadata(soup)
    gender = infer_gender_from_text(blurbs.get("life_blurb", ""))
    country = infer_country(meta.get("place_of_birth"))
    return {**blurbs, **meta, "gender": gender, "country": country}

def extract_speech_text(soup: BeautifulSoup) -> Optional[str]:
    """Try multiple content blocks to extract meaningful speech text."""
    candidates = [
        soup.find("div", class_="article-body"),
        soup.find("div", class_="content"),
        soup.find("main"),
    ]
    for block in candidates:
        if block:
            text = block.get_text(separator="\n").strip()
            if text and len(text.split()) > 50:  # avoid nav/footer junk
                return text
    return None

def fetch_and_save_speech(url: str, save_path: str, label: str) -> str | None:
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            logger.warning(f"{label} not found at {url} (status {response.status_code})")
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        text = extract_speech_text(soup)
        if not text:
            logger.warning(f"{label} text not found or too short at {url}")
            return None
        # Clean the text before saving or returning
        cleaned_text = clean_speech_text(text)
        if not cleaned_text or len(cleaned_text.split()) < 50:
            logger.warning(f"{label} text missing or too short after cleaning at {url}")
            return None
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)
        return cleaned_text
    except Exception as e:
        logger.error(f"Exception fetching {label} at {url}: {e}")
        return None

def fetch_and_save_acceptance_speech(year: int, lastname: str) -> str | None:
    """
    Fetches and saves the laureate's acceptance (banquet) speech if available.
    Returns the cleaned text or None if not found.
    """
    url = f"https://www.nobelprize.org/prizes/literature/{year}/{lastname}/speech/"
    save_path = os.path.join(ACCEPTANCE_SPEECH_DIR, f"{year}_{lastname}.txt")
    return fetch_and_save_speech(url, save_path, label="Acceptance speech")

def extract_html_lecture_text(html: str) -> str:
    """
    Extract lecture title and paragraphs from Nobel lecture HTML fallback.
    Use the second <h2> tag as the lecture title if it exists.
    """
    soup = BeautifulSoup(html, "html.parser")
    h2_tags = soup.find_all("h2")
    if len(h2_tags) >= 2:
        title = h2_tags[1].get_text(strip=True)
    elif h2_tags:
        for h2 in h2_tags:
            title = h2.get_text(strip=True)
            if title:
                break
        else:
            title = "Nobel Lecture"
    else:
        title = "Nobel Lecture"

    article = soup.find("article")
    if not article:
        raise ValueError("No <article> tag found")

    p_tags = article.find_all("p")
    # Always skip the first <p> tag
    filtered_p_tags = p_tags[1:]

    paragraphs = [
        p.get_text(strip=True)
        for p in filtered_p_tags
        if (not p.get("class") or "smalltext" not in p.get("class", []))
        and not p.get_text(strip=True).startswith("To cite this section")
    ]

    return f"{title}\n\n" + "\n\n".join(paragraphs)

def main(input_json: str = FACTS_INPUT_JSON, year: int | None = None):
    with open(input_json, "r", encoding="utf-8") as f:
        laureates = json.load(f)

    # If year is specified, filter laureates to only that year
    if year is not None:
        laureates = [entry for entry in laureates if entry["year"] == year]

    results = []

    # Mapping of (year, lastname) to cited work
    cited_works = {
        (1902, "mommsen"): "A history of Rome",
        (1919, "spitteler"): "Olympian Spring",
        (1920, "hamsun"): "Growth of the Soil",
        (1924, "reymont"): "The Peasants",
        (1929, "mann"): "Buddenbrooks",
        (1932, "galsworthy"): "The Forsyte Saga",
        (1937, "du-gard"): "Les Thibault",
        (1954, "hemingway"): "The Old Man and the Sea",
        (1965, "sholokhov"): "Epic of the Don",
    }

    for entry in laureates:
        year = entry["year"]
        fullname = entry["fullname"]
        lastname = entry["lastname"]
        facts_url = entry["url"]

        logger.info(f"Scraping {fullname} ({year})...")
        scraped = scrape_facts_page(facts_url)

        # Set declined for Pasternak (1958) and Sartre (1964)
        declined = False
        if (year == 1958 and lastname.lower() == "pasternak") or (year == 1964 and lastname.lower() == "sartre"):
            declined = True

        # Set specific_work_cited and cited_work
        key = (year, lastname.lower())
        if key in cited_works:
            specific_work_cited = True
            cited_work = cited_works[key]
        else:
            specific_work_cited = False
            cited_work = None

        # Fetch Nobel lecture (prefer PDF, fallback to HTML)
        lecture_url = f"https://www.nobelprize.org/prizes/literature/{year}/{lastname}/lecture/"
        lecture_pdf_url = find_english_pdf_url(lecture_url)
        lecture_file_path = os.path.join(NOBEL_LECTURE_DIR, f"{year}_{lastname}.txt")
        os.makedirs(NOBEL_LECTURE_DIR, exist_ok=True)
        lecture_text = None
        success = False  # Ensure this is always defined

        if lecture_pdf_url:
            pdf_save_path = os.path.join(NOBEL_LECTURE_PDF_DIR, f"{year}_{lastname}.pdf")
            success = download_pdf(lecture_pdf_url, pdf_save_path)
            if success:
                lecture_text = None  # No text extraction from PDF in this step
            else:
                logger.warning(f"Failed to download PDF for {fullname} ({year}), falling back to HTML.")
        if not lecture_pdf_url or not success:
            # Fallback to HTML extraction
            try:
                html = requests.get(lecture_url, timeout=10).text
                lecture_text = extract_html_lecture_text(html)
                with open(lecture_file_path, "w", encoding="utf-8") as f:
                    f.write(lecture_text)
            except Exception as e:
                logger.warning(f"Failed to extract HTML lecture for {fullname} ({year}): {e}")
                lecture_file_path = None
        else:
            # If PDF was downloaded, still create an empty file to keep the path reference
            with open(lecture_file_path, "w", encoding="utf-8") as f:
                f.write("")

        # Fetch ceremony speech (announcement)
        ceremony_url = f"https://www.nobelprize.org/prizes/literature/{year}/ceremony-speech/"
        ceremony_path = os.path.join(CEREMONY_DIR, f"{year}.txt")
        ceremony_speech_text = fetch_and_save_speech(ceremony_url, ceremony_path, label="Ceremony speech")
        if ceremony_speech_text:
            ceremony_file = ceremony_path
        else:
            # Fallback: Try press release if ceremony speech is missing
            press_release_url = f"https://www.nobelprize.org/prizes/literature/{year}/press-release/"
            press_release_path = os.path.join(CEREMONY_DIR, f"{year}_pressrelease.txt")
            ceremony_speech_text = fetch_and_save_speech(press_release_url, press_release_path, label="Press release fallback")
            if ceremony_speech_text:
                logger.info(f"Using press release as fallback for {year} award announcement")
                ceremony_file = press_release_path
            else:
                ceremony_file = None

        # Fetch acceptance (banquet) speech
        acceptance_speech_text = fetch_and_save_acceptance_speech(year, lastname)
        if acceptance_speech_text:
            acceptance_file = os.path.join(ACCEPTANCE_SPEECH_DIR, f"{year}_{lastname}.txt")
        else:
            acceptance_file = None

        # Store the file path in the JSON output
        nobel_lecture_file = lecture_file_path if os.path.exists(lecture_file_path) else None

        record = {
            "year_awarded": year,
            "category": "Literature",
            "laureates": [
                {
                    "full_name": fullname,
                    "gender": scraped.get("gender"),
                    "country": scraped.get("country"),
                    "date_of_birth": scraped.get("date_of_birth"),
                    "date_of_death": scraped.get("date_of_death"),
                    "place_of_birth": scraped.get("place_of_birth"),
                    "prize_motivation": scraped.get("prize_motivation"),
                    "life_blurb": scraped.get("life_blurb"),
                    "work_blurb": scraped.get("work_blurb"),
                    "language": scraped.get("language"),
                    "declined": declined,
                    "specific_work_cited": specific_work_cited,
                    "cited_work": cited_work,
                    "nobel_lecture_file": nobel_lecture_file,
                    "ceremony_file": ceremony_file,
                    "acceptance_file": acceptance_file
                }
            ]
        }

        results.append(record)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Nobel Literature laureate data.")
    parser.add_argument(
        "--input",
        type=str,
        default=FACTS_INPUT_JSON,
        help="Path to input JSON file with laureate URLs (default: data/nobel_literature_facts_urls.json)",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="If set, only process laureates for this year. (default: all years)",
    )
    args = parser.parse_args()
    main(args.input, args.year)
