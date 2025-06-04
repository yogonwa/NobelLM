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

### prompt_template.py

* **✅ `test_prompt_template.py`**: Unit tests for PromptTemplateSelector. Covers factual, thematic, generative, and error handling. All tests present and passing.

### context_formatting.py

* **✅ `test_context_formatting.py`**: Unit tests for context formatting helpers. Covers factual and thematic context formatting. All tests present and passing.

### prompt_builder.py
* **✅ `test_prompt_builder.py`**: Unit tests for prompt building logic. Covers all query types and edge cases.

### answer_compiler.py
* **✅ `test_answer_compiler.py`**: Unit tests for answer compilation logic. Covers all output types and edge cases.

## ✅ 2. Integration Tests

### intent_classifier + query_router

* **✅ `test_intent_to_router.py`**: Integration test present and passing. Verifies that a thematic query is correctly classified and routed by the QueryRouter, with correct intent, answer_type, and top_k (15) for thematic queries. Test present and passing 6/3.

### query_router + retriever

* **✅ `test_query_router_to_retriever.py`**: Integration tests for filter propagation, top_k tuning, and chunk schema. Includes tests for single-field and multi-field filters (e.g., {"country": "USA", "source_type": "nobel_lecture"}), asserting all returned chunks match the expected output fields (not internal metadata). Output schema is privacy-preserving. Test present and passing 6/3.

### retriever + query_index

* **✅ `test_retriever_to_query_index.py`**: Integration tests for retrieve_chunks → query_index. Covers argument propagation, filter propagation, no results, output schema, score threshold filtering, min_k fallback, and invalid embedding handling. All tests present and passing 6/3.

### faiss_query_worker (subprocess integration)

* **✅ `test_faiss_query_worker.py`**: Integration test for subprocess-based FAISS retrieval. Runs the worker as a subprocess with a temp FAISS index, metadata, and filters. Asserts only matching chunks are returned, subprocess uses provided paths, and no global state is affected. Required for Mac/Intel dual-process support. Test present and passing 6/3.

### prompt builder + compiler

* **✅ `test_prompt_to_compiler.py`**: Integration test for prompt builder → answer compiler. Ensures all source chunks and their metadata are included in the prompt, the user query is present, and the prompt structure is correct. Asserts that all chunk texts, laureate names, years, and source types are present in the prompt. All required integration tests present and passing. 6/3

✅ 3. End-to-End Tests

### e2e_frontend_contract.py
* **✅ `test_e2e_frontend_contract.py`**: End-to-end tests for user query to frontend output contract. Covers all user-facing scenarios.

✅ 4. Failure Tests

### Failure & Edge Cases

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
