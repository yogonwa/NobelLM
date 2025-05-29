# Tests for Nobel Laureate Speech Explorer

This directory contains unit tests for core extraction and parsing logic in the Nobel Laureate Speech Explorer project. All tests use `pytest` and static HTML/text fixtures—no live HTTP requests are made.

## Test File: `test_scraper.py`

### What is Tested?

#### 1. `extract_life_and_work_blurbs`
- **Purpose:** Extracts "life" and "work" blurbs from NobelPrize.org laureate HTML.
- **Test Cases:**
  - Both blurbs present
  - Only one blurb present
  - Neither blurb present
  - Missing `<h3>` heading
  - Empty `<p>` tags
- **Inputs:** Static HTML snippets with various combinations of sections and tags.
- **Expected Output:** Dict with `life_blurb` and `work_blurb` keys, values as extracted text or empty string.

#### 2. `infer_gender_from_text`
- **Purpose:** Infers gender from pronouns in a text blurb.
- **Test Cases:**
  - Text with male pronouns ("he", "his")
  - Text with female pronouns ("she", "her")
  - Ambiguous, empty, or unrelated text
- **Inputs:** Short text strings
- **Expected Output:** "Male", "Female", or `None`

#### 3. `extract_metadata`
- **Purpose:** Extracts birth/death dates, place of birth, prize motivation, and language from laureate HTML.
- **Test Cases:**
  - All fields present
  - Missing date of death
  - Missing place of birth
  - No expected fields present
  - Odd formatting/extra whitespace
- **Inputs:** Static HTML snippets with various field combinations and formatting.
- **Expected Output:** Dict with keys: `date_of_birth`, `date_of_death`, `place_of_birth`, `prize_motivation`, `language` (values as string or `None`)

---

## Test File: `test_query_router.py`

### What is Tested?

#### 1. `IntentClassifier` (query type classification)
- **Purpose:** Ensures queries are correctly classified as factual, thematic, or generative.
- **Test Cases:**
  - Factual, thematic, and generative queries
  - Precedence rules (generative > thematic > factual)
  - Case insensitivity
  - Fallback to factual
- **Inputs:** Query strings
- **Expected Output:** Correct intent classification

#### 2. `QueryRouter` (routing and metadata integration)
- **Purpose:** Ensures queries are routed to the correct answer path (metadata or RAG) and that logs/fields are correct.
- **Test Cases:**
  - Factual queries matching metadata rules (should return `answer_type='metadata'` and correct answer)
  - Factual queries not matching metadata rules (should return `answer_type='rag'`)
  - No metadata provided (should return `answer_type='rag'`)
  - Thematic and generative queries (should return `answer_type='rag'`)
  - Logs and metadata_answer fields present and correct
- **Inputs:** Query strings and static `EXAMPLE_METADATA` (see test file)
- **Expected Output:** Correct routing, answer type, and logs

---

## How to Run the Tests

From the project root, activate your virtual environment and run:

```bash
pytest
```

Or to run only a specific test file:

```bash
pytest tests/test_query_router.py
```

## Output
- All tests should pass with no errors.
- Output will be shown in the terminal by pytest (summary of passed/failed tests).
- No files are written or modified by these tests.

## Adding More Tests
- Add new test files for other modules as needed (e.g., `test_chunking.py`, `test_embeddings.py`).
- Use static fixtures and avoid network calls for unit tests.
- Follow the same style: docstrings, descriptive test names, and clear input/output expectations. 