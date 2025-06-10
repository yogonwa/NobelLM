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

* **✅ `test_intent_classifier.py`**: Covers classification for factual, thematic, hybrid phrasing, malformed inputs, international queries. All required unit tests present and passing. 6/8

### query\_router.py

* **✅ `test_query_router.py`**: Tests routing from intent, fallback strategies, invalid intent input, missing/malformed filters. All required unit tests present and passing. 6/8

### retriever.py / dual\_process\_retriever.py

* **✅ `test_retriever.py`**: Covers:
  - Standard retrieval with valid filters, zero vector handling
  - **NEW: Dual-process path switching and consistency**
  - **NEW: Large query handling (10KB)**
  - **NEW: File I/O error scenarios**
  - **NEW: Model-aware retrieval for all supported models**
  - **NEW: Index type safety (is_supported_index())**
  - **NEW: Score threshold filtering and min/max return logic**
  - All required unit tests present and passing. 6/8

### query\_index()

* **✅ `test_retriever.py`**: Covers:
  - Top_k result count and correct metadata
  - Missing index error handling
  - **NEW: Standard default top_k behavior**
  - **NEW: Model-specific path handling**
  - **NEW: IndexFlatIP requirement for filtered queries**
  - **NEW: Score threshold filtering**
  - All required unit tests present and passing. 6/8

### metadata\_handler.py

* **✅ `test_metadata_handler.py`**: All factual query patterns and variants are covered. Edge cases for unknown laureate/country and fallbacks for zero matches are tested. Compound/nested filter logic is tested via manual filtering (handler does not natively support compound filters—should be updated for full coverage). All required unit tests present and passing. 6/8

### prompt_utils / utils.py

* **✅ `test_utils.py`**: Covers:
  - format_chunks_for_prompt (existing)
  - **NEW: filter_top_chunks() with all cases:**
    - No filtering needed (all chunks above threshold)
    - Some chunks below threshold
    - Fewer than min_return chunks pass threshold
    - max_return enforced
    - Empty chunk list
    - Invalid score handling
  - All required unit tests present and passing. 6/8

### answer_compiler.py

* **✅ `test_answer_compiler.py`**: Unit tests for answer compilation logic. Covers:
  - RAG answer compilation for factual, thematic, and hybrid queries
  - Metadata answer handling
  - Output structure validation (answer, sources, metadata_answer)
  - Model-aware retrieval configuration
  - Fallback behavior for no relevant chunks
  - All required unit tests present and passing. 6/8

### theme_reformulator.py

* **✅ `test_theme_reformulator.py`**: Covers expansion for canonical themes and all related keywords, parametric coverage for all keywords, empty set for no matches, and case insensitivity. All required unit tests present and passing. 6/8

### prompt_template.py

* **✅ `test_prompt_template.py`**: Unit tests for PromptTemplateSelector. Covers factual, thematic, generative, and error handling. All tests present and passing. 6/8

### context_formatting.py

* **✅ `test_context_formatting.py`**: Unit tests for context formatting helpers. Covers factual and thematic context formatting. All tests present and passing. 6/8

### answer_query.py

* **✅ `test_answer_query.py`**: Unit tests for the canonical `answer_query()` function. Covers:
  - Metadata answer handling
  - RAG answer compilation
  - Model-aware retrieval configuration
  - Score threshold consistency
  - All required unit tests present and passing. 6/8

### scraper.py

* **✅ `test_scraper.py`**: Unit tests for web scraping and data extraction. Covers:
  - HTML parsing and metadata extraction
  - Life and work blurb extraction
  - Gender inference from text
  - Edge cases and error handling
  - All required unit tests present and passing. 6/8

### utils_intent.py

* **✅ `test_utils_intent.py`**: Unit tests for intent classification utilities. Covers:
  - Intent classification helper functions
  - Query preprocessing
  - All required unit tests present and passing. 6/8

## ✅ 2. Integration Tests

### intent_classifier + query_router

* **✅ `test_intent_to_router.py`**: Integration test present and passing. Verifies that a thematic query is correctly classified and routed by the QueryRouter, with correct intent, answer_type, and top_k (15) for thematic queries. Test present and passing 6/8.

### query_router + retriever

* ** test_query_router_to_retriever_integration.py


### retriever + query_index

* **✅ `test_retriever_to_query_index.py`**: Integration tests for:
  - retrieve_chunks → query_index argument propagation
  - Filter propagation
  - No results handling
  - Output schema validation
  - **NEW: Score threshold filtering and min/max return**
  - **NEW: IndexFlatIP requirement for filtered queries**
  - **NEW: Model-aware path handling**
  - **NEW: Dual-process vs single-process consistency**
  - All tests present and passing 6/9

### faiss_query_worker (subprocess integration)

* **✅ `test_faiss_query_worker.py`**: Integration test for subprocess-based FAISS retrieval. Runs the worker as a subprocess with a temp FAISS index, metadata, and filters. Asserts only matching chunks are returned, subprocess uses provided paths, and no global state is affected. Required for Mac/Intel dual-process support. Test present and passing 6/3.

### prompt builder + compiler

* **✅ `test_prompt_to_compiler.py`**: Integration test for prompt builder → answer compiler. Ensures all source chunks and their metadata are included in the prompt, the user query is present, and the prompt structure is correct. Asserts that all chunk texts, laureate names, years, and source types are present in the prompt. All required integration tests present and passing. 6/9

## ✅ 3. End-to-End Tests

### e2e_frontend_contract.py
* **✅ `test_e2e_frontend_contract.py`**: End-to-end tests for:
  - User query to frontend output contract
  - **NEW: Score threshold filtering**
  - **NEW: Model-aware retrieval**
  - All user-facing scenarios covered
  - All required E2E tests present and passing. 6/3

## ✅ 4. Failure Tests

### test_failures.py
* **✅ `test_failures.py`**: Covers:
  - Empty query handling
  - Missing index file
  - Zero vector handling
  - Model config mismatch
  - Large query handling
  - **NEW: Unsupported index type (IVF/PQ)**
  - **NEW: Score threshold edge cases**
  - All required failure tests present and passing. 6/3

## ✅ 5. Legacy and Compatibility Tests

### test_query_router_LEGACY.py
* **✅ `test_query_router_LEGACY.py`**: Legacy tests for query router functionality. Covers:
  - Metadata match and no-match scenarios
  - Thematic query routing
  - Logs and field validation
  - Comprehensive thematic query testing
  - All required legacy tests present and passing. 6/3

### test_retriever_LEGACY.py
* **✅ `test_retriever_LEGACY.py`**: Legacy tests for retriever functionality. Covers:
  - Legacy retrieval patterns
  - Backward compatibility
  - All required legacy tests present and passing. 6/3

## ✅ 6. Sanity Check Tests

### faiss_index_sanity_check.py
* **✅ `faiss_index_sanity_check.py`**: Sanity check for FAISS index integrity. Covers:
  - Index loading and basic operations
  - Vector dimension validation
  - All required sanity checks present and passing. 6/3

### embedder_sanity_check.py
* **✅ `embedder_sanity_check.py`**: Sanity check for embedding model functionality. Covers:
  - Model loading and embedding generation
  - Vector dimension consistency
  - All required sanity checks present and passing. 6/3

### e2e_embed_faiss_sanity_check.py
* **✅ `e2e_embed_faiss_sanity_check.py`**: End-to-end sanity check for embedding and FAISS pipeline. Covers:
  - Full embedding → FAISS → retrieval pipeline
  - Integration validation
  - All required sanity checks present and passing. 6/3

## 📦 Additional Infrastructure

Use mock chunks and metadata fixtures in tests/fixtures/.

Create config toggles for test vs. live (DRY_RUN, TEST_MODE).

Inject fake query embeddings for deterministic testing.

**NEW: Model-aware test fixtures:**
- Add model-specific test data in tests/fixtures/{model_id}/
- Include sample chunks, embeddings, and metadata for each model
- Use in parameterized tests to verify model-specific behavior

## 📋 Deprecated/Removed Test Files

The following test files have been deprecated and their functionality is now covered by other test files:

* **❌ `test_query_engine.py`**: Functionality now covered by:
  - `test_answer_compiler.py` - answer compilation logic
  - `test_answer_query.py` - answer_query() function
  - `test_e2e_frontend_contract.py` - end-to-end query processing

* **❌ `test_prompt_builder.py`**: Functionality now covered by:
  - `test_prompt_template.py` - prompt template selection
  - `test_prompt_to_compiler.py` - prompt builder → answer compiler integration
  - `test_context_formatting.py` - context formatting helpers
