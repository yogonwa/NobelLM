import os
import re

LECTURES_DIR = "data/nobel_lectures"
HEADER_LINE = "nobel prizes 2024"
TRANSLATION_PATTERN = re.compile(r"^translation from.*", re.IGNORECASE)
GREETINGS_PATTERNS = [
    re.compile(r"^your majesties.*", re.IGNORECASE),
    re.compile(r"^your royal highnesses.*", re.IGNORECASE),
    re.compile(r"^ladies and gentlemen.*", re.IGNORECASE),
]

def clean_file(filepath: str) -> bool:
    """
    Remove the first line if it matches 'Nobel Prizes 2024' (case-insensitive),
    any line that starts with 'Translation from', and any greeting line.
    Returns True if the file was changed.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    new_lines = []
    changed = False
    for i, line in enumerate(lines):
        lstripped = line.strip().lower()
        if i == 0 and lstripped == HEADER_LINE:
            changed = True
            continue
        if TRANSLATION_PATTERN.match(line.strip()):
            changed = True
            continue
        if any(pat.match(line.strip()) for pat in GREETINGS_PATTERNS):
            changed = True
            continue
        new_lines.append(line)
    if changed:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"Cleaned: {os.path.basename(filepath)}")
        return True
    return False

def main():
    changed = 0
    for fname in os.listdir(LECTURES_DIR):
        if fname.endswith(".txt"):
            fpath = os.path.join(LECTURES_DIR, fname)
            if clean_file(fpath):
                changed += 1
    print(f"Done. {changed} files cleaned.")

if __name__ == "__main__":
    main() 