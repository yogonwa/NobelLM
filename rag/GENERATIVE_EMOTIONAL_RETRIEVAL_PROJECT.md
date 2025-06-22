# Generative Emotional Retrieval Project

**Date:** 2025-06-21 
**Goal:** Transform generative query retrieval from keyword-based to emotional/tonal-based  
**Audience:** Cursor AI coding assistant (future developer)  
**Status:** PLANNING

---

## 🎯 **Project Overview**

### **Problem Statement**
Current generative queries use keyword similarity search, which fails for creative tasks:

```
❌ CURRENT (Wrong):
User: "Write an acceptance email in the style of a Nobel laureate"
Query: "acceptance email Nobel laureate" 
Result: Chunks about "acceptance emails" (which don't exist in corpus)
Quality: Poor, generic responses

✅ TARGET (Correct):
User: "Write an acceptance email in the style of a Nobel laureate"
Query: "gratitude humility responsibility honor"
Result: Chunks expressing gratitude, humility, responsibility from various laureates
Quality: Rich, authentic Nobel laureate voice
```

### **Core Insight**
For generative tasks, we need to search for **emotional/tonal content** that matches the desired style, not keywords that match the task description.

---

## 📊 **Current State Analysis**

### **Existing Components**
- ✅ **Intent Classification**: `rag/intent_classifier.py` - identifies generative queries
- ✅ **Query Router**: `rag/query_router.py` - routes to appropriate retriever
- ✅ **Thematic Retriever**: `rag/thematic_retriever.py` - handles thematic queries
- ✅ **Prompt Builder**: `rag/prompt_builder.py` - constructs prompts from chunks
- ✅ **Query Engine**: `rag/query_engine.py` - main orchestration point

### **Current Generative Query Flow**
```python
# Current flow in query_engine.py
if route_result.intent == "generative":
    retriever = get_mode_aware_retriever(model_id)  # Uses same retriever as factual
    chunks = retriever.retrieve(
        query_string,  # Direct keyword similarity search
        top_k=10,
        score_threshold=0.2
    )
```

### **Problems with Current Approach**
1. **Wrong Search Strategy**: Uses keyword similarity instead of emotional similarity
2. **Insufficient Sampling**: n=10 chunks, need n=15 for generative tasks
3. **No Emotional Awareness**: No consideration of tone, emotion, or style
4. **Poor Quality**: Results in generic, non-laureate-like responses

---

## 🎯 **Desired Future State**

### **Target Generative Query Flow**
```python
# Target flow
if route_result.intent == "generative":
    retriever = GenerativeEmotionalRetriever(model_id)
    emotional_query = extract_emotional_concepts(query_string, task_type)
    chunks = retriever.retrieve(
        emotional_query,
        top_k=15,  # Broader sampling
        emotional_filters=get_emotional_filters(task_type),
        diversity_constraints=True
    )
```

### **Success Criteria**
- ✅ **Emotional Relevance**: Chunks express target emotions (gratitude, humility, etc.)
- ✅ **Broad Sampling**: n=15 diverse chunks from multiple laureates
- ✅ **Quality Improvement**: Responses sound authentically like Nobel laureates
- ✅ **No Regression**: Factual/thematic queries still work perfectly
- ✅ **Performance**: Retrieval time <2s for emotional queries

---

## 🏗️ **Implementation Plan**

### **Phase 1: Emotional Mapping Foundation** (Day 1)
- [ ] **Create emotional mapping configuration**
  - [ ] `config/emotional_mappings.json` - define task→emotion mappings
  - [ ] `rag/emotional_mapper.py` - mapping logic and utilities
- [ ] **Define core emotional concepts**
  - [ ] Acceptance email: gratitude, humility, responsibility, honor
  - [ ] Inspirational speech: hope, inspiration, courage, determination
  - [ ] Reflection piece: contemplation, wisdom, insight, reflection

### **Phase 2: Generative Retriever Implementation** (Day 1-2)
- [ ] **Create `rag/generative_retriever.py`**
  - [ ] `GenerativeEmotionalRetriever` class
  - [ ] Emotional query construction
  - [ ] Broad sampling logic (n=15)
  - [ ] Emotional filtering and ranking
- [ ] **Integration with query engine**
  - [ ] Update `rag/query_engine.py` to use new retriever
  - [ ] Add emotional retrieval path

### **Phase 3: Enhanced Prompt Building** (Day 2)
- [ ] **Update `rag/prompt_builder.py`**
  - [ ] Emotional context awareness
  - [ ] Generative-specific templates
  - [ ] Emotional diversity indicators
- [ ] **Template improvements**
  - [ ] Better generative prompt templates
  - [ ] Emotional context framing

### **Phase 4: Testing & Validation** (Day 3)
- [ ] **Unit tests for new components**
- [ ] **Integration tests for full pipeline**
- [ ] **Performance testing**
- [ ] **Quality validation with real queries**

---

## 📁 **File Audit & Changes Required**

### **New Files to Create**
```
rag/
├── emotional_mapper.py          # NEW: Emotional mapping logic
├── generative_retriever.py      # NEW: Emotional retrieval implementation
└── config/
    └── emotional_mappings.json  # NEW: Task→emotion mappings
```

### **Files to Modify**

#### **1. `rag/query_engine.py`** (HIGH PRIORITY)
**Lines to modify:** ~480-520 (generative query handling)
```python
# CURRENT:
if route_result.intent == "generative":
    retriever = get_mode_aware_retriever(model_id)

# TARGET:
if route_result.intent == "generative":
    retriever = GenerativeEmotionalRetriever(model_id)
    emotional_query = extract_emotional_concepts(query_string, task_type)
```

**Functions to update:**
- `answer_query()` - Add emotional retrieval path
- `build_intent_aware_prompt()` - Handle emotional context

#### **2. `rag/query_router.py`** (MEDIUM PRIORITY)
**Lines to modify:** ~200-250 (retrieval config for generative)
```python
# CURRENT:
else:  # generative
    config = RetrievalConfig(top_k=10, score_threshold=0.2)

# TARGET:
else:  # generative
    config = RetrievalConfig(
        top_k=15, 
        score_threshold=0.2,
        emotional_retrieval=True,
        task_type=extract_task_type(query)
    )
```

**Functions to update:**
- `route_query()` - Add emotional retrieval configuration
- `extract_task_type()` - NEW: Identify specific generative task

#### **3. `rag/prompt_builder.py`** (MEDIUM PRIORITY)
**Lines to modify:** ~150-200 (generative prompt building)
```python
# ADD NEW METHOD:
def build_emotional_generative_prompt(
    self, 
    query: str, 
    chunks: List[Dict], 
    emotional_context: Dict[str, Any]
) -> str:
    """Build generative prompt with emotional context awareness."""
```

**Functions to update:**
- `build_generative_prompt()` - Add emotional context
- `_format_chunks_with_metadata()` - Add emotional indicators

#### **4. `rag/retrieval_logic.py`** (LOW PRIORITY)
**Lines to modify:** ~300-346 (broad sampling logic)
```python
# ADD NEW FUNCTION:
def apply_emotional_sampling(
    chunks: List[Dict[str, Any]],
    emotional_filters: Dict[str, Any],
    target_count: int = 15
) -> List[Dict[str, Any]]:
    """Apply emotional filtering and broad sampling."""
```

#### **5. `tools/query_harness.py`** (LOW PRIORITY)
**Lines to modify:** ~150-200 (verbose output for emotional retrieval)
```python
# ADD TO VERBOSE OUTPUT:
if args.verbose and intent == "generative":
    print_info(f"Emotional query: {emotional_query}")
    print_info(f"Emotional filters: {emotional_filters}")
```

### **Configuration Files to Update**

#### **1. `config/prompt_templates.json`** (MEDIUM PRIORITY)
**Add new templates:**
```json
{
  "generative_emotional": {
    "template": "You are a Nobel laureate expressing {emotions}. {query}\n\nContext:\n{context}",
    "intent": "generative",
    "tags": ["generative", "emotional", "laureate-style"],
    "chunk_count": 15,
    "citation_style": "inline"
  }
}
```

#### **2. `rag/README.md`** (LOW PRIORITY)
**Add section:** "Emotional Retrieval for Generative Queries"
- Explain the problem and solution
- Document new components
- Provide usage examples

---

## 🧪 **Testing Strategy**

### **Regression Tests** (CRITICAL)
**Files to run:** `tests/unit/test_query_engine.py`, `tests/integration/test_full_pipeline.py`

**Test cases to verify still work:**
- [ ] Factual queries: "What year did Toni Morrison win?"
- [ ] Thematic queries: "How do laureates view literature?"
- [ ] Metadata queries: "Who won in 2017?"
- [ ] Scoped queries: "What did Hemingway say about writing?"

### **New Unit Tests** (HIGH PRIORITY)
**File to create:** `tests/unit/test_generative_retriever.py`

**Test cases:**
```python
def test_emotional_mapping():
    """Test task→emotion mapping logic."""
    
def test_emotional_query_construction():
    """Test emotional query building."""
    
def test_broad_sampling():
    """Test n=15 retrieval with emotional filtering."""
    
def test_emotional_ranking():
    """Test emotional relevance ranking."""
```

### **New Integration Tests** (HIGH PRIORITY)
**File to create:** `tests/integration/test_generative_queries.py`

**Test cases:**
```python
def test_acceptance_email_generation():
    """Test full acceptance email generation pipeline."""
    
def test_inspirational_speech_generation():
    """Test inspirational speech generation."""
    
def test_emotional_diversity():
    """Test that emotional chunks come from diverse sources."""
```

### **Performance Tests** (MEDIUM PRIORITY)
**File to create:** `tests/performance/test_emotional_retrieval.py`

**Test cases:**
```python
def test_retrieval_speed():
    """Test that emotional retrieval completes in <2s."""
    
def test_memory_usage():
    """Test memory usage for n=15 retrieval."""
    
def test_concurrent_queries():
    """Test multiple emotional queries simultaneously."""
```

### **Quality Validation Tests** (MEDIUM PRIORITY)
**File to create:** `tests/validation/test_generative_quality.py`

**Test cases:**
```python
def test_emotional_relevance():
    """Test that retrieved chunks express target emotions."""
    
def test_laureate_authenticity():
    """Test that responses sound like Nobel laureates."""
    
def test_diversity_metrics():
    """Test temporal and author diversity."""
```

---

## 📝 **Documentation Updates**

### **Code Comments** (REQUIRED)
**Files requiring detailed comments:**
- `rag/emotional_mapper.py` - Document mapping logic and emotional concepts
- `rag/generative_retriever.py` - Document retrieval strategy and sampling
- `rag/query_engine.py` - Document emotional retrieval integration
- `config/emotional_mappings.json` - Document each mapping with examples

### **README Updates** (REQUIRED)
**Files to update:**
- `rag/README.md` - Add emotional retrieval section
- `config/README.md` - Document emotional mappings configuration
- `tests/README.md` - Document new test categories

### **API Documentation** (RECOMMENDED)
**Create:** `docs/emotional_retrieval_api.md`
- Document new classes and methods
- Provide usage examples
- Explain configuration options

---

## ✅ **Task Completion Checklist**

### **Phase 1: Foundation** 
- [ ] Create `config/emotional_mappings.json`
- [ ] Create `rag/emotional_mapper.py`
- [ ] Define core emotional concepts
- [ ] Write unit tests for emotional mapping

### **Phase 2: Retriever Implementation**
- [ ] Create `rag/generative_retriever.py`
- [ ] Implement `GenerativeEmotionalRetriever` class
- [ ] Add emotional query construction
- [ ] Implement broad sampling logic
- [ ] Update `rag/query_engine.py` integration
- [ ] Write unit tests for retriever

### **Phase 3: Prompt Enhancement**
- [ ] Update `rag/prompt_builder.py` for emotional context
- [ ] Add new generative templates to `config/prompt_templates.json`
- [ ] Update `rag/query_router.py` for emotional configuration
- [ ] Write integration tests

### **Phase 4: Testing & Validation**
- [ ] Run all regression tests
- [ ] Write performance tests
- [ ] Write quality validation tests
- [ ] Performance optimization if needed

### **Phase 5: Documentation**
- [ ] Update all README files
- [ ] Add comprehensive code comments
- [ ] Create API documentation
- [ ] Update `tools/query_harness.py` verbose output

### **Phase 6: Final Validation**
- [ ] End-to-end testing with real queries
- [ ] Quality assessment of generated responses
- [ ] Performance benchmarking
- [ ] Code review and cleanup

---

## 🚨 **Risk Mitigation**

### **Technical Risks**
- **Performance Impact**: Monitor retrieval times, implement caching if needed
- **Memory Usage**: Profile n=15 retrieval, optimize if necessary
- **Integration Complexity**: Implement incrementally with feature flags

### **Quality Risks**
- **Emotional Misclassification**: Use conservative thresholds, validate manually
- **Over-engineering**: Start simple, add complexity only if needed
- **Prompt Bloat**: Monitor token usage, implement truncation if needed

### **Regression Risks**
- **Existing Queries**: Comprehensive regression test suite
- **Performance**: Benchmark before/after for all query types
- **API Changes**: Maintain backward compatibility

---

## 🎯 **Success Metrics**

### **Quality Metrics**
- **Emotional Relevance**: 85%+ chunks express target emotions
- **Response Authenticity**: 90%+ responses sound like Nobel laureates
- **Diversity**: 5+ different laureates per response
- **Temporal Spread**: 3+ different decades represented

### **Performance Metrics**
- **Retrieval Speed**: <2s for emotional queries
- **Memory Usage**: <50MB increase for n=15 retrieval
- **No Regression**: 0% performance degradation for existing queries

### **User Experience Metrics**
- **Response Quality**: Significant improvement in generative response quality
- **Consistency**: Reliable emotional tone across similar queries
- **Authenticity**: Responses indistinguishable from real laureate writing

---

## 📞 **Implementation Notes**

### **For Future Developers**
1. **Start with Phase 1** - Foundation is critical
2. **Test incrementally** - Each phase should be fully tested before proceeding
3. **Monitor performance** - Emotional retrieval may be slower initially
4. **Validate quality** - Manual review of generated responses is essential
5. **Document thoroughly** - Future maintenance depends on good documentation

### **Code Style Requirements**
- **Type hints**: All new functions must have complete type annotations
- **Docstrings**: Comprehensive docstrings for all new classes and methods
- **Error handling**: Robust error handling with meaningful messages
- **Logging**: Appropriate logging for debugging and monitoring

### **Testing Requirements**
- **Unit tests**: 90%+ coverage for new code
- **Integration tests**: Full pipeline testing for all query types
- **Performance tests**: Benchmarking for all new functionality
- **Quality tests**: Manual validation of response quality

---

**Project Status:** READY FOR IMPLEMENTATION  
**Next Action:** Begin Phase 1 - Emotional Mapping Foundation  
**Estimated Duration:** 3-4 days  
**Priority:** HIGH - Core quality improvement for generative queries 