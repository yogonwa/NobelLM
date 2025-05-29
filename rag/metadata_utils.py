import os
import json
from typing import List, Dict, Any

def flatten_laureate_metadata(raw_metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Flattens the nested laureate metadata into a flat list of laureate dicts.
    Each laureate dict will include all original laureate fields plus year_awarded, category, and any other top-level fields needed for factual queries.
    """
    flat = []
    for entry in raw_metadata:
        year = entry.get("year_awarded")
        category = entry.get("category")
        for laureate in entry.get("laureates", []):
            laureate_flat = dict(laureate)
            laureate_flat["year_awarded"] = year
            laureate_flat["category"] = category
            flat.append(laureate_flat)
    return flat

def load_laureate_metadata(metadata_path: str = None) -> List[Dict[str, Any]]:
    """
    Loads and flattens laureate metadata from the canonical JSON file.
    If metadata_path is not provided, uses the default Nobel literature metadata location.
    """
    if metadata_path is None:
        metadata_path = os.path.join(os.path.dirname(__file__), '../data/nobel_literature.json')
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
            return flatten_laureate_metadata(raw)
    return None 