import pytest
from rag.metadata_handler import handle_metadata_query

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

def test_award_year_by_name():
    """Test: What year did [laureate] win?"""
    q = "What year did Toni Morrison win?"
    result = handle_metadata_query(q, EXAMPLE_METADATA)
    assert "1993" in result["answer"]

def test_count_women_since_year():
    """Test: How many women won since [year]?"""
    q = "How many women won since 1900?"
    result = handle_metadata_query(q, EXAMPLE_METADATA)
    assert "2 women" in result["answer"]

def test_winner_in_year():
    """Test: Who won the Nobel Prize in Literature in 2017?"""
    q = "Who won the Nobel Prize in Literature in 2017?"
    result = handle_metadata_query(q, EXAMPLE_METADATA)
    assert "Kazuo Ishiguro" in result["answer"]

def test_most_awarded_country():
    """Test: Which country has won the most Nobel Prizes in Literature?"""
    q = "Which country has won the most Nobel Prizes in Literature?"
    result = handle_metadata_query(q, EXAMPLE_METADATA)
    assert "united" in result["answer"] or "sweden" in result["answer"] or "states" in result["answer"]

def test_country_of_laureate():
    """Test: What country is Kazuo Ishiguro from?"""
    q = "What country is Kazuo Ishiguro from?"
    result = handle_metadata_query(q, EXAMPLE_METADATA)
    assert "united kingdom" in result["answer"].lower()

def test_first_last_gender_laureate():
    """Test: Who was the first female laureate?"""
    q = "Who was the first female laureate?"
    result = handle_metadata_query(q, EXAMPLE_METADATA)
    assert "Selma Lagerlöf" in result["answer"]
    q2 = "Who was the last male winner?"
    result2 = handle_metadata_query(q2, EXAMPLE_METADATA)
    assert "Kazuo Ishiguro" in result2["answer"]

def test_count_laureates_from_country():
    """Test: How many laureates are from Sweden?"""
    q = "How many laureates are from Sweden?"
    result = handle_metadata_query(q, EXAMPLE_METADATA)
    assert "1 laureates are from Sweden" in result["answer"]

def test_prize_motivation_by_name():
    """Test: What was the prize motivation for Toni Morrison?"""
    q = "What was the prize motivation for Toni Morrison?"
    result = handle_metadata_query(q, EXAMPLE_METADATA)
    assert "visionary force" in result["answer"]

def test_birth_death_date_by_name():
    """Test: When was Selma Lagerlöf born? When did Toni Morrison die?"""
    q = "When was Selma Lagerlöf born?"
    result = handle_metadata_query(q, EXAMPLE_METADATA)
    assert "1858-11-20" in result["answer"]
    q2 = "When was Toni Morrison died?"
    result2 = handle_metadata_query(q2, EXAMPLE_METADATA)
    assert "2019-08-05" in result2["answer"]

def test_no_match_returns_none():
    """Test: Query with no match returns None."""
    q = "What is the favorite color of Toni Morrison?"
    result = handle_metadata_query(q, EXAMPLE_METADATA)
    assert result is None

def test_years_with_no_award():
    """Test: Which years was the Nobel Prize in Literature not awarded?"""
    # Remove 1994 from the dataset to simulate a missing year
    metadata_with_gap = [
        {**entry} for entry in EXAMPLE_METADATA if entry["year_awarded"] != 1994
    ]
    # Add a fake laureate for 1995 to ensure a gap
    metadata_with_gap.append({
        "full_name": "Fake Laureate",
        "year_awarded": 1995,
        "gender": "male",
        "country": "nowhere",
        "prize_motivation": "none",
        "date_of_birth": "1900-01-01",
        "date_of_death": None
    })
    q = "Which years was the Nobel Prize in Literature not awarded?"
    result = handle_metadata_query(q, metadata_with_gap)
    # Should include 1994 in the answer
    assert "1994" in result["answer"]

def test_first_last_country_laureate():
    """Test: Who was the first/last [country] laureate?"""
    q = "Who was the first united states laureate?"
    result = handle_metadata_query(q, EXAMPLE_METADATA)
    assert "Toni Morrison" in result["answer"]
    q2 = "Who was the last sweden laureate?"
    result2 = handle_metadata_query(q2, EXAMPLE_METADATA)
    assert "Selma Lagerlöf" in result2["answer"] 