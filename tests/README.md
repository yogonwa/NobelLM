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

## Test File: `test_intent_classifier.py`

### What is Tested?

#### 1. `IntentClassifier` (query type and scoping)
- **Purpose:** Ensures queries are correctly classified as factual, thematic, or generative, and that laureate scoping (full/last name) works.
- **Test Cases:**
  - Factual, thematic, and generative queries
  - Precedence rules (generative > thematic > factual)
  - Case insensitivity
  - Fallback to factual
  - Thematic + full name scoping
  - Thematic + last name scoping
  - Edge cases (ambiguous, partial, etc.)
- **Inputs:** Query strings
- **Expected Output:** Correct intent classification and scoping

---

## Test File: `test_query_router.py`

### What is Tested?

#### 1. `QueryRouter` (routing and metadata integration)
- **Purpose:** Ensures queries are routed to the correct answer path (metadata or RAG) and that logs/fields are correct.
- **Test Cases:**
  - Factual queries matching metadata rules (should return `answer_type='metadata'` and correct answer)
  - Factual queries not matching metadata rules (should return `answer_type='rag'`)
  - No metadata provided (should return `answer_type='rag'`)
  - Thematic and generative queries (should return `answer_type='rag'`)
  - Logs and metadata_answer fields present and correct
- **Inputs:** Query strings and static `EXAMPLE_METADATA` (see test file)
- **Expected Output:** Correct routing, answer type, and logs

#### 2. `PromptTemplateSelector` (prompt template selection)
- **Purpose:** Ensures the correct prompt template is returned for thematic intent and that errors are raised for unknown intents.
- **Test Cases:**
  - Thematic intent returns the correct template with all key instructions
  - Factual template is not returned for thematic intent
  - ValueError is raised for unknown intent
- **Inputs:** Intent strings ('thematic', 'unknown_intent')
- **Expected Output:** Thematic template string for 'thematic', error for unknown

#### 3. Context Formatting (if applicable)
- **Purpose:** Ensures context is formatted as expected for thematic prompts, if a dedicated formatting helper exists.
- **Test Cases:**
  - Thematic context is formatted with all required fields and structure
- **Inputs:** Retrieved context chunks for thematic queries
- **Expected Output:** Properly formatted context string for the prompt
- **Note:** Review if a dedicated formatting helper exists for thematic context; add or update tests as needed.

#### 4. End-to-End Thematic Query Handling (Integration)
- **Purpose:** Simulates the full thematic query pipeline, including routing, retrieval, prompt construction, and LLM call (mocked), to ensure the entire pipeline works as expected.
- **Test Cases:**
  - Thematic query is routed, context is retrieved (mocked), prompt is constructed, and LLM call is made (mocked)
  - Checks that the answer, sources, and answer_type are correct in the final output
- **Inputs:** Thematic query string (e.g., "What are common themes in Nobel lectures?")
- **Expected Output:**
  - `answer_type` is 'rag'
  - The answer contains expected thematic content (e.g., mentions "justice")
  - Sources include correct metadata (e.g., laureate, text_snippet)

### 3. IntentClassifier (Unit)
- **Status:** ✅ Fully implemented in `tests/test_intent_classifier.py`.
- **Note:** All required unit tests for the IntentClassifier (factual, thematic, generative, precedence, case insensitivity, fallback, scoping) are present and comprehensive as of this review. No further action needed.

---

## Metadata Handler & Pattern Robustness

All factual query patterns in the metadata handler are now robust to extra trailing context (e.g., "Nobel Prizes in Literature") and punctuation. The test suite covers all pattern variants, including those with additional phrasing at the end of the query. The metadata flattening utility is now in `rag/metadata_utils.py` for lightweight import in tests and other modules.

Test collection and execution is now fast due to modularization and lazy loading of heavy resources.

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

## Test File: `test_theme_reformulator.py`

### What is Tested?

#### 1. `expand_query_terms`
- **Purpose:** Ensures that expansion includes canonical themes and all related keywords for a sample query, using lemmatization and theme mapping.
- **Test Cases:**
  - Query with multiple related theme keywords (e.g., "morality and truth")
  - Checks that all canonical and related keywords for matched themes are included in the expansion.
- **Inputs:** Sample queries containing theme-related words.
- **Expected Output:** Set of expanded keywords including all canonical and related terms for the matched themes.

#### 2. `expand_query_terms` (parametric, all keywords)
- **Purpose:** Ensures that for every theme and every keyword in `themes.json`, the expansion includes both the canonical theme and the original keyword.
- **Test Cases:**
  - For each theme and each keyword, query with that keyword and check expansion.
- **Inputs:** All theme keywords from `themes.json`.
- **Expected Output:** Expansion includes the canonical theme and the original keyword for every input.

- **Note:** Retrieval configuration for thematic queries (i.e., `RetrievalConfig(top_k=15, score_threshold=None)`) is explicitly checked in the comprehensive thematic routing test (`test_router_thematic_query_comprehensive`), so no separate test is needed for this logic. 