# Nobel Laureate Speech Explorer - Test Suite Documentation

## Table of Contents
- [Environment Setup](#environment-setup)
- [Test Architecture](#test-architecture)
- [Test Coverage](#test-coverage)
- [Test Categories](#test-categories)
- [Running Tests](#running-tests)
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

### Test Organization
The test suite is organized into four main categories:
- **Unit Tests** (`unit/`): Individual component testing
- **Integration Tests** (`integration/`): Component interaction testing
- **End-to-End Tests** (`e2e/`): Full workflow validation
- **Validation Tests** (`validation/`): Data quality and schema validation

## Test Coverage

The test suite follows the core pipeline flow:
1. Extraction & Parsing
2. Intent Classification (including Phase 2 modernization)
3. **Theme Embedding Infrastructure (Phase 3A - NEW)**
4. Metadata Direct Answer
5. Chunking/Embeddings
6. Retrieval
7. Thematic Analysis
8. RAG Pipeline
9. Frontend E2E
10. Cross-Cutting Tests

**Phase 2 Intent Classifier Tests:**
- `test_intent_classifier.py`: Comprehensive coverage of new structured intent classification
- Tests for hybrid confidence scoring, config-driven weights, multiple laureate detection
- Validation of decision traces, lemmatization integration, and backward compatibility

**Phase 3A Theme Embedding Infrastructure Tests:**
- `test_theme_embedding_infrastructure.py`: Core theme embedding and similarity computation infrastructure
- `test_theme_reformulator_phase3.py`: Enhanced ThemeReformulator with ranked expansion
- Tests for pre-computed embeddings, model-aware storage, quality filtering
- Validation of hybrid keyword extraction, fallback behavior, and performance benchmarks

**Phase 3B Enhanced ThematicRetriever Tests:**
- `test_thematic_retriever.py`: Enhanced ThematicRetriever with weighted retrieval functionality
- Tests for similarity-based ranked expansion integration, exponential weight scaling
- Validation of weighted chunk merging, deduplication, and sorting
- Backward compatibility testing with legacy retrieval methods
- Performance monitoring and logging validation
- Error handling and fallback behavior testing
- Comprehensive coverage of dual retrieval architecture (weighted vs legacy)

## Test Categories

### 1. Unit Tests (`unit/`)
Individual component testing with mocked dependencies.

#### `test_scraper.py`
**Coverage:**
- `extract_life_and_work_blurbs`
- `infer_gender_from_text`
- `extract_metadata`

**Purpose:** Validate HTML parsing and data extraction robustness

#### `test_intent_classifier.py`
- Query type classification (factual, thematic, generative)
- Laureate scoping
- Precedence rules
- Edge cases
- **Phase 2 Intent Classifier Modernization Tests**
- Structured `IntentResult` object validation
- Hybrid confidence scoring with pattern strength and ambiguity penalty
- Config-driven keyword/phrase weight testing
- Multiple laureate detection and deduplication
- Lemmatization integration and fallback behavior
- Decision trace logging and transparency
- Backward compatibility with legacy `classify_legacy()` method
- Confidence threshold validation and edge cases
- Comprehensive test coverage for all new Phase 2 features

#### `test_theme_reformulator_phase3.py` (NEW - Phase 3A)
- **Phase 3A Theme Embedding Infrastructure Tests**
- Enhanced ThemeReformulator with ranked expansion functionality
- Similarity-based expansion with quality filtering and threshold validation
- Hybrid keyword extraction (theme keywords → preprocessed → full query)
- Backward compatibility with existing `expand_query_terms()` method
- Fallback behavior when similarity computation fails
- Performance testing (<100ms expansion time for typical queries)
- Model-aware functionality (bge-large vs miniLM)
- Lazy loading of theme embeddings and embedding models
- Comprehensive logging and monitoring validation
- Expansion statistics and debugging functionality

#### `test_query_router.py`
- Fallback strategies (metadata to RAG)
- Intent routing
- Prompt template selection
- End-to-end routing tests

#### `test_prompt_template.py`
- Prompt template correctness for all intent types

#### `test_metadata_handler.py`
- Factual query pattern coverage
- Edge cases for unknown laureate/country
- Fallback behavior validation

#### `test_chunking.py`
- Schema validation, metadata completeness
- Chunking logic and boundary detection

#### `test_embeddings.py`
- File shape and dimension validation
- Embedding generation and storage

#### `test_index_build.py`
- FAISS index integrity
- Index building and validation

#### `test_utils.py`
- `format_chunks_for_prompt` utility validation
- General utility function testing

#### `test_context_formatting.py`
- Context formatting helpers
- Prompt assembly utilities

#### `test_thematic_retriever.py` (NEW - Phase 3B)
- **Phase 3B Enhanced ThematicRetriever Tests**
- Weighted retrieval with similarity-based ranked expansion integration
- Exponential weight scaling validation (`exp(2 * similarity_score)`)
- Weighted chunk merging, deduplication, and sorting logic
- Backward compatibility testing with legacy retrieval methods
- Dual retrieval architecture testing (weighted vs legacy modes)
- Source term attribution and performance monitoring validation
- Error handling and fallback behavior testing
- Comprehensive logging and debugging functionality
- Model-aware functionality (bge-large vs miniLM)
- Performance benchmarks and monitoring validation
- Integration testing between Phase 3A theme embeddings and Phase 3B weighted retrieval

#### `test_answer_compiler.py`
- RAG answer compilation logic
- Output validation (answer, sources, metadata_answer)

### 2. Integration Tests (`integration/`)
Component interaction testing with realistic data flow.

#### `test_answer_query_integration.py`
- Complete `answer_query` pipeline testing
- Query routing integration
- Retriever selection and execution
- LLM integration and response handling
- Error handling and logging validation
- Metadata answer path testing
- RAG answer path testing

#### `test_faiss_query_worker.py`
- FAISS query worker subprocess integration
- Query embedding and index querying
- Result filtering and threshold validation
- Error handling and model configuration
- Subprocess communication testing

#### `test_prompt_to_compiler.py`
- Prompt building to answer compilation integration
- Query router to retriever integration
- Thematic retriever usage
- Metadata answer handling
- Error handling and empty result scenarios

#### `test_query_router_to_retriever_integration.py`
- Query router to retriever selection integration
- Model-aware retriever selection
- Thematic query RAG answer generation
- Dual process retrieval toggle testing
- Consistency validation
- Min/max return parameter propagation

#### `test_retriever_to_query_index.py`
- Integration: `retrieve_chunks` → `query_index`
- Filter propagation
- Score threshold + min_k fallback
- Invalid embedding handling
- Dual-process vs single-process retrieval
- Model-aware retrieval
- I/O error handling

### 3. End-to-End Tests (`e2e/`)
Full workflow validation with minimal mocking.

#### `test_e2e_frontend_contract.py`
- Full user query → answer flow validation:
  - Factual queries
  - Thematic queries
  - Generative queries
  - No-results handling
  - Error scenarios
- Frontend output contract stability

#### `test_theme_embedding_infrastructure.py` (NEW - Phase 3A E2E)
- **Phase 3A Core Infrastructure E2E Tests**
- ThemeEmbeddings class with model-aware storage and validation
- Theme similarity computation using existing safe_faiss_scoring pattern
- Pre-computed embedding storage and retrieval from disk
- Health checks for embedding quality and dimension consistency
- Model switching between bge-large and miniLM
- Error handling and edge cases for similarity computation
- Performance benchmarks and monitoring
- Integration testing between theme embeddings and similarity computation

#### `test_failures.py`
- Error scenario testing
- Failure mode validation

### 4. Validation Tests (`validation/`)
Data quality and schema validation.

#### `test_data_validation.py`
- Data schema validation
- Metadata completeness checks
- Embedding quality validation

## Running Tests

### Basic Test Execution
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/e2e/          # End-to-end tests only
pytest tests/validation/   # Validation tests only

# Run tests with specific markers
pytest -m unit             # Unit tests
pytest -m integration      # Integration tests
pytest -m e2e             # End-to-end tests
pytest -m validation      # Validation tests
```

### Test Configuration
The test suite uses `tests/pytest.ini` for configuration:
- Test discovery paths: `unit`, `integration`, `e2e`, `validation`
- Markers: `unit`, `integration`, `e2e`, `validation`, `performance`, `slow`, `legacy`
- Output: Verbose with short tracebacks
- Warnings: Deprecation warnings filtered

### Performance and Slow Tests
```bash
# Run only fast tests (exclude slow/performance)
pytest -m "not slow and not performance"

# Run performance tests only
pytest -m performance

# Run slow tests only
pytest -m slow
```

### Model-Specific Testing
```bash
# Test with specific model
pytest --model-id bge-large
pytest --model-id miniLM
```

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

### Integration Test Mocking
```python
@pytest.mark.integration
def test_component_integration():
    with patch('module.component') as mock_component:
        # Setup mock behavior
        mock_component.return_value = expected_result
        
        # Execute integration
        result = function_under_test()
        
        # Verify interactions
        mock_component.assert_called_once_with(expected_args)
        assert result == expected_result
```

### Key Guidelines
1. **Model Awareness**: Avoid hardcoding model names, file paths, or dimensions
2. **Config-Driven**: Use `get_model_config()` for all model-specific values
3. **Platform Compatibility**: Test dual-process retrieval toggle for Mac/Linux consistency
4. **Logging**: Use logging instead of print statements
5. **Error Messages**: Include descriptive error messages
6. **Exception Handling**: Avoid catching broad exceptions
7. **Mocking**: Use appropriate mocking levels for each test category
8. **Performance**: Keep integration tests under 30 seconds each
9. **Documentation**: Document complex test scenarios and edge cases

### Test Naming Conventions
- Unit tests: `test_function_name_scenario`
- Integration tests: `test_component_to_component_integration`
- E2E tests: `test_full_workflow_scenario`
- Validation tests: `test_data_quality_validation`

## Future Improvements

### Immediate Priorities
1. **Add comprehensive model-aware validation tests:**
   - Enhanced `test_chunking.py` with schema validation
   - Enhanced `test_embeddings.py` with dimension validation
   - Enhanced `test_index_build.py` with integrity checks

2. **Add `test_rag_pipeline.py` for stable RAG result validation:**
   - Full (non-mocked) RAG query validation
   - End-to-end RAG flow verification
   - Performance benchmarking

3. **Expand integration test coverage:**
   - More edge cases in component interactions
   - Error propagation testing
   - Performance regression testing

### Long-term Enhancements
1. **Automated Performance Testing:**
   - CI/CD integration for performance regression detection
   - Automated benchmarking and reporting

2. **Enhanced Mocking Infrastructure:**
   - Shared mock fixtures for common scenarios
   - Mock data generators for realistic testing

3. **Test Data Management:**
   - Automated test data generation
   - Test data versioning and validation

4. **Coverage Analysis:**
   - Integration with coverage tools
   - Coverage reporting and analysis

5. **Parallel Test Execution:**
   - Optimize test suite for parallel execution
   - Reduce overall test execution time