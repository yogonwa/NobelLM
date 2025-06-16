# Phase 5: Prompt Builder Improvements - Implementation TODO

**Date:** 2025-01-XX  
**Goal:** Transform the prompt building system from static templates to intelligent, metadata-aware prompt construction with citation scaffolding, explainable formatting, and intent-specific templates.

---

## 🎯 **Phase 5A: Core Infrastructure (Day 1)** 

### **1. Prompt Builder Infrastructure** 
- [ ] **Create `rag/prompt_builder.py`**
  - [ ] Implement `PromptBuilder` class with configurable templates
  - [ ] Add `build_generative_prompt(task_description: str, chunks: List[Dict], intent: str) -> str`
  - [ ] Add `build_qa_prompt(query: str, chunks: List[Dict], intent: str) -> str`
  - [ ] Add `build_thematic_prompt(query: str, chunks: List[Dict], theme: str) -> str`
  - [ ] Implement template loading from `config/prompt_templates.json`
  - [ ] Add template validation and fallback mechanisms

- [ ] **Create `config/prompt_templates.json`**
  - [ ] Define intent-specific templates (generative, qa, thematic, scoped)
  - [ ] Add metadata-aware chunk formatting templates
  - [ ] Include citation scaffolding patterns
  - [ ] Add tone and style guidance templates
  - [ ] Implement template versioning and inheritance

### **2. Chunk Metadata Formatting** 
- [ ] **Enhance chunk metadata in `embeddings/chunk_text.py`**
  - [ ] Add `speech_type` field (lecture, ceremony, interview, etc.)
  - [ ] Add `laureate_info` field (name, year, category, country)
  - [ ] Add `tone_markers` field (gratitude, responsibility, inspiration, etc.)
  - [ ] Add `context_metadata` field (audience, occasion, theme)
  - [ ] Implement metadata extraction during chunking process

- [ ] **Create chunk formatting utilities**
  - [ ] Implement `format_chunk_with_metadata(chunk: Dict) -> str`
  - [ ] Add emoji-based visual markers: `[🎓 Lecture — Toni Morrison, 1993]`
  - [ ] Add tone indicators: `[🏅 Ceremony — Gabriel García Márquez, 1982]`
  - [ ] Implement citation format: `[📚 Literature — 1982 — Colombia]`
  - [ ] Add fallback formatting for missing metadata

### **3. Intent-Specific Prompt Templates** 
- [ ] **Create generative prompt templates**
  - [ ] Identity statement templates: "You are a Nobel laureate..."
  - [ ] Task-specific templates: "Draft a job acceptance email..."
  - [ ] Style guidance templates: "Write in the tone of..."
  - [ ] Output format templates: "Structure your response as..."
  - [ ] Add clear section markers: `--- EXCERPTS START ---`

- [ ] **Create QA prompt templates**
  - [ ] Question-focused templates with context priming
  - [ ] Citation-aware templates with source attribution
  - [ ] Multi-perspective templates for complex queries
  - [ ] Confidence-indicating templates with uncertainty handling

---

## 🚀 **Phase 5B: Smart Chunk Sampling & Selection (Day 1-2)** 

### **4. Enhanced Chunk Selection Logic** 
- [ ] **Update `rag/query_engine.py`**
  - [ ] Modify `retrieve_chunks()` to support intent-aware sampling
  - [ ] Add `_select_chunks_by_intent(chunks: List[Dict], intent: str) -> List[Dict]`
  - [ ] Implement `_balance_chunk_types(chunks: List[Dict]) -> List[Dict]`
  - [ ] Add `_prioritize_tone_chunks(chunks: List[Dict], target_tone: str) -> List[Dict]`

- [ ] **Implement smart sampling strategies**
  - [ ] **Generative queries**: top_k=10-12, mix of lecture/ceremony, tone bias
  - [ ] **QA queries**: top_k=5-8, highest relevance, citation focus
  - [ ] **Thematic queries**: top_k=8-10, theme-balanced, diversity focus
  - [ ] **Scoped queries**: top_k=6-8, laureate-specific, context-rich

### **5. Tone and Style Biasing** 
- [ ] **Create tone classification system**
  - [ ] Implement `classify_chunk_tone(chunk: Dict) -> str`
  - [ ] Add tone keywords: gratitude, responsibility, inspiration, reflection
  - [ ] Create tone scoring: `score_chunk_tone(chunk: Dict, target_tone: str) -> float`
  - [ ] Implement tone-based chunk re-ranking

- [ ] **Add style-aware chunk selection**
  - [ ] Implement `select_chunks_by_style(chunks: List[Dict], style: str) -> List[Dict]`
  - [ ] Add style categories: formal, inspirational, personal, academic
  - [ ] Create style matching algorithms
  - [ ] Add style diversity balancing

### **6. Wildcard and Diversity Sampling** 
- [ ] **Implement wildcard chunk selection**
  - [ ] Add `_include_wildcard_chunks(chunks: List[Dict], count: int = 2) -> List[Dict]`
  - [ ] Select random high-quality chunks for inspiration
  - [ ] Ensure wildcards don't dominate primary results
  - [ ] Add wildcard quality validation

- [ ] **Add diversity balancing**
  - [ ] Implement `_balance_laureate_diversity(chunks: List[Dict]) -> List[Dict]`
  - [ ] Ensure representation across decades, countries, categories
  - [ ] Add gender and regional diversity considerations
  - [ ] Implement diversity scoring and optimization

---

## 🔧 **Phase 5C: Citation Scaffolding & Attribution (Day 2)** 

### **7. Citation System Implementation** 
- [ ] **Create citation formatting utilities**
  - [ ] Implement `format_citation(chunk: Dict) -> str`
  - [ ] Add inline citation format: `(Morrison, 1993)`
  - [ ] Add footnote citation format: `[1] Toni Morrison, Nobel Lecture 1993`
  - [ ] Add full citation format: `Toni Morrison, Nobel Prize in Literature, 1993`
  - [ ] Implement citation style selection based on intent

- [ ] **Add citation scaffolding to prompts**
  - [ ] Include citation instructions in prompt templates
  - [ ] Add citation format examples
  - [ ] Implement citation placement guidance
  - [ ] Add citation quality validation

### **8. Source Attribution Enhancement** 
- [ ] **Enhance chunk metadata with source info**
  - [ ] Add `source_url` field for traceability
  - [ ] Add `source_type` field (lecture, ceremony, interview)
  - [ ] Add `source_date` field for temporal context
  - [ ] Add `source_location` field for geographical context
  - [ ] Implement source validation and fallbacks

- [ ] **Create attribution tracking**
  - [ ] Implement `track_chunk_attribution(chunks: List[Dict]) -> Dict`
  - [ ] Add attribution metadata to prompt output
  - [ ] Create attribution reporting for debugging
  - [ ] Add attribution quality metrics

---

## 🧪 **Phase 5D: Comprehensive Test Suite & Coverage (Day 1-3)** 

### **9. Test Suite Analysis & Organization** 
- [ ] **Analyze current prompt-related tests**
  - [ ] Identify existing prompt building tests
  - [ ] Map Phase 5 test coverage gaps
  - [ ] Document prompt template testing needs
  - [ ] Create comprehensive test plan

- [ ] **Create Phase 5 test structure**
  - [ ] `tests/unit/test_prompt_builder.py` - Core prompt building logic
  - [ ] `tests/unit/test_chunk_formatting.py` - Metadata formatting
  - [ ] `tests/unit/test_chunk_sampling.py` - Smart selection logic
  - [ ] `tests/unit/test_citation_system.py` - Citation formatting
  - [ ] `tests/integration/test_prompt_integration.py` - End-to-end workflows

### **10. Unit Test Implementation** 
- [ ] **Prompt Builder Unit Tests**
  - [ ] Test all prompt template types (generative, qa, thematic, scoped)
  - [ ] Test template loading and validation
  - [ ] Test fallback mechanisms and error handling
  - [ ] Test intent-specific prompt generation
  - [ ] Test metadata-aware formatting

- [ ] **Chunk Formatting Unit Tests**
  - [ ] Test metadata extraction and formatting
  - [ ] Test emoji-based visual markers
  - [ ] Test citation format generation
  - [ ] Test fallback formatting for missing metadata
  - [ ] Test tone and style classification

- [ ] **Chunk Sampling Unit Tests**
  - [ ] Test intent-aware chunk selection
  - [ ] Test tone-based chunk prioritization
  - [ ] Test diversity balancing algorithms
  - [ ] Test wildcard chunk inclusion
  - [ ] Test sampling strategy validation

- [ ] **Citation System Unit Tests**
  - [ ] Test citation format generation
  - [ ] Test attribution tracking
  - [ ] Test citation quality validation
  - [ ] Test source metadata handling
  - [ ] Test citation style selection

### **11. Integration Test Enhancement** 
- [ ] **Create Phase 5 Integration Tests**
  - [ ] Test end-to-end prompt building workflows
  - [ ] Test chunk selection → formatting → prompt generation
  - [ ] Test intent classification → prompt template selection
  - [ ] Test citation scaffolding → attribution tracking
  - [ ] Test fallback behavior when components fail

- [ ] **Create Prompt Quality Tests**
  - [ ] Test prompt clarity and effectiveness
  - [ ] Test citation accuracy and completeness
  - [ ] Test chunk relevance and diversity
  - [ ] Test tone and style consistency
  - [ ] Test output format compliance

### **12. End-to-End Test Suite** 
- [ ] **Create User Scenario Tests**
  - [ ] Test generative email writing scenarios
  - [ ] Test QA question answering scenarios
  - [ ] Test thematic exploration scenarios
  - [ ] Test scoped laureate queries
  - [ ] Test error handling and recovery

- [ ] **Create Performance Tests**
  - [ ] Test prompt generation speed (<50ms for typical queries)
  - [ ] Test chunk selection performance
  - [ ] Test citation formatting performance
  - [ ] Test memory usage and optimization
  - [ ] Test scalability with large chunk sets

---

## 📊 **Phase 5E: Prompt Templates & Examples (Day 2-3)** 

### **13. Template Library Creation** 
- [ ] **Create comprehensive template library**
  - [ ] **Generative Templates**
    - [ ] Job acceptance email: "Draft a job acceptance email in the style of a Nobel Prize winner"
    - [ ] Inspirational speech: "Write an inspirational speech about creativity"
    - [ ] Personal reflection: "Write a personal reflection on success and failure"
    - [ ] Academic response: "Respond to a research question in Nobel laureate style"
    - [ ] Creative writing: "Write a short story about scientific discovery"

  - [ ] **QA Templates**
    - [ ] Factual questions: "What did [laureate] say about [topic]?"
    - [ ] Comparative questions: "How do different laureates approach [theme]?"
    - [ ] Analytical questions: "Analyze the evolution of [concept] in Nobel speeches"
    - [ ] Synthesis questions: "Synthesize perspectives on [topic] across laureates"

  - [ ] **Thematic Templates**
    - [ ] Theme exploration: "Explore how laureates discuss [theme]"
    - [ ] Cross-cultural analysis: "Compare perspectives on [theme] across cultures"
    - [ ] Temporal analysis: "How has [theme] evolved over time in Nobel speeches?"
    - [ ] Category comparison: "Compare [theme] across Nobel categories"

### **14. Template Configuration System** 
- [ ] **Implement template configuration**
  - [ ] Add template metadata (tags, categories, difficulty)
  - [ ] Add template parameters (chunk_count, tone_preference, citation_style)
  - [ ] Add template validation and testing
  - [ ] Add template versioning and updates
  - [ ] Add template performance tracking

- [ ] **Create template management utilities**
  - [ ] Implement template search and filtering
  - [ ] Add template recommendation system
  - [ ] Create template quality metrics
  - [ ] Add template usage analytics
  - [ ] Implement template optimization

### **15. Example Prompt Library** 
- [ ] **Create example prompts for each template**
  - [ ] **Generative Examples**
    ```json
    {
      "template": "job_acceptance_email",
      "example": "Draft a job acceptance email in the style of a Nobel Prize winner",
      "tags": ["generative", "email", "acceptance", "laureate-style"],
      "expected_tone": "humble, grateful, responsible",
      "chunk_preference": "ceremony speeches, gratitude themes"
    }
    ```

  - [ ] **QA Examples**
    ```json
    {
      "template": "factual_question",
      "example": "What did Toni Morrison say about the power of language?",
      "tags": ["qa", "factual", "scoped", "literature"],
      "citation_style": "inline",
      "chunk_preference": "lecture content, specific quotes"
    }
    ```

  - [ ] **Thematic Examples**
    ```json
    {
      "template": "theme_exploration",
      "example": "How do Nobel laureates discuss the role of creativity in their work?",
      "tags": ["thematic", "exploration", "creativity", "cross-category"],
      "chunk_preference": "diverse perspectives, balanced sampling"
    }
    ```

---

## 🔄 **Phase 5F: Integration & Query Router Updates (Day 3)** 

### **16. Query Router Enhancement** 
- [ ] **Update `rag/query_router.py`**
  - [ ] Add generative intent detection
  - [ ] Add prompt template selection logic
  - [ ] Add chunk sampling strategy selection
  - [ ] Add citation style selection
  - [ ] Add fallback mechanisms for new intents

- [ ] **Implement intent-specific routing**
  - [ ] Route generative queries to `build_generative_prompt()`
  - [ ] Route QA queries to `build_qa_prompt()`
  - [ ] Route thematic queries to `build_thematic_prompt()`
  - [ ] Route scoped queries to `build_scoped_prompt()`
  - [ ] Add confidence scoring for intent classification

### **17. Query Engine Integration** 
- [ ] **Update `rag/query_engine.py`**
  - [ ] Integrate `PromptBuilder` into `answer_query()`
  - [ ] Add prompt template selection based on intent
  - [ ] Add chunk sampling strategy selection
  - [ ] Add citation scaffolding integration
  - [ ] Add attribution tracking and reporting

- [ ] **Enhance answer generation**
  - [ ] Add prompt quality validation
  - [ ] Add citation accuracy checking
  - [ ] Add chunk relevance validation
  - [ ] Add output format compliance
  - [ ] Add performance monitoring

---

## 📊 **Phase 5 Success Criteria**

### **Quality Improvements**
- [ ] **Enhanced prompt clarity**: 30% improvement in LLM response quality
- [ ] **Better citation accuracy**: 95%+ citation accuracy rate
- [ ] **Improved chunk relevance**: 25% improvement in chunk selection quality
- [ ] **Consistent tone/style**: 90%+ tone/style consistency across responses

### **Performance Metrics**
- [ ] **Prompt generation time**: <50ms for typical queries
- [ ] **Chunk selection time**: <100ms for smart sampling
- [ ] **Citation formatting time**: <20ms per citation
- [ ] **Memory usage**: <10% increase over current system

### **Maintainability**
- [ ] **Test coverage**: >90% for all new functionality
- [ ] **Template coverage**: 100% of use cases covered by templates
- [ ] **Documentation**: Comprehensive API and template documentation
- [ ] **Monitoring**: Full prompt quality and performance tracking

---

## 🚨 **Risk Mitigation**

### **Backward Compatibility**
- [ ] Maintain existing prompt building interfaces
- [ ] Add new methods without breaking existing API
- [ ] Provide fallback to original behavior if new system fails
- [ ] Ensure existing queries continue to work

### **Error Handling**
- [ ] Graceful fallbacks for template loading failures
- [ ] Validation for chunk metadata consistency
- [ ] Logging for debugging prompt generation issues
- [ ] Recovery mechanisms for citation system failures

### **Performance Monitoring**
- [ ] Track prompt generation time and quality
- [ ] Monitor chunk selection effectiveness
- [ ] Measure citation accuracy and completeness
- [ ] Monitor template usage and effectiveness

---

## 📅 **Timeline**

| Day | Focus | Deliverables |
|-----|-------|--------------|
| 1 | Infrastructure | Prompt builder, templates, chunk formatting, metadata enhancement |
| 1-2 | Smart Sampling | Chunk selection logic, tone biasing, diversity balancing |
| 2 | Citation System | Citation formatting, attribution tracking, source enhancement |
| 2-3 | Templates & Examples | Template library, example prompts, configuration system |
| 3 | Integration | Query router updates, query engine integration, testing |
| Throughout | Testing | Comprehensive test suite, integration tests, performance validation |

---

## 🔍 **Implementation Examples**

### **Example 1: Enhanced Prompt Generation**
```python
# Before Phase 5
prompt = f"Answer this question: {query}\n\nContext:\n{chunks_text}"

# After Phase 5
prompt_builder = PromptBuilder("config/prompt_templates.json")
prompt = prompt_builder.build_qa_prompt(
    query="What did Toni Morrison say about language?",
    chunks=formatted_chunks,
    intent="factual_question"
)
# Returns structured prompt with citations, tone guidance, and clear formatting
```

### **Example 2: Smart Chunk Selection**
```python
# ThematicRetriever now uses smart sampling
retriever = ThematicRetriever(model_id="bge-large")
chunks = retriever.retrieve(
    "How do winners discuss creativity and freedom?",
    top_k=12,
    intent="generative",
    target_tone="inspirational"
)
# Returns balanced mix of lecture/ceremony chunks with inspirational tone bias
# Includes 2 wildcard chunks for creative inspiration
```

### **Example 3: Citation Scaffolding**
```python
# Generated prompt includes citation guidance
prompt = """
You are a Nobel laureate responding to a question about creativity.

--- EXCERPTS START ---
[🎓 Lecture — Toni Morrison, 1993] Language can never pin down slavery, genocide, war...
[🏅 Ceremony — Gabriel García Márquez, 1982] The solitude of Latin America...
--- EXCERPTS END ---

Please cite specific laureates and years in your response using format: (Author, Year)
"""
```

---

## ✅ **Deliverables**

### **Core Files**
- `rag/prompt_builder.py` - Main prompt building system
- `config/prompt_templates.json` - Template library
- `config/prompt_examples.json` - Example prompts
- `embeddings/chunk_text.py` - Enhanced metadata extraction
- `rag/query_router.py` - Updated intent detection and routing
- `rag/query_engine.py` - Integrated prompt building

### **Test Files**
- `tests/unit/test_prompt_builder.py` - Core prompt building tests
- `tests/unit/test_chunk_formatting.py` - Metadata formatting tests
- `tests/unit/test_chunk_sampling.py` - Smart selection tests
- `tests/unit/test_citation_system.py` - Citation formatting tests
- `tests/integration/test_prompt_integration.py` - End-to-end tests

### **Documentation**
- `docs/prompt_builder_guide.md` - User guide for prompt templates
- `docs/citation_system_guide.md` - Citation formatting guide
- `docs/chunk_sampling_guide.md` - Smart selection guide
- Updated `rag/README.md` - Phase 5 features and usage

---

**Note:** This TODO document should be updated as implementation progresses. Each completed item should be checked off and any blockers or lessons learned should be documented. The goal is to create a comprehensive handoff document for an AI coding assistant to implement Phase 5 successfully. 