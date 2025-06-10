# Nobel Laureate Speech Explorer - Test Suite Documentation

## Table of Contents
- [Environment Setup](#environment-setup)
- [Test Architecture](#test-architecture)
- [Test Coverage](#test-coverage)
- [Test Categories](#test-categories)
- [Best Practices](#best-practices)
- [Future Improvements](#future-improvements)

## Environment Setup

### Platform-Specific Configuration
The test suite supports dual-process FAISS retrieval for Mac/Intel systems to prevent segfaults:

```bash
# On Mac/Intel (avoid segfaults):
export NOBELLM_USE_FAISS_SUBPROCESS=1
pytest

# On Linux/CI (faster):
export NOBELLM_USE_FAISS_SUBPROCESS=0  # or leave unset
pytest
```

You can also configure this programmatically in test setup:
```python
import os
os.environ["NOBELLM_USE_FAISS_SUBPROCESS"] = "0"  # For explicit control
```

> **Note**: See `main/README.md` and `rag/README.md` for detailed information about the environment toggle and dual-mode retrieval logic.

## Test Architecture

### Model-Aware, Config-Driven Testing
All tests for chunking, embedding, and RAG are model-aware and config-driven. The embedding model, FAISS index, and chunk metadata paths are centrally managed in `rag/model_config.py`.

Tests must:
- Use `get_model_config()` to obtain model names, file paths, and dimensions
- Be parameterized over supported models to ensure robustness
- Avoid hardcoding model-specific values

## Test Coverage

The test suite follows the core pipeline flow:
1. Extraction & Parsing
2. Intent Classification
3. Metadata Direct Answer
4. Chunking/Embeddings
5. Retrieval
6. Thematic Analysis
7. RAG Pipeline
8. Frontend E2E
9. Cross-Cutting Tests

## Test Categories

### 1. Extraction & Parsing Tests 
####`test_scraper.py`
**Coverage:**
- `extract_life_and_work_blurbs`
- `infer_gender_from_text`
- `extract_metadata`

**Purpose:** Validate HTML parsing and data extraction robustness

### 2. Intent Classification & Query Routing
#### `test_intent_classifier.py`
- Query type classification (factual, thematic, generative)
- Laureate scoping
- Precedence rules
- Edge cases

#### `test_query_router.py`
- Fallback strategies (metadata to RAG)
- Intent routing
- Prompt template selection
- End-to-end routing tests

#### `test_prompt_template.py`
- Prompt template correctness for all intent types

### 3. Metadata Query Tests (`test_metadata_handler.py`)
- Factual query pattern coverage
- Edge cases for unknown laureate/country
- Fallback behavior validation

### 4. Chunking & Embedding Tests
**Recommended Test Files:**
- `test_chunking.py` (Schema validation, metadata completeness)
- `test_embeddings.py` (File shape and dimension validation)
- `test_index_build.py` (FAISS index integrity)

### 5. Retrieval Layer Tests
#### `test_retriever.py`
- Standard retrieval functionality
- Dual-process vs single-process retrieval
- Model-aware retrieval
- I/O error handling

#### `test_retriever_to_query_index.py`
- Integration: `retrieve_chunks` → `query_index`
- Filter propagation
- Score threshold + min_k fallback
- Invalid embedding handling

### 6. Thematic Retrieval & Context Formatting
#### `test_utils.py`
- `format_chunks_for_prompt` utility validation

#### `test_context_formatting.py`
- Context formatting helpers

**Recommended Addition:**
- `test_thematic_retriever.py` for:
  - Deduplication
  - Score filtering
  - Expanded terms
  - Output schema validation

### 7. RAG Pipeline & Prompt Assembly
#### `test_answer_compiler.py`
- RAG answer compilation logic
- Output validation (answer, sources, metadata_answer)

**Recommended Addition:**
- `test_rag_pipeline.py` for:
  - Full (non-mocked) RAG query validation
  - End-to-end RAG flow verification

### 8. End-to-End Frontend Contract Tests
#### `test_e2e_frontend_contract.py`
- Full user query → answer flow validation:
  - Factual queries
  - Thematic queries
  - Generative queries
  - No-results handling
  - Error scenarios
- Frontend output contract stability

### 9. Cross-Cutting Tests
- `test_retriever.py`: Dual-process path switching
- `test_query_router.py`: Path switching and fallback consistency
- `test_retriever_to_query_index.py`: Filter propagation and retrieval behavior

## Best Practices

### Model Parameterization Example
```python
import pytest
from rag.model_config import MODEL_CONFIGS, get_model_config

@pytest.mark.parametrize("model_id", list(MODEL_CONFIGS.keys()))
def test_chunking_output_schema(model_id):
    config = get_model_config(model_id)
    # Use config["model_name"], config["index_path"], etc.
    # ... test logic ...
```

### Key Guidelines
1. Avoid hardcoding model names, file paths, or dimensions
2. Make all tests model-aware and future-proof
3. Regularly test dual-process retrieval toggle for Mac/Linux consistency
4. Use logging instead of print statements
5. Include descriptive error messages
6. Avoid catching broad exceptions

## Future Improvements
1. Implement `test_thematic_retriever.py`
2. Add comprehensive model-aware validation tests:
   - `test_chunking.py`
   - `test_embeddings.py`
   - `test_index_build.py`
3. Add `test_rag_pipeline.py` for stable RAG result validation