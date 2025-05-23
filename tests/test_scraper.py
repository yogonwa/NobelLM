import pytest
from bs4 import BeautifulSoup
from scraper.scrape_literature import extract_life_and_work_blurbs, infer_gender_from_text, extract_metadata
from scraper.speech_extraction import clean_speech_text, extract_nobel_lecture
from unittest.mock import patch, Mock

# --- Fixtures for HTML snippets ---

BOTH_BLURBS_HTML = '''
<div class="description border-top">
  <h3>Life</h3>
  <p>Born in a small town.</p>
  <p>He became a writer.</p>
</div>
<div class="description border-top">
  <h3>Work</h3>
  <p>Known for his novels.</p>
</div>
'''

ONLY_LIFE_HTML = '''
<div class="description border-top">
  <h3>Life</h3>
  <p>She was born in Paris.</p>
</div>
'''

NO_BLURBS_HTML = '''
<div class="description border-top">
  <h3>Other</h3>
  <p>Irrelevant section.</p>
</div>
'''

MISSING_H3_HTML = '''
<div class="description border-top">
  <p>No heading here.</p>
</div>
'''

EMPTY_P_HTML = '''
<div class="description border-top">
  <h3>Life</h3>
  <p>   </p>
</div>
'''

# --- Tests for extract_life_and_work_blurbs ---

def test_extract_life_and_work_blurbs_both():
    """Should extract both life and work blurbs when present."""
    soup = BeautifulSoup(BOTH_BLURBS_HTML, "html.parser")
    result = extract_life_and_work_blurbs(soup)
    assert result["life_blurb"] == "Born in a small town. He became a writer."
    assert result["work_blurb"] == "Known for his novels."

def test_extract_life_and_work_blurbs_only_life():
    """Should extract only life blurb if work is missing."""
    soup = BeautifulSoup(ONLY_LIFE_HTML, "html.parser")
    result = extract_life_and_work_blurbs(soup)
    assert result["life_blurb"] == "She was born in Paris."
    assert result["work_blurb"] == ""

def test_extract_life_and_work_blurbs_none():
    """Should return empty blurbs if neither section is present."""
    soup = BeautifulSoup(NO_BLURBS_HTML, "html.parser")
    result = extract_life_and_work_blurbs(soup)
    assert result["life_blurb"] == ""
    assert result["work_blurb"] == ""

def test_extract_life_and_work_blurbs_missing_h3():
    """Should handle missing <h3> gracefully."""
    soup = BeautifulSoup(MISSING_H3_HTML, "html.parser")
    result = extract_life_and_work_blurbs(soup)
    assert result["life_blurb"] == ""
    assert result["work_blurb"] == ""

def test_extract_life_and_work_blurbs_empty_p():
    """Should ignore empty <p> tags."""
    soup = BeautifulSoup(EMPTY_P_HTML, "html.parser")
    result = extract_life_and_work_blurbs(soup)
    assert result["life_blurb"] == ""
    assert result["work_blurb"] == ""

# --- Tests for infer_gender_from_text ---

def test_infer_gender_male():
    """Should return 'Male' for text with male pronouns."""
    assert infer_gender_from_text("He was a great writer.") == "Male"
    assert infer_gender_from_text("His work is known worldwide.") == "Male"
    assert infer_gender_from_text("He and his friends.") == "Male"

def test_infer_gender_female():
    """Should return 'Female' for text with female pronouns."""
    assert infer_gender_from_text("She was a great writer.") == "Female"
    assert infer_gender_from_text("Her work is known worldwide.") == "Female"
    assert infer_gender_from_text("She and her friends.") == "Female"

def test_infer_gender_ambiguous_or_empty():
    """Should return None for ambiguous or empty text."""
    assert infer_gender_from_text("") is None
    assert infer_gender_from_text("The author was born in Paris.") is None
    assert infer_gender_from_text("They wrote many books.") is None

# --- Fixtures for extract_metadata ---

ALL_FIELDS_HTML = '''
<p class="born-date">Born: 1901-09-23, Žižkov, Austria-Hungary</p>
<p class="dead-date">Died: 1986-01-10</p>
<div class="content">
  <p>Prize motivation: "for his poetry which endowed with freshness"</p>
  <p>Language: Czech</p>
</div>
'''

MISSING_DEATH_HTML = '''
<p class="born-date">Born: 1920-01-01, Paris, France</p>
<div class="content">
  <p>Prize motivation: "for her novels"</p>
  <p>Language: French</p>
</div>
'''

MISSING_PLACE_HTML = '''
<p class="born-date">Born: 1950-05-05</p>
<p class="dead-date">Died: 2000-12-31</p>
<div class="content">
  <p>Prize motivation: "for his plays"</p>
  <p>Language: English</p>
</div>
'''

NO_FIELDS_HTML = '''
<div class="content">
  <p>Some unrelated text.</p>
</div>
'''

ODD_FORMATTING_HTML = '''
<p class="born-date">  Born:   1975-07-15 ,  Berlin , Germany  </p>
<p class="dead-date"> Died: 2010-03-10 </p>
<div class="content">
  <p>Prize motivation:  "for his unique style"  </p>
  <p>Language:  German </p>
</div>
'''

# --- Tests for extract_metadata ---

def test_extract_metadata_all_fields():
    """Should extract all fields when present."""
    soup = BeautifulSoup(ALL_FIELDS_HTML, "html.parser")
    result = extract_metadata(soup)
    assert result["date_of_birth"] == "1901-09-23"
    assert result["date_of_death"] == "1986-01-10"
    assert result["place_of_birth"] == "Žižkov, Austria-Hungary"
    assert result["prize_motivation"] == "for his poetry which endowed with freshness"
    assert result["language"] == "Czech"

def test_extract_metadata_missing_death():
    """Should handle missing date of death."""
    soup = BeautifulSoup(MISSING_DEATH_HTML, "html.parser")
    result = extract_metadata(soup)
    assert result["date_of_birth"] == "1920-01-01"
    assert result["date_of_death"] is None
    assert result["place_of_birth"] == "Paris, France"
    assert result["prize_motivation"] == "for her novels"
    assert result["language"] == "French"

def test_extract_metadata_missing_place():
    """Should handle missing place of birth."""
    soup = BeautifulSoup(MISSING_PLACE_HTML, "html.parser")
    result = extract_metadata(soup)
    assert result["date_of_birth"] == "1950-05-05"
    assert result["date_of_death"] == "2000-12-31"
    assert result["place_of_birth"] is None
    assert result["prize_motivation"] == "for his plays"
    assert result["language"] == "English"

def test_extract_metadata_no_fields():
    """Should return all None for missing fields."""
    soup = BeautifulSoup(NO_FIELDS_HTML, "html.parser")
    result = extract_metadata(soup)
    assert result["date_of_birth"] is None
    assert result["date_of_death"] is None
    assert result["place_of_birth"] is None
    assert result["prize_motivation"] is None
    assert result["language"] is None

def test_extract_metadata_odd_formatting():
    """Should handle extra whitespace and odd formatting."""
    soup = BeautifulSoup(ODD_FORMATTING_HTML, "html.parser")
    result = extract_metadata(soup)
    assert result["date_of_birth"] == "1975-07-15"
    assert result["date_of_death"] == "2010-03-10"
    assert result["place_of_birth"] == "Berlin , Germany"
    assert result["prize_motivation"] == "for his unique style"
    assert result["language"] == "German"

# 1. Unit test for clean_speech_text

def test_clean_speech_text_removes_noise_and_keeps_content():
    raw_text = """
Back to top

The Nobel Lecture by Jon Fosse

Explore prizes and laureates

This is the beginning of the actual lecture content.

It continues with more reflections and ideas.

Facebook

The closing lines of the lecture.
"""
    expected = (
        "The Nobel Lecture by Jon Fosse\n"
        "This is the beginning of the actual lecture content.\n"
        "It continues with more reflections and ideas.\n"
        "The closing lines of the lecture."
    )
    assert clean_speech_text(raw_text) == expected

# 2. Integration-level test for extract_nobel_lecture

def test_extract_nobel_lecture_parses_title_and_cleans_body():
    mock_html = """
    <html>
    <head><title>Nobel Lecture</title></head>
    <body>
    <h2 class="article-header__title">The Nobel Lecture by Jane Doe</h2>
    <div class="article-video">[video player]</div>
    <div class="article-body">
      <p>This is the lecture text.</p>
      <p>It continues here with more insights.</p>
    </div>
    </body>
    </html>
    """
    # Patch requests.get to return this HTML
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    with patch("scraper.speech_extraction.requests.get", return_value=mock_response):
        # Use a lower min_words threshold for testing
        result = extract_nobel_lecture("http://fake-url-for-test", min_words=2)
    assert result["nobel_lecture_title"] == "The Nobel Lecture by Jane Doe"
    assert result["nobel_lecture_text"] == "This is the lecture text.\nIt continues here with more insights."

# 3. Parametrized edge cases for extract_nobel_lecture
import pytest

@pytest.mark.parametrize("mock_html,expected_title,expected_text", [
    # Missing <h2>
    ("""
    <html><body>
    <div class='article-body'><p>Valid content only.</p></div>
    </body></html>
    """, None, "Valid content only."),
    # Missing article-body
    ("""
    <html><body>
    <h2 class='article-header__title'>Lecture Title</h2>
    </body></html>
    """, "Lecture Title", None),
    # Junk-dominated body
    ("""
    <html><body>
    <h2 class='article-header__title'>Lecture Title</h2>
    <div class='article-body'><p>Back to top</p></div>
    </body></html>
    """, "Lecture Title", None),
])
def test_extract_nobel_lecture_edge_cases(mock_html, expected_title, expected_text):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    with patch("scraper.speech_extraction.requests.get", return_value=mock_response):
        result = extract_nobel_lecture("http://fake-url-for-test", min_words=2)
    assert result["nobel_lecture_title"] == expected_title
    assert result["nobel_lecture_text"] == expected_text 