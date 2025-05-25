"""
Utility to find 'noisy' lecture files in data/nobel_lectures/ that contain a known 'not found' template, are empty, or contain only a placeholder header.
Optionally deletes them with --delete flag.
"""
import os
import logging
from typing import List, Tuple
import argparse

logging.basicConfig(level=logging.INFO)

NOT_FOUND_TEMPLATE = [
    "Nobel Prizes 2024\n",
    "\n",
    "You can also use the Search below or browse from the Homepage to find the information you need.\n"
]
HEADER_ONLY = "Nobel Prizes 2024"


def check_noisy_file(filepath: str) -> Tuple[bool, str]:
    """
    Check if a file is noisy and return (is_noisy, reason).
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        content = ''.join(lines).strip()
        if len(lines) == 0 or content == '':
            return True, "Empty file"
        # Robustly check for the 'not found' template, ignoring line endings and whitespace
        stripped_lines = [line.strip() for line in lines if line.strip()]
        stripped_template = [line.strip() for line in NOT_FOUND_TEMPLATE if line.strip()]
        if stripped_lines == stripped_template:
            return True, "Not found template (robust match)"
        # Alternatively, check for key phrases in the content
        if HEADER_ONLY in content and "You can also use the Search" in content:
            return True, "Not found template (content match)"
        if content == HEADER_ONLY:
            return True, "Header only ('Nobel Prizes 2024')"
    return False, ""


def find_noisy_lecture_files(directory: str) -> List[Tuple[str, str]]:
    """
    Scan all .txt files in the given directory and return those matching noisy patterns.
    Returns a list of (filename, reason) tuples.
    """
    noisy_files = []
    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            filepath = os.path.join(directory, filename)
            is_noisy, reason = check_noisy_file(filepath)
            if is_noisy:
                noisy_files.append((filename, reason))
    return noisy_files


def main():
    parser = argparse.ArgumentParser(description="Find and optionally delete noisy lecture files.")
    parser.add_argument('--delete', action='store_true', help='Delete noisy files after listing them')
    args = parser.parse_args()

    directory = os.path.join(os.path.dirname(__file__), '..', 'data', 'nobel_lectures')
    noisy_files = find_noisy_lecture_files(directory)
    if noisy_files:
        logging.info("Noisy lecture files found:")
        for file, reason in noisy_files:
            print(f"{file}: {reason}")
        if args.delete:
            for file, _ in noisy_files:
                filepath = os.path.join(directory, file)
                try:
                    os.remove(filepath)
                    print(f"Deleted: {file}")
                except Exception as e:
                    print(f"Failed to delete {file}: {e}")
    else:
        logging.info("No noisy lecture files found.")


if __name__ == "__main__":
    main() 