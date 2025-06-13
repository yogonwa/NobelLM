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

## 🔧 **Phase 3C: Optional Paraphraser (Day 2)**

### **4. Semantic Term Generation**
- [ ] **Create `config/theme_paraphraser.py`**
  - [ ] Implement `generate_semantic_variants(theme: str) -> List[str]`
  - [ ] Add paraphraser model integration (e.g., T5-small for paraphrasing)
  - [ ] Implement caching for paraphraser outputs
  - [ ] Add fallback mechanisms for paraphraser failures

- [ ] **Integrate with ThemeReformulator**
  - [ ] Add `use_paraphraser: bool = False` parameter to `expand_query_terms_ranked()`
  - [ ] Generate semantic variants for high-similarity themes
  - [ ] Include variants in similarity ranking
  - [ ] Add paraphraser performance logging

---

## 🧪 **Phase 3D: Comprehensive Testing (Throughout)**

### **5. New Test Files**
- [ ] **Create `tests/test_theme_similarity.py`**
  - [ ] `test_theme_embedding_generation()`
  - [ ] `test_cosine_similarity_ranking()`
  - [ ] `test_similarity_threshold_filtering()`
  - [ ] `test_empty_theme_embeddings()`
  - [ ] `test_invalid_theme_embeddings()`

- [ ] **Create `tests/test_theme_reformulator_phase3.py`**
  - [ ] `test_ranked_expansion_with_similarity()`
  - [ ] `test_low_similarity_pruning()`
  - [ ] `test_mixed_theme_expansion_ranking()`
  - [ ] `test_fallback_to_original_query()`
  - [ ] `test_similarity_score_logging()`
  - [ ] `test_hybrid_keyword_extraction()`
  - [ ] `test_stopword_removal()`

- [ ] **Create `tests/test_thematic_retriever_phase3.py`**
  - [ ] `test_weighted_term_retrieval()`
  - [ ] `test_similarity_based_term_selection()`
  - [ ] `test_quality_ranking_integration()`
  - [ ] `test_performance_with_ranked_terms()`
  - [ ] `test_weighted_chunk_merging()`

- [ ] **Create `tests/test_theme_expansion_integration.py`**
  - [ ] `test_end_to_end_ranked_expansion()`
  - [ ] `test_paraphraser_integration()`
  - [ ] `test_model_switching_with_themes()`
  - [ ] `test_performance_benchmarks()`

### **6. Update Existing Tests**
- [ ] **Update `tests/test_theme_reformulator.py`**
  - [ ] Ensure existing tests still pass with new implementation
  - [ ] Add backward compatibility tests
  - [ ] Test fallback behavior

- [ ] **Update `tests/test_query_router_to_retriever_integration.py`**
  - [ ] Test integration with enhanced ThematicRetriever
  - [ ] Verify weighted retrieval works correctly
  - [ ] Test performance improvements

---

## 📊 **Phase 3E: Configuration & Documentation**

### **7. Configuration Updates**
- [ ] **Update `config/themes.json`**
  - [ ] Add embedding metadata for each theme
  - [ ] Add similarity threshold configurations
  - [ ] Add paraphraser settings (optional)

- [ ] **Update `rag/model_config.py`**
  - [ ] Add theme embedding paths for each model
  - [ ] Add theme similarity configuration
  - [ ] Add paraphraser model configuration

### **8. Documentation Updates**
- [ ] **Update `rag/README.md`**
  - [ ] Document new ThemeReformulator methods
  - [ ] Explain weighted retrieval algorithm
  - [ ] Add performance benchmarks
  - [ ] Update usage examples

- [ ] **Update `rag/RAG_Audit.md`**
  - [ ] Mark Phase 3 as completed
  - [ ] Document performance improvements
  - [ ] Add lessons learned

- [ ] **Update `/README.md`**
  - [ ] Document new ThemeReformulator methods in project docs

- [ ] **Update `tests/README.md`**
  - [ ] Add all tests in similar style and format
  - [ ] Place tests in proper position in file, under correct category and orderd by sequence in pipeline


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

## 🔄 **Next Steps After Phase 3**

1. **Phase 4**: Retrieval Logic Enhancements (score threshold consolidation)
2. **Phase 5**: Prompt Builder Improvements (metadata awareness, citations)
3. **Performance Optimization**: Further tuning based on real-world usage
4. **Feature Expansion**: Additional semantic capabilities based on user feedback

---

**Note:** This TODO document should be updated as implementation progresses. Each completed item should be checked off and any blockers or lessons learned should be documented. 