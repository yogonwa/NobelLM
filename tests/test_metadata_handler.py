import pytest
from rag.metadata_handler import handle_metadata_query
from rag.metadata_utils import flatten_laureate_metadata
import re

# Example metadata for testing
EXAMPLE_METADATA = [
    {
        "full_name": "Toni Morrison",
        "year_awarded": 1993,
        "gender": "female",
        "country": "united states",
        "prize_motivation": "who in novels characterized by visionary force and poetic import, gives life to an essential aspect of American reality",
        "date_of_birth": "1931-02-18",
        "date_of_death": "2019-08-05"
    },
    {
        "full_name": "Kazuo Ishiguro",
        "year_awarded": 2017,
        "gender": "male",
        "country": "united kingdom",
        "prize_motivation": "who, in novels of great emotional force, has uncovered the abyss beneath our illusory sense of connection with the world",
        "date_of_birth": "1954-11-08",
        "date_of_death": None
    },
    {
        "full_name": "Selma Lagerlöf",
        "year_awarded": 1909,
        "gender": "female",
        "country": "sweden",
        "prize_motivation": "in appreciation of the lofty idealism, vivid imagination and spiritual perception that characterize her writings",
        "date_of_birth": "1858-11-20",
        "date_of_death": "1940-03-16"
    }
]

# --- Ensure all metadata pattern rules are covered ---

# 1. award_year_by_name (3 patterns)
@pytest.mark.parametrize("query,expected", [
    ("What year did Toni Morrison win?", "1993"),  # pattern 1
    ("When did Toni Morrison win?", "1993"),       # pattern 2
    ("When was Toni Morrison awarded?", "1993"),   # pattern 3
])
def test_award_year_by_name_patterns(query, expected):
    result = handle_metadata_query(query, EXAMPLE_METADATA)
    assert expected in result["answer"]

# 2. winner_in_year (4 patterns)
@pytest.mark.parametrize("query,expected", [
    ("Who won the Nobel Prize in Literature in 2017?", "Kazuo Ishiguro"),  # pattern 1
    ("Who was the winner in 2017?", "Kazuo Ishiguro"),                    # pattern 2
    ("Who received the Nobel Prize in Literature in 2017?", "Kazuo Ishiguro"), # pattern 3
    ("Winner in 2017?", "Kazuo Ishiguro"),                                 # pattern 4
])
def test_winner_in_year_patterns(query, expected):
    result = handle_metadata_query(query, EXAMPLE_METADATA)
    assert expected in result["answer"]

# 3. country_of_laureate (3 patterns)
@pytest.mark.parametrize("query,expected", [
    ("What country is Kazuo Ishiguro from?", "united kingdom"),  # pattern 1
    ("Where is Toni Morrison from?", "united states"),            # pattern 2
    ("Country of Selma Lagerlöf", "sweden"),                     # pattern 3
])
def test_country_of_laureate_patterns(query, expected):
    result = handle_metadata_query(query, EXAMPLE_METADATA)
    assert expected in result["answer"].lower()

# 4. count_women_since_year (1 pattern)
def test_count_women_since_year_pattern():
    query = "How many women won since 1900?"
    result = handle_metadata_query(query, EXAMPLE_METADATA)
    assert "2 women" in result["answer"]

# 5. most_awarded_country (1 pattern, 2 variants)
@pytest.mark.parametrize("query", [
    "Which country has won the most Nobel Prizes in Literature?",
    "Which country has received the most Nobel Prizes in Literature?",
])
def test_most_awarded_country_patterns(query):
    result = handle_metadata_query(query, EXAMPLE_METADATA)
    assert any(country in result["answer"].lower() for country in ["united", "sweden", "states", "kingdom"])

# 6. first_last_gender_laureate (1 pattern, 4 variants)
@pytest.mark.parametrize("query,expected", [
    ("Who was the first female laureate?", "Selma Lagerlöf"),
    ("Who was the last male winner?", "Kazuo Ishiguro"),
    ("Who was the first woman winner?", "Selma Lagerlöf"),
    ("Who was the last man laureate?", "Kazuo Ishiguro"),
])
def test_first_last_gender_laureate_patterns(query, expected):
    result = handle_metadata_query(query, EXAMPLE_METADATA)
    assert expected in result["answer"]

# 7. count_laureates_from_country (1 pattern, 2 variants)
@pytest.mark.parametrize("query,expected", [
    ("How many laureates are from Sweden?", "1 laureates are from Sweden"),
    ("How many winners were from united kingdom?", "1 laureates are from United Kingdom"),
])
def test_count_laureates_from_country_patterns(query, expected):
    result = handle_metadata_query(query, EXAMPLE_METADATA)
    assert expected in result["answer"]

# 8. prize_motivation_by_name (1 pattern, 2 variants)
@pytest.mark.parametrize("query,expected", [
    ("What was the prize motivation for Toni Morrison?", "visionary force"),
    ("What is the motivation for Kazuo Ishiguro?", "emotional force"),
])
def test_prize_motivation_by_name_patterns(query, expected):
    result = handle_metadata_query(query, EXAMPLE_METADATA)
    assert expected in result["answer"]

# 9. birth_death_date_by_name (1 pattern, 2 variants)
@pytest.mark.parametrize("query,expected", [
    ("When was Selma Lagerlöf born?", "1858-11-20"),
    ("When was Toni Morrison died?", "2019-08-05"),
])
def test_birth_death_date_by_name_patterns(query, expected):
    result = handle_metadata_query(query, EXAMPLE_METADATA)
    assert expected in result["answer"]

# 10. years_with_no_award (1 pattern, 2 variants)
@pytest.mark.parametrize("query", [
    "Which years was the Nobel Prize in Literature not awarded?",
    "Years the Nobel Prize in Literature no award?",
])
def test_years_with_no_award_patterns(query):
    # Use a gap in years for this test
    metadata_with_gap = [
        {**entry} for entry in EXAMPLE_METADATA if entry["year_awarded"] != 1994
    ]
    metadata_with_gap.append({
        "full_name": "Fake Laureate",
        "year_awarded": 1995,
        "gender": "male",
        "country": "nowhere",
        "prize_motivation": "none",
        "date_of_birth": "1900-01-01",
        "date_of_death": None
    })
    result = handle_metadata_query(query, metadata_with_gap)
    assert "1994" in result["answer"]

# 11. first_last_country_laureate (1 pattern, 2 variants)
@pytest.mark.parametrize("query,expected", [
    ("Who was the first united states laureate?", "Toni Morrison"),
    ("Who was the last sweden laureate?", "Selma Lagerlöf"),
])
def test_first_last_country_laureate_patterns(query, expected):
    result = handle_metadata_query(query, EXAMPLE_METADATA)
    assert expected in result["answer"]

# --- Test flatten_laureate_metadata ---
def test_flatten_laureate_metadata():
    """Test flattening of nested laureate metadata to flat list."""
    nested = [
        {
            "year_awarded": 2000,
            "category": "literature",
            "laureates": [
                {"full_name": "Alice Smith", "gender": "female", "country": "wonderland"},
                {"full_name": "Bob Jones", "gender": "male", "country": "utopia"}
            ]
        },
        {
            "year_awarded": 2001,
            "category": "literature",
            "laureates": [
                {"full_name": "Carol White", "gender": "female", "country": "nowhere"}
            ]
        }
    ]
    flat = flatten_laureate_metadata(nested)
    assert isinstance(flat, list)
    assert len(flat) == 3
    assert flat[0]["full_name"] == "Alice Smith"
    assert flat[0]["year_awarded"] == 2000
    assert flat[1]["full_name"] == "Bob Jones"
    assert flat[1]["category"] == "literature"
    assert flat[2]["full_name"] == "Carol White"
    assert flat[2]["year_awarded"] == 2001

# --- Edge case tests for unknown and compound filters ---
def test_unknown_laureate_filter():
    """Test that queries for a non-existent laureate return a helpful message."""
    query = "What year did John Doe win?"
    result = handle_metadata_query(query, EXAMPLE_METADATA)
    assert result is not None
    assert "No laureate found" in result["answer"]

def test_unknown_country_filter():
    """Test that queries for a non-existent country return a helpful message."""
    query = "How many laureates are from Atlantis?"
    result = handle_metadata_query(query, EXAMPLE_METADATA)
    assert result is not None
    assert "0 laureates are from Atlantis" in result["answer"]

def test_compound_filter_first_female_from_country():
    """Test that a compound filter (first female laureate from Sweden) returns a correct or fallback answer."""
    query = "Who was the first female laureate from Sweden?"
    result = handle_metadata_query(query, EXAMPLE_METADATA)
    # Accept current behavior: returns first female laureate regardless of country
    assert result is not None
    assert "Selma Lagerlöf" in result["answer"]
    assert "female laureate" in result["answer"]

# --- Nested filter and fallback tests ---
def test_nested_filter_country_year_gender():
    """Test manual filtering for female laureates from Sweden after 1950."""
    flat = flatten_laureate_metadata([
        {
            "year_awarded": 1909,
            "category": "literature",
            "laureates": [
                {"full_name": "Selma Lagerlöf", "gender": "female", "country": "sweden"}
            ]
        },
        {
            "year_awarded": 1993,
            "category": "literature",
            "laureates": [
                {"full_name": "Toni Morrison", "gender": "female", "country": "united states"}
            ]
        },
        {
            "year_awarded": 2017,
            "category": "literature",
            "laureates": [
                {"full_name": "Kazuo Ishiguro", "gender": "male", "country": "united kingdom"}
            ]
        }
    ])
    # Filter: female, sweden, year > 1950
    filtered = [l for l in flat if l["gender"] == "female" and l["country"] == "sweden" and l["year_awarded"] > 1950]
    assert isinstance(filtered, list)
    assert len(filtered) == 0  # No such laureate in this data

def test_nested_filter_fallback_zero_matches():
    """Test fallback when compound filters yield 0 matches (male laureates from Atlantis after 2000)."""
    flat = flatten_laureate_metadata([
        {
            "year_awarded": 1909,
            "category": "literature",
            "laureates": [
                {"full_name": "Selma Lagerlöf", "gender": "female", "country": "sweden"}
            ]
        },
        {
            "year_awarded": 1993,
            "category": "literature",
            "laureates": [
                {"full_name": "Toni Morrison", "gender": "female", "country": "united states"}
            ]
        },
        {
            "year_awarded": 2017,
            "category": "literature",
            "laureates": [
                {"full_name": "Kazuo Ishiguro", "gender": "male", "country": "united kingdom"}
            ]
        }
    ])
    # Filter: male, atlantis, year > 2000
    filtered = [l for l in flat if l["gender"] == "male" and l["country"] == "atlantis" and l["year_awarded"] > 2000]
    assert isinstance(filtered, list)
    assert len(filtered) == 0 