"""
MetadataQueryRegistry

This module defines a registry of factual query types that can be answered directly from Nobel laureate metadata, without invoking LLM or embedding-based retrieval. 
Each rule includes a matching function and a handler function.

To integrate:
- Use `match_query_to_handler()` in the router layer before triggering semantic RAG.
- Handlers receive a match object and the metadata (list of laureates).
"""
import re
from typing import Callable, Dict, List, Optional, Pattern, Tuple, Any
from dataclasses import dataclass
from collections import Counter

# --- Handler Implementations ---
def handle_award_year(match: re.Match, metadata: List[Dict[str, Any]]) -> str:
    name = match.group(1).strip().lower()
    for laureate in metadata:
        if name in laureate.get("full_name", "").lower():
            return f"{laureate['full_name']} won in {laureate['year_awarded']}."
    return f"No laureate found matching '{name}'."

def handle_count_women_since(match: re.Match, metadata: List[Dict[str, Any]]) -> str:
    since_year = int(match.group(1))
    count = sum(1 for l in metadata if l.get("gender") == "female" and l.get("year_awarded", 0) >= since_year)
    return f"{count} women have won the Nobel Prize in Literature since {since_year}."

def handle_winner_in_year(match: re.Match, metadata: List[Dict[str, Any]]) -> str:
    year = int(match.group(1))
    names = [l["full_name"] for l in metadata if l.get("year_awarded") == year]
    if names:
        return f"The winner{'s were' if len(names) > 1 else ' was'}: {', '.join(names)}."
    return f"No winners found for the year {year}."

def handle_most_awarded_country(_: re.Match, metadata: List[Dict[str, Any]]) -> str:
    countries = [l.get("country") for l in metadata if l.get("country")]
    counter = Counter(countries)
    most_common = counter.most_common(1)
    if most_common:
        country, count = most_common[0]
        return f"{country} has the most Nobel Prize in Literature winners with {count}."
    return "Could not determine the most awarded country."

def handle_country_of_laureate(match: re.Match, metadata: List[Dict[str, Any]]) -> str:
    name = match.group(1).strip().lower()
    for laureate in metadata:
        if name in laureate.get("full_name", "").lower():
            country = laureate.get("country", "Unknown")
            return f"{laureate['full_name']} is from {country}."
    return f"No laureate found matching '{name}'."

def handle_first_last_gender_laureate(match: re.Match, metadata: List[Dict[str, Any]]) -> str:
    order = match.group(1).lower()  # 'first' or 'last'
    gender = match.group(2).lower()
    # Normalize gender
    if gender in ["woman", "female"]:
        gender = "female"
    elif gender in ["man", "male"]:
        gender = "male"
    filtered = [l for l in metadata if l.get("gender", "").lower() == gender]
    if not filtered:
        return f"No {gender} laureates found."
    # Sort by year_awarded
    filtered_sorted = sorted(filtered, key=lambda l: l.get("year_awarded", 0))
    laureate = filtered_sorted[0] if order == "first" else filtered_sorted[-1]
    return f"The {order} {gender} laureate was {laureate['full_name']} in {laureate['year_awarded']}."

def handle_count_laureates_from_country(match: re.Match, metadata: List[Dict[str, Any]]) -> str:
    country = match.group(1).strip().lower()
    count = sum(1 for l in metadata if l.get("country", "").lower() == country)
    return f"{count} laureates are from {country.title()}."

def handle_prize_motivation(match: re.Match, metadata: List[Dict[str, Any]]) -> str:
    name = match.group(1).strip().lower()
    for laureate in metadata:
        if name in laureate.get("full_name", "").lower():
            motivation = laureate.get("prize_motivation", "No motivation found.")
            return f"The prize motivation for {laureate['full_name']} was: {motivation}"
    return f"No laureate found matching '{name}'."

def handle_birth_death_date(match: re.Match, metadata: List[Dict[str, Any]]) -> str:
    name = match.group(1).strip().lower()
    event = match.group(2).lower()  # 'born' or 'died'
    for laureate in metadata:
        if name in laureate.get("full_name", "").lower():
            if event == "born":
                date = laureate.get("date_of_birth", "Unknown")
                return f"{laureate['full_name']} was born on {date}."
            elif event == "died":
                date = laureate.get("date_of_death", "Unknown")
                return f"{laureate['full_name']} died on {date}."
    return f"No laureate found matching '{name}'."

def handle_years_with_no_award(_: re.Match, metadata: List[Dict[str, Any]]) -> str:
    """
    Returns a list of years in which the Nobel Prize in Literature was not awarded.
    """
    awarded_years = {entry['year_awarded'] for entry in metadata}
    if not awarded_years:
        return "No data available."
    all_years = set(range(min(awarded_years), max(awarded_years)+1))
    missing_years = sorted(all_years - awarded_years)
    if not missing_years:
        return "Every year in the dataset has at least one laureate."
    year_list = ", ".join(str(y) for y in missing_years)
    return f"The Nobel Prize in Literature was not awarded in the following years: {year_list}."

def handle_first_last_country_laureate(match: re.Match, metadata: List[Dict[str, Any]]) -> str:
    order = match.group(1).lower()  # 'first' or 'last'
    country = match.group(2).strip().lower()
    filtered = [l for l in metadata if l.get("country", "").lower() == country]
    if not filtered:
        return f"No laureates found from {country.title()}."
    filtered_sorted = sorted(filtered, key=lambda l: l.get("year_awarded", 0))
    laureate = filtered_sorted[0] if order == "first" else filtered_sorted[-1]
    return f"The {order} laureate from {country.title()} was {laureate['full_name']} in {laureate['year_awarded']}."

# --- Registry Entry Definition ---
@dataclass
class QueryRule:
    name: str
    pattern: Pattern
    handler: Callable[[re.Match, List[Dict[str, Any]]], str]

# --- Rule Registry ---
FACTUAL_QUERY_REGISTRY: List[QueryRule] = [
    QueryRule(
        name="award_year_by_name",
        pattern=re.compile(r"what year did (.+?) win", re.IGNORECASE),
        handler=handle_award_year
    ),
    QueryRule(
        name="count_women_since_year",
        pattern=re.compile(r"how many women won since (\d{4})", re.IGNORECASE),
        handler=handle_count_women_since
    ),
    QueryRule(
        name="winner_in_year",
        pattern=re.compile(r"who won (?:the )?nobel (?:prize )?(?:in literature )?in (\d{4})", re.IGNORECASE),
        handler=handle_winner_in_year
    ),
    QueryRule(
        name="most_awarded_country",
        pattern=re.compile(r"which country has (?:won|received) the most", re.IGNORECASE),
        handler=handle_most_awarded_country
    ),
    QueryRule(
        name="country_of_laureate",
        pattern=re.compile(r"what country is ([\w .'-]+) from", re.IGNORECASE),
        handler=handle_country_of_laureate
    ),
    QueryRule(
        name="first_last_gender_laureate",
        pattern=re.compile(r"who was the (first|last) (male|female|woman|man) (?:winner|laureate)", re.IGNORECASE),
        handler=handle_first_last_gender_laureate
    ),
    QueryRule(
        name="count_laureates_from_country",
        pattern=re.compile(r"how many (?:laureates|winners) (?:are|were)? from ([\w .'-]+)", re.IGNORECASE),
        handler=handle_count_laureates_from_country
    ),
    QueryRule(
        name="prize_motivation_by_name",
        pattern=re.compile(r"what (?:was|is) the (?:prize )?motivation for ([\w .'-]+)", re.IGNORECASE),
        handler=handle_prize_motivation
    ),
    QueryRule(
        name="birth_death_date_by_name",
        pattern=re.compile(r"when was ([\w .'-]+) (born|died)", re.IGNORECASE),
        handler=handle_birth_death_date
    ),
    QueryRule(
        name="years_with_no_award",
        pattern=re.compile(r"(which years|years) (was|were)? (the )?nobel prize in literature (not awarded|no award)", re.IGNORECASE),
        handler=handle_years_with_no_award
    ),
    QueryRule(
        name="first_last_country_laureate",
        pattern=re.compile(r"who was the (first|last) ([\w .'-]+) laureate", re.IGNORECASE),
        handler=handle_first_last_country_laureate
    ),
    # Add more rules here as needed
]

# --- Query Matcher ---
def match_query_to_handler(query: str) -> Optional[Tuple[QueryRule, re.Match]]:
    for rule in FACTUAL_QUERY_REGISTRY:
        match = rule.pattern.search(query)
        if match:
            return rule, match
    return None

# --- Main Metadata Handler ---
def handle_metadata_query(query: str, metadata: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Attempt to answer a query directly from structured laureate metadata using the registry.
    Returns a dict with 'answer', 'source', and 'answer_type' if resolvable, else None.
    """
    result = match_query_to_handler(query)
    if result:
        rule, match = result
        answer = rule.handler(match, metadata)
        return {
            "answer": answer,
            "source": {"rule": rule.name},
            "answer_type": "metadata"
        }
    return None  # fall back to RAG 