import argparse
import logging
import json
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def validate_jsonl(path: str, required_field: Optional[str] = None) -> None:
    """Validate a JSONL file for JSON correctness and required field presence."""
    total = 0
    valid = 0
    blank = 0
    malformed = 0
    missing_field = 0
    first_error = None
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            total += 1
            line = line.strip()
            if not line:
                blank += 1
                continue
            try:
                obj = json.loads(line)
                valid += 1
                if required_field and required_field not in obj:
                    missing_field += 1
                    if missing_field == 1:
                        logging.warning(f"Line {i} missing required field '{required_field}'")
            except Exception as e:
                malformed += 1
                if not first_error:
                    first_error = (i, line, str(e))
    logging.info(f"Total lines: {total}")
    logging.info(f"Valid JSON lines: {valid}")
    logging.info(f"Blank lines: {blank}")
    logging.info(f"Malformed lines: {malformed}")
    if required_field:
        logging.info(f"Lines missing '{required_field}': {missing_field}")
    if first_error:
        logging.error(f"First malformed line at {first_error[0]}: {first_error[1][:80]}... Error: {first_error[2]}")
    else:
        logging.info("No malformed lines detected.")

def main():
    parser = argparse.ArgumentParser(description="Validate a JSONL file for line-by-line JSON correctness.")
    parser.add_argument("path", help="Path to the JSONL file to validate.")
    parser.add_argument("--required_field", help="Field that must be present in each JSON object.", default=None)
    args = parser.parse_args()
    validate_jsonl(args.path, args.required_field)

if __name__ == "__main__":
    main() 