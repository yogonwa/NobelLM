import os
import json
import requests
from bs4 import BeautifulSoup
from typing import Dict
import logging

FACTS_INPUT_JSON = "data/nobel_literature_facts_urls.json"
OUTPUT_JSON = "data/nobel_literature.json"
SPEECH_DIR = "data/literature_speeches"
CEREMONY_DIR = "data/ceremony_speeches"

os.makedirs(SPEECH_DIR, exist_ok=True)
os.makedirs(CEREMONY_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_life_and_work_blurbs(soup: BeautifulSoup) -> Dict[str, str]:
    blurbs = {"life_blurb": "", "work_blurb": ""}
    for section in soup.find_all("div", class_="description border-top"):
        heading = section.find("h3")
        if heading:
            title = heading.get_text(strip=True).lower()
            if title in ["life", "work"]:
                blurbs[f"{title}_blurb"] = " ".join(
                    p.get_text(strip=True) for p in section.find_all("p") if p.get_text(strip=True)
                )
    return blurbs

def infer_gender_from_text(text: str) -> str | None:
    text = text.lower()
    if " he " in text or " his " in text:
        return "Male"
    elif " she " in text or " her " in text:
        return "Female"
    return None

def extract_metadata(soup: BeautifulSoup) -> Dict[str, str | None]:
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
        data["date_of_birth"] = parts[0]
        if len(parts) > 1:
            data["place_of_birth"] = parts[1]

    dod_tag = soup.select_one("p.dead-date")
    if dod_tag:
        data["date_of_death"] = dod_tag.get_text(strip=True).replace("Died: ", "")

    for p in soup.select("div.content p"):
        text = p.get_text(strip=True)
        if "Prize motivation:" in text:
            data["prize_motivation"] = text.replace("Prize motivation:", "").strip(' "')
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

def fetch_and_save_speech(url: str, save_path: str, label: str) -> str | None:
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            logger.warning(f"{label} not found at {url} (status {response.status_code})")
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        article = soup.find("div", class_="article-body")
        if not article:
            logger.warning(f"{label} article-body not found at {url}")
            return None
        text = article.get_text(separator="\n").strip()
        if not text:
            logger.warning(f"{label} text empty at {url}")
            return None
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(text)
        return text
    except Exception as e:
        logger.error(f"Exception fetching {label} at {url}: {e}")
        return None

def main():
    with open(FACTS_INPUT_JSON, "r", encoding="utf-8") as f:
        laureates = json.load(f)

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

        # Fetch Nobel lecture (speech)
        speech_url = facts_url.replace("/facts/", "/speech/")
        speech_path = os.path.join(SPEECH_DIR, f"{year}_{lastname}.txt")
        nobel_lecture_text = fetch_and_save_speech(speech_url, speech_path, label="Nobel lecture")

        # Fetch ceremony speech (announcement)
        ceremony_url = f"https://www.nobelprize.org/prizes/literature/{year}/ceremony-speech/"
        ceremony_path = os.path.join(CEREMONY_DIR, f"{year}.txt")
        ceremony_speech_text = fetch_and_save_speech(ceremony_url, ceremony_path, label="Ceremony speech")

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
                    "nobel_lecture_text": nobel_lecture_text,
                    "ceremony_speech_text": ceremony_speech_text,
                    "declined": declined,
                    "specific_work_cited": specific_work_cited,
                    "cited_work": cited_work
                }
            ]
        }

        results.append(record)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
