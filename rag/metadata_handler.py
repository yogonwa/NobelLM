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
# Example: "What year did Toni Morrison win?"
def handle_award_year(match: re.Match, metadata: List[Dict[str, Any]]) -> dict:
    name = match.group(1).strip().lower()
    for laureate in metadata:
        if name in laureate.get("full_name", "").lower():
            answer = f"{laureate['full_name']} won in {laureate['year_awarded']}."
            motivation = laureate.get("prize_motivation")
            if motivation:
                answer += f" The laureate was recognized for: {motivation}"
            return {
                "answer": answer,
                "laureate": laureate["full_name"],
                "year_awarded": laureate["year_awarded"],
                "country": laureate.get("country"),
                "category": laureate.get("category"),
                "prize_motivation": laureate.get("prize_motivation"),
            }
    return {"answer": f"No laureate found matching '{name}'."}

# Example: "How many women won since 1900?"
def handle_count_women_since(match: re.Match, metadata: List[Dict[str, Any]]) -> dict:
    since_year = int(match.group(1))
    count = sum(1 for l in metadata if l.get("gender") == "female" and l.get("year_awarded", 0) >= since_year)
    return {"answer": f"{count} women have won the Nobel Prize in Literature since {since_year}."}

# Example: "Who won the Nobel Prize in Literature in 2017?"
def handle_winner_in_year(match: re.Match, metadata: List[Dict[str, Any]]) -> dict:
    year = int(match.group(1))
    winners = [l for l in metadata if l.get("year_awarded") == year]
    names = [l["full_name"] for l in winners]
    if names:
        if len(names) == 1:
            laureate = winners[0]
            answer = f"The winner was: {names[0]}."
            motivation = laureate.get("prize_motivation")
            if motivation:
                answer += f" The laureate was recognized for: {motivation}"
            return {
                "answer": answer,
                "laureate": laureate["full_name"],
                "year_awarded": laureate["year_awarded"],
                "country": laureate.get("country"),
                "category": laureate.get("category"),
                "prize_motivation": laureate.get("prize_motivation"),
            }
        else:
            return {"answer": f"The winners were: {', '.join(names)}.", "year_awarded": year, "laureates": names}
    return {"answer": f"No winners found for the year {year}."}

# Example: "Which country has won the most Nobel Prizes in Literature?"
def handle_most_awarded_country(_: re.Match, metadata: List[Dict[str, Any]]) -> dict:
    countries = [l.get("country") for l in metadata if l.get("country")]
    counter = Counter(countries)
    most_common = counter.most_common(1)
    if most_common:
        country, count = most_common[0]
        return {"answer": f"{country} has the most Nobel Prize in Literature winners with {count}.", "country": country, "count": count}
    return {"answer": "Could not determine the most awarded country."}

# Example: "What country is Kazuo Ishiguro from?"
def handle_country_of_laureate(match: re.Match, metadata: List[Dict[str, Any]]) -> dict:
    name = match.group(1).strip().lower()
    for laureate in metadata:
        if name in laureate.get("full_name", "").lower():
            country = laureate.get("country", "Unknown")
            answer = f"{laureate['full_name']} is from {country}."
            motivation = laureate.get("prize_motivation")
            if motivation:
                answer += f" The laureate was recognized for: {motivation}"
            return {
                "answer": answer,
                "laureate": laureate["full_name"],
                "year_awarded": laureate["year_awarded"],
                "country": laureate.get("country"),
                "category": laureate.get("category"),
                "prize_motivation": laureate.get("prize_motivation"),
            }
    return {"answer": f"No laureate found matching '{name}'."}

# Example: "Who was the first female laureate?"
def handle_first_last_gender_laureate(match: re.Match, metadata: List[Dict[str, Any]]) -> dict:
    order = match.group(1).lower()  # 'first' or 'last'
    gender = match.group(2).lower()
    # Normalize gender
    if gender in ["woman", "female"]:
        gender = "female"
    elif gender in ["man", "male"]:
        gender = "male"
    filtered = [l for l in metadata if l.get("gender", "").lower() == gender]
    if not filtered:
        return {"answer": f"No {gender} laureates found."}
    # Sort by year_awarded
    filtered_sorted = sorted(filtered, key=lambda l: l.get("year_awarded", 0))
    laureate = filtered_sorted[0] if order == "first" else filtered_sorted[-1]
    answer = f"The {order} {gender} laureate was {laureate['full_name']} in {laureate['year_awarded']}."
    motivation = laureate.get("prize_motivation")
    if motivation:
        answer += f" The laureate was recognized for: {motivation}"
    return {
        "answer": answer,
        "laureate": laureate["full_name"],
        "year_awarded": laureate["year_awarded"],
        "country": laureate.get("country"),
        "category": laureate.get("category"),
        "prize_motivation": laureate.get("prize_motivation"),
        "gender": gender,
        "order": order
    }

# Example: "How many laureates are from Sweden?"
def handle_count_laureates_from_country(match: re.Match, metadata: List[Dict[str, Any]]) -> dict:
    country = match.group(1).strip().lower()
    count = sum(1 for l in metadata if l.get("country", "").lower() == country)
    return {"answer": f"{count} laureates are from {country.title()}.", "country": country.title(), "count": count}

# Example: "What was the prize motivation for Toni Morrison?"
def handle_prize_motivation(match: re.Match, metadata: List[Dict[str, Any]]) -> dict:
    name = match.group(1).strip().lower()
    for laureate in metadata:
        if name in laureate.get("full_name", "").lower():
            motivation = laureate.get("prize_motivation", "No motivation found.")
            return {
                "answer": f"The prize motivation for {laureate['full_name']} was: {motivation}",
                "laureate": laureate["full_name"],
                "year_awarded": laureate["year_awarded"],
                "country": laureate.get("country"),
                "category": laureate.get("category"),
                "prize_motivation": motivation,
            }
    return {"answer": f"No laureate found matching '{name}'."}

# Example: "When was Selma Lagerlöf born?" or "When did Toni Morrison die?"
def handle_birth_death_date(match: re.Match, metadata: List[Dict[str, Any]]) -> dict:
    name = match.group(1).strip().lower()
    event = match.group(2).lower()  # 'born' or 'died'
    for laureate in metadata:
        if name in laureate.get("full_name", "").lower():
            if event == "born":
                date = laureate.get("date_of_birth", "Unknown")
                answer = f"{laureate['full_name']} was born on {date}."
            elif event == "died":
                date = laureate.get("date_of_death", "Unknown")
                answer = f"{laureate['full_name']} died on {date}."
            else:
                continue
            motivation = laureate.get("prize_motivation")
            if motivation:
                answer += f" The laureate was recognized for: {motivation}"
            return {
                "answer": answer,
                "laureate": laureate["full_name"],
                "year_awarded": laureate["year_awarded"],
                "country": laureate.get("country"),
                "category": laureate.get("category"),
                "prize_motivation": laureate.get("prize_motivation"),
                "date_of_birth": laureate.get("date_of_birth"),
                "date_of_death": laureate.get("date_of_death"),
                "event": event
            }
    return {"answer": f"No laureate found matching '{name}'."}

# Example: "Which years was the Nobel Prize in Literature not awarded?"
def handle_years_with_no_award(_: re.Match, metadata: List[Dict[str, Any]]) -> dict:
    awarded_years = {entry['year_awarded'] for entry in metadata}
    if not awarded_years:
        return {"answer": "No data available."}
    all_years = set(range(min(awarded_years), max(awarded_years)+1))
    missing_years = sorted(all_years - awarded_years)
    if not missing_years:
        return {"answer": "Every year in the dataset has at least one laureate."}
    year_list = ", ".join(str(y) for y in missing_years)
    return {"answer": f"The Nobel Prize in Literature was not awarded in the following years: {year_list}.", "years": missing_years}

# Example: "Who was the first United States laureate?"
def handle_first_last_country_laureate(match: re.Match, metadata: List[Dict[str, Any]]) -> dict:
    order = match.group(1).lower()  # 'first' or 'last'
    country = match.group(2).strip().lower()
    filtered = [l for l in metadata if l.get("country", "").lower() == country]
    if not filtered:
        return {"answer": f"No laureates found from {country.title()}."}
    filtered_sorted = sorted(filtered, key=lambda l: l.get("year_awarded", 0))
    laureate = filtered_sorted[0] if order == "first" else filtered_sorted[-1]
    answer = f"The {order} laureate from {country.title()} was {laureate['full_name']} in {laureate['year_awarded']}."
    motivation = laureate.get("prize_motivation")
    if motivation:
        answer += f" The laureate was recognized for: {motivation}"
    return {
        "answer": answer,
        "laureate": laureate["full_name"],
        "year_awarded": laureate["year_awarded"],
        "country": laureate.get("country"),
        "category": laureate.get("category"),
        "prize_motivation": laureate.get("prize_motivation"),
        "order": order
    }

# --- Registry Entry Definition ---
@dataclass
class QueryRule:
    name: str
    patterns: List[Pattern]  # Now supports multiple patterns
    handler: Callable[[re.Match, List[Dict[str, Any]]], str]

# --- Rule Registry (multi-pattern) ---
FACTUAL_QUERY_REGISTRY: List[QueryRule] = [
    QueryRule(
        name="award_year_by_name",
        patterns=[
            re.compile(r"what year did (.+?) win(?: [\w\s]+)?\s*[\?\.\!\,;:]*$", re.IGNORECASE),
            re.compile(r"when did (.+?) win(?: [\w\s]+)?\s*[\?\.\!\,;:]*$", re.IGNORECASE),
            re.compile(r"when was (.+?) awarded(?: [\w\s]+)?\s*[\?\.\!\,;:]*$", re.IGNORECASE),
        ],
        handler=handle_award_year
    ),
    QueryRule(
        name="winner_in_year",
        patterns=[
            re.compile(r"who won(?: the)?(?: nobel)?(?: prize)?(?: in literature)? in (\d{4})(?: [\w\s]+)?\s*[\?\.\!\,;:]*$", re.IGNORECASE),
            re.compile(r"who was the winner in (\d{4})(?: [\w\s]+)?\s*[\?\.\!\,;:]*$", re.IGNORECASE),
            re.compile(r"who received(?: the)?(?: nobel)?(?: prize)?(?: in literature)? in (\d{4})(?: [\w\s]+)?\s*[\?\.\!\,;:]*$", re.IGNORECASE),
            re.compile(r"winner in (\d{4})(?: [\w\s]+)?\s*[\?\.\!\,;:]*$", re.IGNORECASE),
        ],
        handler=handle_winner_in_year
    ),
    QueryRule(
        name="country_of_laureate",
        patterns=[
            re.compile(r"what country is ([\w .'-]+) from(?: [\w\s]+)?\s*[\?\.\!\,;:]*$", re.IGNORECASE),
            re.compile(r"where is ([\w .'-]+) from(?: [\w\s]+)?\s*[\?\.\!\,;:]*$", re.IGNORECASE),
            re.compile(r"country of ([\w .'-]+)(?: [\w\s]+)?\s*[\?\.\!\,;:]*$", re.IGNORECASE),
        ],
        handler=handle_country_of_laureate
    ),
    QueryRule(
        name="count_women_since_year",
        patterns=[re.compile(r"how many women won since (\d{4})(?: [\w\s]+)?\s*[\?\.\!\,;:]*$", re.IGNORECASE)],
        handler=handle_count_women_since
    ),
    QueryRule(
        name="most_awarded_country",
        patterns=[re.compile(r"which country has (?:won|received) the most(?: [\w\s]+)?\s*[\?\.\!\,;:]*$", re.IGNORECASE)],
        handler=handle_most_awarded_country
    ),
    QueryRule(
        name="first_last_gender_laureate",
        patterns=[re.compile(r"who was the (first|last) (male|female|woman|man) (?:winner|laureate)(?: [\w\s]+)?\s*[\?\.\!\,;:]*$", re.IGNORECASE)],
        handler=handle_first_last_gender_laureate
    ),
    QueryRule(
        name="count_laureates_from_country",
        patterns=[re.compile(r"how many (?:laureates|winners) (?:are|were)? from ([\w .'-]+)(?: [\w\s]+)?\s*[\?\.\!\,;:]*$", re.IGNORECASE)],
        handler=handle_count_laureates_from_country
    ),
    QueryRule(
        name="prize_motivation_by_name",
        patterns=[re.compile(r"what (?:was|is) the (?:prize )?motivation for ([\w .'-]+)(?: [\w\s]+)?\s*[\?\.\!\,;:]*$", re.IGNORECASE)],
        handler=handle_prize_motivation
    ),
    QueryRule(
        name="birth_death_date_by_name",
        patterns=[re.compile(r"when was ([\w .'-]+) (born|died)(?: [\w\s]+)?\s*[\?\.\!\,;:]*$", re.IGNORECASE)],
        handler=handle_birth_death_date
    ),
    QueryRule(
        name="years_with_no_award",
        patterns=[
            re.compile(r"(which years|years)\s*(was|were)?\s*(the\s*)?nobel prize in literature\s*(not awarded|no award)(?: [\w\s]+)?[\s\?\.\!\,;:]*$", re.IGNORECASE)
        ],
        handler=handle_years_with_no_award
    ),
    QueryRule(
        name="first_last_country_laureate",
        patterns=[re.compile(r"who was the (first|last) ([\w .'-]+) laureate(?: [\w\s]+)?\s*[\?\.\!\,;:]*$", re.IGNORECASE)],
        handler=handle_first_last_country_laureate
    ),
    # Add more rules here as needed
]

# --- Query Matcher (multi-pattern) ---
def match_query_to_handler(query: str) -> Optional[Tuple[QueryRule, re.Match]]:
    for rule in FACTUAL_QUERY_REGISTRY:
        for pattern in rule.patterns:
            match = pattern.search(query)
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
        handler_result = rule.handler(match, metadata)
        if isinstance(handler_result, dict):
            handler_result = handler_result.copy()
            handler_result["source"] = {"rule": rule.name}
            handler_result["answer_type"] = "metadata"
            return handler_result
        else:
            return {
                "answer": handler_result,
                "source": {"rule": rule.name},
                "answer_type": "metadata"
            }
    return None  # fall back to RAG 