"""
Speech Extraction Utilities for Nobel Laureate Speech Explorer

This module provides functions to extract and clean Nobel lecture titles and transcripts from NobelPrize.org.

Functions:
- clean_speech_text: Remove navigation/footer/UI noise from speech text
- extract_nobel_lecture: Fetch and parse Nobel lecture page, returning title and cleaned transcript
- find_english_pdf_url: Given a Nobel lecture page URL, return the full URL to the English-language PDF if available
- download_pdf: Download a PDF from the given URL and save to save_path

All outputs are cleaned and ready for saving or embedding.
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


def clean_speech_text(text: str) -> str:
    """
    Remove navigation, footer, and UI boilerplate from speech text.
    Strips whitespace, removes empty lines and known noise patterns.
    """
    noise_starts = [
        "back to top",
        "explore prizes and laureates",
        "share this",
        "facebook",
        "linkedin",
        "email this page",
        "x",
        "navigate to:",
        "summary",
        "laureates",
        "facts",
        "biographical",
        "bibliography",
        "nobel lecture",
        "banquet speech",
        "nominations",
        "photo gallery",
        "other resources",
        "award ceremony video",
        "presentation speech",
        "prize announcement",
        "press release",
        "bio-bibliography",
        "award ceremony speech",
        "prize presentation",
        "interview",
        "prose",
        "nobel diploma",
        "article",
        "documentary",
        "speed read",
        "banquet video",
        "your browser does not support the video tag.",
        "copyright",
    ]
    lines = [line.strip() for line in text.splitlines()]
    cleaned = []
    for line in lines:
        l = line.strip().lower()
        if not l:
            continue
        if any(l.startswith(noise) for noise in noise_starts):
            continue
        if l in noise_starts:
            continue
        cleaned.append(line.strip())
    return "\n".join(cleaned).strip()


def extract_nobel_lecture(url: str, min_words: int = 50) -> Dict[str, Optional[str]]:
    """
    Fetch and extract the Nobel lecture title and transcript from the given URL.
    Cleans the transcript and removes unwanted DOM elements.
    Returns a dict with 'nobel_lecture_title' and 'nobel_lecture_text'.
    Logs a warning if content is missing or too short.
    min_words: Minimum number of words required for transcript to be considered valid (default 50).
    """
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Nobel lecture page not found at {url} (status {response.status_code})")
            return {"nobel_lecture_title": None, "nobel_lecture_text": None}
        soup = BeautifulSoup(response.text, "html.parser")
        # Remove unwanted DOM elements
        for selector in [".article-video", ".article-tools", "footer", "nav"]:
            for tag in soup.select(selector):
                tag.decompose()
        # Extract title
        title_tag = soup.select_one("h2.article-header__title")
        title = title_tag.get_text(strip=True) if title_tag else None
        # Extract transcript
        body_tag = soup.select_one("div.article-body")
        transcript = body_tag.get_text(separator="\n").strip() if body_tag else None
        transcript = clean_speech_text(transcript) if transcript else None
        if not transcript or len(transcript.split()) < min_words:
            logger.warning(f"Nobel lecture transcript missing or too short at {url}")
            transcript = None
        return {"nobel_lecture_title": title, "nobel_lecture_text": transcript}
    except Exception as e:
        logger.error(f"Exception extracting Nobel lecture at {url}: {e}")
        return {"nobel_lecture_title": None, "nobel_lecture_text": None}


def find_english_pdf_url(lecture_url: str) -> Optional[str]:
    """
    Given a Nobel lecture page URL, return the full URL to the English-language PDF if available.
    Looks for <a> tags where:
      - href ends with .pdf
      - text includes 'english' (case-insensitive)
      - href contains 'lecture'
    Returns the absolute URL or None if not found.
    """
    try:
        response = requests.get(lecture_url, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Lecture page not found at {lecture_url} (status {response.status_code})")
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True).lower()
            if href.lower().endswith(".pdf") and "lecture" in href.lower() and "english" in text:
                # Normalize relative URLs
                if href.startswith("/"):
                    return f"https://www.nobelprize.org{href}"
                elif href.startswith("http"):
                    return href
        logger.info(f"No English PDF found at {lecture_url}")
        return None
    except Exception as e:
        logger.error(f"Exception finding English PDF at {lecture_url}: {e}")
        return None


def download_pdf(url: str, save_path: str) -> bool:
    """
    Download a PDF from the given URL and save to save_path.
    Returns True if successful, False otherwise.
    """
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200 and response.headers.get("content-type", "").startswith("application/pdf"):
            with open(save_path, "wb") as f:
                f.write(response.content)
            logger.info(f"Downloaded PDF: {save_path}")
            return True
        else:
            logger.warning(f"Failed to download PDF from {url} (status {response.status_code})")
            return False
    except Exception as e:
        logger.error(f"Exception downloading PDF from {url}: {e}")
        return False 