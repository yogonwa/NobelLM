import re
from typing import Optional

def clean_speech_text(raw_text: str) -> str:
    """
    Cleans raw Nobel ceremony speech text by:
    - Removing translator and source notes
    - Normalizing whitespace and punctuation
    - Stripping HTML artifacts or annotation lines

    Args:
        raw_text (str): The raw text scraped from the website

    Returns:
        str: Cleaned, normalized plain text
    """
    text = raw_text.strip()

    # Remove common footnote sections (translated by, source references)
    text = re.sub(r"\*Translated.*?(View with a Grain of Sand|From Les Prix Nobel).*", "", text, flags=re.IGNORECASE | re.DOTALL)

    # Remove any inline footnotes or bracketed source info
    text = re.sub(r"\[[^\]]{0,80}?\]", "", text)  # up to 80-char footnotes

    # Replace curly quotes and dashes with standard ones
    replacements = {
        "“": '"', "”": '"',
        "‘": "'", "’": "'",
        "–": "-", "—": "-",
        "…": "...",
        "\xa0": " ",  # non-breaking space
    }
    for smart, plain in replacements.items():
        text = text.replace(smart, plain)

    # Collapse multiple spaces/newlines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" +\n", "\n", text)
    text = re.sub(r"\n +", "\n", text)

    # Trim any remaining leading/trailing newlines
    return text.strip()
