# Tests for Nobel Laureate Speech Explorer

## 🚦 Test Progress & Environment-Aware Execution (2025)

- **Dual-process FAISS retrieval is now supported for Mac/Intel:**
  - Set `export NOBELLM_USE_FAISS_SUBPROCESS=1` before running tests to avoid segfaults.
  - On Linux/CI, leave this variable unset or set to `0` for faster, unified in-process tests.
- **All tests are model-aware and config-driven.**
- **Test coverage includes:**
  - Extraction/parsing logic
  - Intent classification and routing
  - End-to-end RAG pipeline (dry run and live)
  - Thematic expansion and chunk formatting

**Helper for contributors:**
```bash
# On Mac/Intel (avoid segfaults):
export NOBELLM_USE_FAISS_SUBPROCESS=1
pytest

# On Linux/CI (faster):
export NOBELLM_USE_FAISS_SUBPROCESS=0  # or leave unset
pytest
```
- You can also set this in test setup with `os.environ["NOBELLM_USE_FAISS_SUBPROCESS"] = "0"` for explicit control.
- See the main README.md and rag/README.md for more details on the environment toggle and dual-mode retrieval logic.

---

## Model-Aware, Config-Driven Testing (NEW)

All tests for chunking, embedding, and RAG are now **model-aware and config-driven**. The embedding model, FAISS index, and chunk metadata paths are centrally managed in `rag/model_config.py`:

- Tests should use `get_model_config` to obtain model names, file paths, and dimensions.
- Where relevant, tests should be parameterized to run for all supported models (e.g., MiniLM, BGE-Large).
- This ensures that all code paths are robust to model switching and that outputs are correct for each model.
- Avoid hardcoding file names, model names, or dimensions in tests—always use the config.

**Example (pytest parametrize):**
```python
import pytest
from rag.model_config import get_model_config

@pytest.mark.parametrize("model_id", list(get_model_config().keys()))
def test_chunking_output_schema(model_id):
    config = get_model_config(model_id)
    # Use config["model_name"], config["index_path"], etc.
    # ... test logic ...
```

**To add a new model:**
- Add its config to `rag/model_config.py`.
- All model-aware tests will pick it up automatically.

---

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
  - Edge cases (ambiguous, partial, malformed, international, hybrid phrasing)
- **Inputs:** Query strings
- **Expected Output:** Correct intent classification and scoping for all cases

---

## Test File: `test_query_router.py`

### What is Tested?

- Fallback strategies (metadata to RAG)
- Invalid intent input (raises ValueError)
- Thematic/factual/generative routing
- Logs, config, and prompt template selection
- Missing/malformed filters in thematic routing
- End-to-end pipeline integration (mocked)
- All required unit tests present and passing

#### 1. `extract_life_and_work_blurbs`
# ... existing code ...

#### 5. `test_end_to_end_thematic_and_factual_query`
- **Purpose:** Integration test for the full pipeline for both thematic and factual queries (mocked retrieval and LLM). Also includes a placeholder for generative queries.
- **Inputs:**
  - Thematic query: "What are common themes in Nobel lectures?"
  - Factual query: "What year did Toni Morrison win?"
- **Expected Output:**
  - Thematic: `answer_type` is 'rag', answer contains 'justice', source includes 'Toni Morrison'.
  - Factual: `answer_type` is 'metadata', answer contains '1993', metadata includes 'Toni Morrison'.
  - Generative: Placeholder for future implementation.

#### 6. `test_answer_query_unit`
- **Purpose:** Unit test for `answer_query`, mocking all dependencies to check output schema and correctness.
- **Inputs:** Query string (e.g., "Who won the Nobel Prize in 2017?")
- **Expected Output:**
  - `answer_type` is 'metadata', answer contains '2017', metadata includes 'Kazuo Ishiguro'.

#### 7. Multi-field filter propagation
- **Purpose:** Ensures that when multiple filters (e.g., {"country": "USA", "source_type": "nobel_lecture"}) are passed, they are correctly propagated to the retriever. The test checks only output fields (e.g., chunk_id, text_snippet) in the final answer, not internal metadata fields, to align with privacy and output schema requirements.
- **Test Cases:**
  - Query with multiple filters
- **Inputs:** Query string, filter dict with multiple fields
- **Expected Output:**
  - All returned chunks have correct output fields (e.g., chunk_id, text_snippet) and match the expected output schema
  - Internal metadata fields are not exposed in the output
- **Status:** Test present and passing

## Test File: `test_retriever.py`

### What is Tested?

- Retrieval with valid filters (mocked FAISS and metadata)
- Handling of zero vector (raises ValueError)
- Dual-process retriever returns results (mocked subprocess and file I/O)
- Dual-process retriever handles subprocess error (raises RuntimeError)
- query_index returns correct top_k results and metadata (mocked)
- query_index raises FileNotFoundError if index is missing
- All required unit tests present and passing

## Test File: `test_metadata_handler.py`

### What is Tested?

- All factual query patterns and variants are covered
- Edge cases for unknown laureate/country
- Compound/nested filter logic is tested via manual filtering (handler does not natively support compound filters)
- Fallbacks for zero matches are tested
- Note: Handler should be updated to natively support compound filters for full coverage
- All current required unit tests present and passing

## Test File: `test_utils.py`

### What is Tested?

- format_chunks_for_prompt is fully tested
- Covers: all metadata present, missing metadata fallback, custom template, empty chunk list, all metadata missing
- All required unit tests present and passing

## Test File: `test_prompt_builder.py`
- **Purpose:** Unit tests for prompt building logic. Ensures all fields and formatting are correct for all query types.
- **Test Cases:** Factual, thematic, generative, edge cases (missing fields, empty chunks).
- **Status:** All required unit tests present and passing.

## Test File: `test_answer_compiler.py`
- **Purpose:** Unit tests for answer compilation logic. Ensures output schema, answer content, and source formatting are correct.
- **Test Cases:** RAG, metadata, hybrid, no relevant chunks.
- **Status:** All required unit tests present and passing.

## Test File: `test_e2e_frontend_contract.py`
- **Purpose:** End-to-end test for user query → answer, validating the full output contract expected by the frontend.
- **Test Cases:** Factual, thematic, generative, no results, empty query, error handling.
- **Status:** All required E2E tests present and passing.

## Test File: `test_retriever_to_query_index.py`

### What is Tested?

- **Integration test for retrieve_chunks → query_index**
- Ensures that retrieve_chunks calls query_index with correct arguments (embedding, top_k, filters, model_id)
- Tests filter propagation (single and multi-field)
- Handles no results (empty list)
- Asserts output schema (required fields present)
- **Score threshold filtering:** Only returns chunks above score_threshold unless fallback is triggered
- **min_k fallback:** If too few chunks pass the threshold, returns at least min_k chunks
- **Invalid embedding handling:** Raises ValueError for invalid (all-zeros) embedding
- **Status:** All tests present and passing

---

## Test File: `test_prompt_template.py`
- **Purpose:** Unit tests for PromptTemplateSelector. Ensures correct template is returned for each intent and that error handling is robust.
- **Test Cases:** Factual, thematic, generative, unknown intent.
- **Status:** All required unit tests present and passing.

## Test File: `test_context_formatting.py`
- **Purpose:** Unit tests for context formatting helpers. Ensures correct formatting for factual and thematic contexts.
- **Test Cases:** All fields present, missing fields, custom templates.
- **Status:** All required unit tests present and passing.

## TODO: Model-Aware Test Coverage (Recommended)

The following tests are recommended to ensure robust, model-aware coverage for the full pipeline:

- **Chunking Output Tests:**
  - Add `test_chunking.py` to validate the output schema and content of chunk files (`chunks_literature_labeled_{model}.jsonl`) for all supported models.
  - Parameterize over all models using `get_model_config`.

- **Embedding File Tests:**
  - Add `test_embeddings.py` to check that embedding files (`literature_embeddings_{model}.json`) are present, have correct shape, and match the config dimension for each model.

- **FAISS Index Build Tests:**
  - Add `test_index_build.py` to verify that the FAISS index and metadata files exist, are readable, and have the correct dimension for each model.

- **End-to-End RAG Pipeline Tests:**
  - Add `test_rag_pipeline.py` to run a real (non-mocked) RAG query using the actual index and embeddings for at least one model, and check that results are returned and have the expected schema.

- **General:**
  - All new tests should use `get_model_config` and be parameterized for all supported models.
  - Avoid hardcoding file names, model names, or dimensions in tests.

These additions will ensure the codebase is robust to model switching and that all outputs are correct for each supported model. 