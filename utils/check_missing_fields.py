"""
Utility to check for missing critical fields in Nobel literature laureate records.
"""
import json
from typing import List

def find_missing_fields(
    json_path: str,
    critical_fields: List[str] = ["full_name", "gender", "country"]
) -> None:
    """
    Scan the Nobel literature JSON file for laureate records missing critical fields.
    Args:
        json_path: Path to the JSON file.
        critical_fields: List of fields to check for presence and non-empty values.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for prize_idx, prize in enumerate(data):
        year = prize.get("year_awarded", "Unknown Year")
        for laureate_idx, laureate in enumerate(prize.get("laureates", [])):
            missing = [
                field for field in critical_fields
                if not laureate.get(field)
            ]
            if missing:
                print(
                    f"Year: {year}, Prize Index: {prize_idx}, Laureate Index: {laureate_idx}, "
                    f"Missing fields: {', '.join(missing)}"
                )

if __name__ == "__main__":
    find_missing_fields("data/nobel_literature.json") 