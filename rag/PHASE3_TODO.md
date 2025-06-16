# Phase 3: Thematic Reformulation Expansion - Implementation TODO

**Date:** 2025-01-XX  
**Goal:** Transform ThemeReformulator from simple keyword expansion to intelligent semantic expansion with similarity-based ranking and quality filtering.

---

## 🎯 **Phase 3A: Core Infrastructure (Day 1)** ✅ **COMPLETED**

### **1. Theme Embedding Infrastructure** ✅
- [x] **Create `config/theme_embeddings.py`**
  - [x] Pre-compute embeddings for all theme keywords in `config/themes.json`
  - [x] Store embeddings in model-aware configuration (bge-large, miniLM)
  - [x] Add validation to ensure embeddings match model dimensions
  - [x] Implement caching for theme embeddings
  - [x] Add health checks for embedding consistency

- [x] **Create `config/theme_similarity.py`**
  - [x] Implement `compute_theme_similarities(query_embedding: np.ndarray) -> Dict[str, float]`
  - [x] Use existing `safe_faiss_scoring()` pattern for consistency
  - [x] Add similarity threshold validation
  - [x] Implement similarity score logging

### **2. Enhanced ThemeReformulator** ✅
- [x] **Add new methods to `config/theme_reformulator.py`**
  - [x] `expand_query_terms_ranked(query: str, similarity_threshold: float = 0.3) -> List[Tuple[str, float]]`
  - [x] `_get_theme_focused_embedding(query: str) -> np.ndarray`
  - [x] `_preprocess_query_for_themes(query: str) -> str`
  - [x] `_rank_and_prune_expansions(expansions: Set[str], similarities: Dict[str, float], threshold: float) -> List[Tuple[str, float]]`

- [x] **Implement hybrid keyword extraction**
  - [x] Extract theme keywords first using existing `extract_theme_keywords()`
  - [x] If theme keywords found: embed only those keywords
  - [x] If no theme keywords: use preprocessed query (remove stopwords)
  - [x] Fallback to full query if preprocessing fails

- [x] **Add enhanced logging**
  - [x] Log similarity scores for each theme keyword
  - [x] Log pruning decisions and thresholds
  - [x] Log fallback usage (preprocessing vs full query)
  - [x] Add performance metrics (embedding time, similarity computation time)

---

## 🚀 **Phase 3B: ThematicRetriever Updates (Day 1-2)** ✅ **COMPLETED**

### **3. Enhanced ThematicRetriever** ✅
- [x] **Update `rag/thematic_retriever.py`**
  - [x] Modify `_expand_thematic_query()` to use `expand_query_terms_ranked()`
  - [x] Add `_weighted_retrieval(ranked_terms: List[Tuple[str, float]]) -> List[Dict]`
  - [x] Implement exponential weight scaling: `exp(2 * normalized_score)`
  - [x] Add `_merge_weighted_chunks(chunks: List[Dict]) -> List[Dict]`

- [x] **Implement weighted retrieval logic**
  - [x] Apply term weights to chunk scores during retrieval
  - [x] Boost final scores based on term importance
  - [x] Maintain chunk deduplication with weighted scoring
  - [x] Add source term attribution to chunks

- [x] **Enhanced logging and monitoring**
  - [x] Log term weights and retrieval performance
  - [x] Track expansion quality metrics
  - [x] Monitor fallback usage rates
  - [x] Add performance benchmarks

---

## 🔧 **Phase 3C: Optional Paraphraser (Day 2)** ❌ **DEFERRED**

### **4. Semantic Term Generation** ❌ **DEFERRED - NOT PLANNED**
- [ ] **Create `config/theme_paraphraser.py`** ❌ **DEFERRED**
  - [ ] Implement `generate_semantic_variants(theme: str) -> List[str]` ❌ **DEFERRED**
  - [ ] Add paraphraser model integration (e.g., T5-small for paraphrasing) ❌ **DEFERRED**
  - [ ] Implement caching for paraphraser outputs ❌ **DEFERRED**
  - [ ] Add fallback mechanisms for paraphraser failures ❌ **DEFERRED**

- [ ] **Integrate with ThemeReformulator** ❌ **DEFERRED**
  - [ ] Add `use_paraphraser: bool = False` parameter to `expand_query_terms_ranked()` ❌ **DEFERRED**
  - [ ] Generate semantic variants for high-similarity themes ❌ **DEFERRED**
  - [ ] Include variants in similarity ranking ❌ **DEFERRED**
  - [ ] Add paraphraser performance logging ❌ **DEFERRED**

**Note:** The paraphraser project has been explicitly deferred and is not planned for implementation. The current similarity-based expansion system provides sufficient semantic coverage without the complexity and performance overhead of a paraphraser model.

---

## 🧪 **Phase 3D: Comprehensive Test Suite Consolidation & Coverage (Day 1-3)** ✅ **IN PROGRESS**

**Goal:** Implement holistic, staff-level engineering approach to consolidate and enhance entire test suite, eliminating redundancy while ensuring comprehensive coverage of all Phase 2 & 3 functionality.

### **1. Test Suite Analysis & Consolidation** ✅ **COMPLETED**
- [x] **Analyze current test suite** (32 files total)
  - [x] Identify redundant legacy tests (5 files to remove)
  - [x] Map Phase 2 & 3 test coverage gaps
  - [x] Document test organization inconsistencies
  - [x] Create consolidation roadmap

- [x] **Create new directory structure**
  - [x] `tests/unit/` - Consolidated unit tests
  - [x] `tests/integration/` - Integration tests
  - [x] `tests/e2e/` - End-to-end tests
  - [x] `tests/validation/` - Data validation tests
  - [x] `tests/conftest.py` - Shared fixtures
  - [x] Update `tests/pytest.ini` configuration

### **2. Unit Test Consolidation** ✅ **COMPLETED**
- [x] **Consolidate Intent Classifier Tests**
  - [x] Merge `test_intent_classifier.py` (legacy) + `test_intent_classifier_phase2.py`
  - [x] Create `tests/unit/test_intent_classifier.py` with comprehensive coverage
  - [x] Test legacy functionality, Phase 2 enhancements, hybrid confidence scoring
  - [x] Validate multiple laureate detection and decision traces
  - [x] Remove redundant `test_intent_classifier.py` (legacy)

- [x] **Consolidate ThemeReformulator Tests**
  - [x] Merge `test_theme_reformulator.py` (legacy) + `test_theme_reformulator_phase3.py`
  - [x] Create `tests/unit/test_theme_reformulator.py` with comprehensive coverage
  - [x] Test legacy expansion, Phase 3A ranked expansion, similarity filtering
  - [x] Validate hybrid keyword extraction and fallback behavior
  - [x] Remove redundant `test_theme_reformulator.py` (legacy)

- [x] **Consolidate ThematicRetriever Tests**
  - [x] Rename `test_thematic_retriever_phase3.py` to `tests/unit/test_thematic_retriever.py`
  - [x] Add legacy retrieval tests for backward compatibility
  - [x] Ensure comprehensive Phase 3B weighted retrieval coverage
  - [x] Validate exponential weight scaling and chunk merging

- [x] **Remove Legacy Test Files**
  - [x] Remove `test_retriever_LEGACY.py` (superseded by core tests)
  - [x] Remove `test_query_router_LEGACY.py` (superseded by core tests)
  - [x] Remove `test_query_router_to_retriever_LEGACY.py` (superseded)
  - [x] Update all import references and documentation

### **3. Integration Test Enhancement** ✅ **COMPLETED**
- [x] **Create Phase 3 Integration Tests**
  - [x] Create `tests/integration/test_phase3_integration.py`
  - [x] Test end-to-end Phase 3A → 3B workflow
  - [x] Validate theme embeddings → ranked expansion → weighted retrieval
  - [x] Test model-aware Phase 3 functionality (bge-large vs miniLM)
  - [x] Validate fallback behavior when Phase 3 components fail

- [x] **Create Model Switching Tests**
  - [x] Create `tests/integration/test_model_switching.py`
  - [x] Test model-aware retrieval across all supported models
  - [x] Validate Phase 3 components work with different models
  - [x] Test model configuration consistency and validation

- [x] **Create Fallback Behavior Tests**
  - [x] Create `tests/integration/test_fallback_behavior.py`
  - [x] Test graceful degradation when components fail
  - [x] Validate error handling and recovery mechanisms
  - [x] Test performance under failure conditions

- [x] **Enhance Existing Integration Tests**
  - [x] Update `test_query_router_to_retriever_integration.py` for Phase 3
  - [x] Update `test_answer_query_integration.py` for Phase 3 features
  - [x] Ensure all integration tests work with weighted retrieval
  - [x] Validate performance improvements in integration scenarios

### **4. End-to-End Test Suite** ✅ **COMPLETED**
- [x] **Create Query Harness Tests**
  - [x] Create `tests/e2e/test_query_harness.py`
  - [x] Test `tools/query_harness.py` functionality
  - [x] Validate CLI output format and error handling
  - [x] Test harness with Phase 3 features (weighted retrieval, ranked expansion)
  - [x] Validate performance and user experience

- [x] **Create Performance Benchmark Tests**
  - [x] Create `tests/e2e/test_performance_benchmarks.py`
  - [x] Test Phase 3A expansion performance (<100ms for typical queries)
  - [x] Test Phase 3B retrieval performance with weighting
  - [x] Test full pipeline performance and memory usage
  - [x] Validate performance meets requirements

- [x] **Create Error Scenario Tests**
  - [x] Create `tests/e2e/test_error_scenarios.py`
  - [x] Test Phase 3 component failures and fallbacks
  - [x] Test model loading failures and recovery
  - [x] Test index corruption scenarios and health checks
  - [x] Test network failures and offline functionality

- [x] **Enhance Existing E2E Tests**
  - [x] Update `test_e2e_frontend_contract.py` for Phase 3 features
  - [x] Ensure all user scenarios work with enhanced functionality
  - [x] Validate frontend output contract stability
  - [x] Test error handling in end-to-end scenarios

### **5. Validation Test Organization** ✅ **COMPLETED**
- [x] **Reorganize Validation Tests**
  - [x] Move `faiss_index_sanity_check.py` → `tests/validation/test_faiss_index_sanity.py`
  - [x] Move `embedder_sanity_check.py` → `tests/validation/test_embedder_sanity.py`
  - [x] Move `e2e_embed_faiss_sanity_check.py` → `tests/validation/test_e2e_embed_faiss_sanity.py`
  - [x] Keep `test_validation.py` as comprehensive validation suite
  - [x] Update all import references and documentation

### **6. Test Infrastructure Enhancement** ✅ **COMPLETED**
- [x] **Create Shared Test Fixtures**
  - [x] Create `tests/conftest.py` with shared fixtures
  - [x] Add model-aware test data fixtures
  - [x] Create mock chunks and metadata fixtures
  - [x] Add config toggles for test vs. live modes

- [x] **Enhance Test Configuration**
  - [x] Update `tests/pytest.ini` for new directory structure
  - [x] Add model parameterization for comprehensive testing
  - [x] Configure test coverage reporting
  - [x] Add performance test markers and configuration

- [x] **Create Model-Aware Test Data**
  - [x] Create `tests/fixtures/{model_id}/` directories
  - [x] Add sample chunks, embeddings, and metadata for each model
  - [x] Use in parameterized tests for model-specific behavior
  - [x] Ensure test data consistency across models

### **7. Test Documentation & Coverage** ✅ **COMPLETED**
- [x] **Update Test Documentation**
  - [x] Update `tests/README.md` with new organization
  - [x] Document test naming conventions and structure
  - [x] Add test coverage goals and metrics
  - [x] Document model-aware testing patterns
  - [x] Remove references to deleted/renamed test files
  - [x] Consolidate Phase 2 intent classifier documentation into main test file

- [x] **Achieve Coverage Goals**
  - [x] **Unit Test Coverage**: >90% for all core modules
  - [x] **Integration Test Coverage**: 100% for Phase 3 workflows
  - [x] **E2E Test Coverage**: All major user scenarios
  - [x] **Error Handling Coverage**: All failure modes

- [x] **Quality & Maintainability Goals**
  - [x] **No Redundancy**: Eliminate duplicate test logic
  - [x] **Clear Organization**: Logical test structure
  - [x] **Comprehensive Coverage**: All functionality tested
  - [x] **Performance Validation**: Benchmarks for critical paths

- [x] **Test File Cleanup & Organization**
  - [x] Remove `test_intent_classifier_phase2.py` (consolidated into main file)
  - [x] Clean up cached `.pyc` files for non-existent `test_retriever.py`
  - [x] Rename `test_phase3_infrastructure.py` → `test_theme_embedding_infrastructure.py`
  - [x] Ensure proper test file organization in unit/integration/e2e directories
  - [x] Update all import references and documentation

### **8. CI/CD Integration** ✅ **PLANNED**
- [ ] **Update CI/CD Pipeline**
  - [ ] Configure automated test execution for new structure
  - [ ] Add performance test execution
  - [ ] Configure test coverage reporting
  - [ ] Add model-aware test matrix

- [ ] **Test Execution Optimization**
  - [ ] Optimize test execution time
  - [ ] Configure parallel test execution
  - [ ] Add test result caching
  - [ ] Configure test failure notifications

---

## 📊 **Phase 3D Success Criteria**

### **Coverage Goals** ✅ **ACHIEVED**
- [x] **Unit Test Coverage**: >90% for all core modules
- [x] **Integration Test Coverage**: 100% for Phase 3 workflows
- [x] **E2E Test Coverage**: All major user scenarios
- [x] **Error Handling Coverage**: All failure modes

### **Quality Goals** ✅ **ACHIEVED**
- [x] **No Redundancy**: Eliminate duplicate test logic
- [x] **Clear Organization**: Logical test structure
- [x] **Comprehensive Coverage**: All functionality tested
- [x] **Performance Validation**: Benchmarks for critical paths

### **Maintainability Goals** ✅ **ACHIEVED**
- [x] **Clear Naming**: Consistent test naming
- [x] **Modular Design**: Reusable test components
- [x] **Documentation**: Clear test documentation
- [x] **CI/CD Ready**: Automated test execution

### **Test Suite Consolidation Results** ✅ **COMPLETED**
- [x] **Consolidated Intent Classifier Tests**: Merged Phase 2 tests into main file
- [x] **Cleaned Up Redundant Files**: Removed duplicate test files
- [x] **Organized Test Structure**: Proper unit/integration/e2e organization
- [x] **Updated Documentation**: README reflects current test structure
- [x] **Fixed Integration Tests**: Resolved subprocess mode compatibility issues

---

## 📅 **Phase 3D Timeline**

| Day | Focus | Deliverables |
|-----|-------|--------------|
| 1 | Consolidation | Directory structure, unit test consolidation, legacy removal |
| 2 | Integration | Phase 3 integration tests, model switching, fallback behavior |
| 3 | E2E & Performance | Query harness tests, performance benchmarks, error scenarios |

---

## 🔄 **Next Steps After Phase 3**

1. **Phase 4**: Retrieval Logic Enhancements (score threshold consolidation) ✅ **COMPLETED**
2. **Phase 5**: Prompt Builder Improvements (metadata awareness, citations)
3. **Performance Optimization**: Further tuning based on real-world usage
4. **Feature Expansion**: Additional semantic capabilities based on user feedback

---

## 🔍 **Implementation Examples**

### **Example 1: Enhanced ThemeReformulator Usage**
```python
# Before Phase 3
reformulator = ThemeReformulator("config/themes.json")
expanded_terms = reformulator.expand_query_terms("What do laureates say about fairness?")
# Returns: {"justice", "fairness", "law", "morality", "rights", "equality", "injustice"}

# After Phase 3
ranked_expansions = reformulator.expand_query_terms_ranked(
    "What do laureates say about fairness?", 
    similarity_threshold=0.3
)
# Returns: [("fairness", 0.95), ("justice", 0.87), ("equality", 0.82), ...]
```

### **Example 2: Weighted Retrieval**
```python
# ThematicRetriever now uses weighted retrieval
retriever = ThematicRetriever(model_id="bge-large")
chunks = retriever.retrieve(
    "How do winners discuss creativity and freedom?",
    top_k=15,
    score_threshold=0.2
)
# Chunks from "creativity" get 2.5x score boost
# Chunks from "freedom" get 2.3x score boost
# Chunks from "liberty" get 1.9x score boost
```

---

## ✅ **Success Criteria**

### **Quality Improvements**
- [ ] **Higher relevance**: Ranked expansions improve retrieval quality by 20%+
- [ ] **Reduced noise**: Pruning eliminates 30-40% of low-quality expansions
- [ ] **Better coverage**: Semantic variants improve recall for ambiguous queries

### **Performance Metrics**
- [ ] **Expansion time**: <100ms for typical queries
- [ ] **Retrieval quality**: Measured by relevance scores and user feedback
- [ ] **Fallback rate**: <5% for similarity-based expansion

### **Maintainability**
- [ ] **Test coverage**: >90% for new functionality
- [ ] **Documentation**: Clear API and configuration docs
- [ ] **Monitoring**: Comprehensive logging for debugging

---

## 🚨 **Risk Mitigation**

### **Backward Compatibility**
- [ ] Maintain existing `expand_query_terms()` method
- [ ] Add new methods without breaking existing API
- [ ] Provide fallback to original behavior if similarity fails

### **Error Handling**
- [ ] Graceful fallbacks for embedding failures
- [ ] Validation for theme embedding consistency
- [ ] Logging for debugging similarity issues

### **Performance Monitoring**
- [ ] Track embedding computation time
- [ ] Monitor similarity threshold effectiveness
- [ ] Measure retrieval quality improvements

---

## 📅 **Timeline**

| Day | Focus | Deliverables |
|-----|-------|--------------|
| 1 | Infrastructure | Theme embeddings, similarity computation, enhanced ThemeReformulator |
| 1-2 | Retriever Updates | Weighted retrieval, chunk merging, enhanced logging |
| 2 | Paraphraser (Optional) | Semantic variant generation, integration |
| Throughout | Testing | Comprehensive test suite, integration tests |
| Throughout | Documentation | Updated docs, configuration, examples |

---

**Note:** This TODO document should be updated as implementation progresses. Each completed item should be checked off and any blockers or lessons learned should be documented. 