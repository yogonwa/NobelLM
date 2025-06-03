# RAG Test Coverage Plan for NobelLM

This document outlines a comprehensive testing strategy for the NobelLM Retrieval-Augmented Generation (RAG) pipeline. It includes ideal test coverage tiers, purpose, and status. Existing tests are reviewed and annotated for alignment and gaps. Missing tests are scaffolded with placeholder names and pseudocode.

---

## 🔍 Overview of RAG Pipeline

```
[User Query]
     ↓
[Intent Classifier] → intent type (factual / hybrid / thematic)
     ↓
[Query Router] → selects retriever + top_k strategy
     ↓
[Retriever]
  └── [Embed Query]
  └── [Metadata Filter]
  └── [Vector Search (FAISS)]
     ↓
[Relevant Chunks]
     ↓
[Prompt Builder]
     ↓
[LLM Call (optional in dry_run)]
     ↓
[Answer Compiler]
     ↓
[Final Response]
```

---

## ✅ 1. Unit Tests

### intent\_classifier.py

* **✅ `test_intent_classifier.py`**: Covers classification for factual, thematic, hybrid phrasing, malformed inputs, international queries. All required unit tests present and passing. 6/2

### query\_router.py

* **✅ `test_query_router.py`**: Tests routing from intent, fallback strategies, invalid intent input, missing/malformed filters. All required unit tests present and passing. 6/2

### retriever.py / dual\_process\_retriever.py

* **✅ `test_retriever.py`**: Covers retrieval with valid filters, zero vector handling, dual-process retriever subprocess success and error handling. All required unit tests present and passing. 6/2

### query\_index()

* **✅ `test_retriever.py`**: Covers top_k result count, correct metadata, and missing index error handling. All required unit tests present and passing. 6/2

### metadata\_handler.py

* **✅ `test_metadata_handler.py`**: All factual query patterns and variants are covered. Edge cases for unknown laureate/country and fallbacks for zero matches are tested. Compound/nested filter logic is tested via manual filtering (handler does not natively support compound filters—should be updated for full coverage). All required unit tests present and passing. 6/2 


### prompt_utils / utils.py

* **✅ `test_utils.py`**: format_chunks_for_prompt is fully tested, including fallback for missing metadata and empty chunk list. All required unit tests present and passing. 6/2

### answer_compiler.py

* **✅ `test_answer_compiler.py`**: Covers answer compilation for both RAG and metadata (factual, thematic, hybrid). Tests output structure, answer content, sources, and fallbacks for no relevant chunks. All required unit tests present and passing. 6/2

### theme_reformulator.py

* **✅ `test_theme_reformulator.py`**: Covers expansion for canonical themes and all related keywords, parametric coverage for all keywords, empty set for no matches, and case insensitivity. All required unit tests present and passing. 6/2

✅ 2. Integration Tests

intent_classifier + query_router

⛔ Missing → Add:

# test_intent_to_router.py

def test_routing_from_thematic_intent():
    # Check top_k and retriever selection for thematic query
    pass

query_router + retriever

Partial in test_query_engine.py

🔧 Needs: Explicit tests for top_k tuning and filter propagation.

retriever + query_index

⛔ Missing → Covered by test_query_index.py if added.

prompt builder + compiler

⛔ Missing → Add:

# test_prompt_to_compiler.py

def test_prompt_contains_all_sources():
    # Validate source text appears in prompt and final answer
    pass

✅ 3. End-to-End Tests

test_query_engine.py

✅ Exists

🔧 Needs:

Clear labels for factual, hybrid, thematic

Better assertions (not just "term in answer")

Use fixtures for stability and reproducibility

@pytest.mark.parametrize("user_query, filters, expected_k, dry_run", [...])
def test_query_engine_e2e(...):
    # Validate prompt generation, top_k, and response
    pass

✅ 4. Failure Tests

Failure & Edge Cases

⛔ Missing → Add:

# test_failures.py

def test_empty_query():
    # Should return helpful message, not crash
    pass

def test_missing_index_file():
    # Simulate FAISS index file not found
    pass

def test_zero_vector_handling():
    # Test that a zero vector is logged and handled
    pass

📦 Additional Infrastructure

Use mock chunks and metadata fixtures in tests/fixtures/.

Create config toggles for test vs. live (DRY_RUN, TEST_MODE).

Inject fake query embeddings for deterministic testing.
