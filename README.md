---
title: NobelLM
emoji: 📚
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.32.0
app_file: app.py
pinned: false
---

[![Hugging Face Spaces](https://img.shields.io/badge/Live%20Demo-Hugging%20Face%20Spaces-blue?logo=huggingface)](https://huggingface.co/spaces/yogonwa/nobelLM)

# NobelLM

**Semantic search + Retrieval-Augmented Generation (RAG) for Nobel Prize speeches**  
Explore the words of Nobel laureates through embeddings, vector search, and a lightweight Streamlit UI.

---

## 🎯 Project Overview

NobelLM is a modular, full-stack GenAI project that:

- Scrapes and normalizes NobelPrize.org metadata and speeches (starting with the Literature category)
- Embeds speech content using sentence-transformers (MiniLM or BGE-Large, model-aware)
- Supports natural language Q&A via RAG using OpenAI's GPT-3.5
- Exposes a simple interactive UI powered by Streamlit
- **Is publicly deployed and accessible via Hugging Face Spaces: [Live Demo](https://huggingface.co/spaces/yogonwa/nobelLM)**
- Deploys publicly via Hugging Face Spaces

This project is designed for learning, modularity, and extensibility.

---

## 🚀 **Recent Major Features (June 2025)**

### **Intelligent Prompt Builder System** ✨ **NEW**
The NobelLM RAG pipeline now features a sophisticated, metadata-aware prompt construction system that significantly improves response quality and consistency.

**Key Features:**
- **Intent-Specific Templates**: 11 configurable templates for different query types (QA, generative, thematic, scoped)
- **Metadata-Aware Formatting**: Visual markers (🎓 for lectures, 🏅 for ceremonies) and automatic citation formatting
- **Citation Scaffolding**: Multiple citation styles (inline, footnote, full) with automatic attribution
- **Template Configuration**: JSON-based templates with metadata, versioning, and validation

**Example Usage:**
```python
from rag.query_engine import answer_query

# Generative email with metadata-aware formatting
response = answer_query("Draft a job acceptance email in the style of a Nobel laureate")
# Returns prompt with: [🎓 Lecture — Toni Morrison, 1993] citations and laureate-style guidance

# Thematic exploration with citation scaffolding  
response = answer_query("How do laureates discuss creativity and freedom?")
# Returns prompt with: [🏅 Ceremony — Gabriel García Márquez, 1982] citations and thematic analysis guidance
```

**Template Types:**
- **QA Templates**: Factual, analytical, comparative queries with citation focus
- **Generative Templates**: Email, speech, reflection tasks with laureate-style guidance
- **Thematic Templates**: Exploration, cross-cultural, temporal analysis with diverse perspectives
- **Scoped Templates**: Laureate-specific queries with focused context

### **Enhanced Thematic Retrieval with Weighted Scoring** ✨ **NEW**
The thematic retrieval system has been significantly enhanced with intelligent similarity-based expansion and exponential weight scaling.

**Key Features:**
- **Similarity-Based Expansion**: Pre-computed theme embeddings with configurable similarity thresholds
- **Weighted Retrieval**: Exponential weight scaling prioritizes most relevant expansion terms
- **Quality Filtering**: Automatic pruning of low-similarity expansions (30-40% noise reduction)
- **Source Attribution**: Each chunk includes source term and boost factor for debugging

**Performance Improvements:**
- **20-40% higher relevance** through similarity ranking
- **<100ms expansion time** for typical queries
- **Exponential weighting** prioritizes most relevant terms
- **Quality filtering** removes low-similarity expansions

### **Unified Retrieval Logic with Consistent Thresholds** ✨ **NEW**
All retrieval paths now use centralized logic with consistent score thresholds and guaranteed minimum results.

**Key Features:**
- **Query-Type Specific Thresholds**: Factual (0.25), Thematic (0.2), Generative (0.2)
- **Guaranteed Minimum Results**: Always returns at least 3-5 chunks when available
- **Transparent Filtering**: Each chunk includes filtering reason and boost factors
- **Consistent Performance**: 100% consistent results for identical queries

**Before vs After:**
- **Before**: Inconsistent results, mixed quality, confusing user experience
- **After**: Predictable quality, transparent decisions, reliable performance

### **Enhanced Intent Classification** ✨ **NEW**
The intent classifier now provides structured results with confidence scoring and multiple laureate support.

**Key Features:**
- **Structured Results**: `IntentResult` objects with intent, confidence, matched terms, scoped entities
- **Hybrid Confidence Scoring**: Pattern strength × (1 - ambiguity penalty)
- **Multiple Laureate Support**: Detects up to 3 laureates in single query with proper deduplication
- **Config-Driven Keywords**: JSON-based configuration for easy tuning and extension

**Example:**
```python
from rag.intent_classifier import IntentClassifier

classifier = IntentClassifier()
result = classifier.classify("Compare the themes of hope in Toni Morrison and Gabriel García Márquez")

print(f"Intent: {result.intent}")  # "thematic"
print(f"Confidence: {result.confidence}")  # 0.87
print(f"Scoped entities: {result.scoped_entities}")  # ["Toni Morrison", "Gabriel García Márquez"]
```

### **Model-Aware, Config-Driven Pipeline** ✨ **NEW**
All embedding, chunking, indexing, and RAG operations are now model-aware and config-driven.

**Key Features:**
- **Centralized Configuration**: All model paths, dimensions, and settings in `rag/model_config.py`
- **Model Consistency Checks**: Automatic validation of model/index dimension matching
- **Easy Model Switching**: Pass `model_id` to any function or use `--model` CLI flag
- **A/B Testing Ready**: Seamless switching between BGE-Large and MiniLM

**Example:**
```python
# Switch models easily
response = answer_query("What do laureates say about justice?", model_id="miniLM")

# All downstream operations automatically use correct model
# - Embedding model
# - FAISS index  
# - Chunk metadata
# - Theme embeddings
```

---

## 🎯 **Core Features**

- 🗂 Structured metadata and full-text speech extraction
- 🔎 Local embedding + FAISS vector search
- 🤖 RAG-powered question answering with GPT-3.5
- ⚡️ Fast, robust factual Q&A from a flat laureate metadata structure (see below)
- 🖥 Streamlit interface for live semantic search
- 🚀 Public deployment via Hugging Face Spaces
- 📦 **Model-aware, token-based chunking with optional overlap for context continuity**
- 🧩 **Embeddings generated for each chunk using BGE-Large or MiniLM; outputs are model-specific**
- 🛠️ **Centralized model config for easy model switching and reproducibility**

## Pre-retrieval Metadata Filtering

NobelLM now supports **pre-retrieval metadata filtering** at the retrieval layer. This means that any filter (e.g., by gender, country, source_type) is applied to the chunk metadata before vector search (FAISS), ensuring only relevant chunks are searched. This improves efficiency, explainability, and privacy.

- Filters can be passed as a dictionary (e.g., {"gender": "female", "country": "USA"}) to any query.
- Filtering is supported in both in-process and subprocess retrieval modes.
- Any metadata field present in the chunk index can be used for filtering.
- The output schema is privacy-preserving: only public fields (e.g., chunk_id, text_snippet) are returned in answers.

See `tests/README.md` and `tests/test_coverage_plan.md` for integration test coverage.

---

## 🗺️ Architecture Overview

View the interactive RAG pipeline architecture diagram here:  
[NobelLM RAG Pipeline – Mermaid Chart](https://www.mermaidchart.com/app/projects/f11ebb0b-c097-43bd-80d5-e9740319bf5e/diagrams/4ac34c1b-cea0-40b8-a1d3-10014bbcf904/version/v0.1/edit)

---

## ⚙️ Tech Stack

- **Language**: Python 3.11+
- **Scraping**: `requests`, `beautifulsoup4`
- **Text Parsing**: `PyMuPDF`, custom HTML/text cleaning
- **Embeddings**: `sentence-transformers` (MiniLM or BGE-Large, model-aware chunking), upgradeable to OpenAI `text-embedding-3-small`
- **Vector Store**: `FAISS` (cosine similarity, local CPU)
- **Frontend**: `Streamlit` (hosted on Hugging Face Spaces)
- **Testing**: `pytest`
- **Deployment**: GitHub + Hugging Face Spaces

---

## 📁 Folder Structure

```text
NobelLM/
├── data/                 # Raw and processed data (JSON, CSV, text, embeddings)
├── scraper/              # NobelPrize.org scraping scripts
├── embeddings/           # Chunking and vector embedding logic
├── rag/                  # Retrieval-augmented generation pipeline
├── frontend/             # Streamlit UI app
├── utils/                # Shared helpers (e.g., cleaning)
├── tests/                # Pytest test modules
├── .env.example          # Environment variable template
├── requirements.txt      # Project dependencies
├── IMPLEMENTATION_PLAN.md
├── SPEC.md
├── TASKS.md
├── NOTES.md
├── .cursorrules          # Cursor AI execution rules
```

---

## 🚀 Getting Started

1. **Clone the repo**  
   ```bash
   git clone https://github.com/yourusername/NobelLM.git
   cd NobelLM
   ```
2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or 'venv\Scripts\activate' on Windows
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Set up critical data files**
   ```bash
   python scripts/setup_data.py
   ```
5. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Add your OpenAI API key to the .env file
   ```
6. **Run an example module**
   ```bash
   python -m scraper.scrape_literature
   ```

---

## 📊 Data Management Strategy

NobelLM uses a multi-layered approach to ensure critical data files are always available:

### **Critical Files**
- `data/nobel_literature.json` - Core laureate metadata (tracked via Git LFS)
- `data/intent_keywords.json` - Intent classification configuration
- `data/nobel_literature_facts_urls.json` - Factual query patterns

### **Large Generated Files (Not Tracked)**
- `data/literature_embeddings*.json` - Embedding vectors (generated)
- `data/faiss_index/*.faiss` - FAISS index files (generated)
- `data/chunks_*.jsonl` - Chunk metadata (generated)

### **Fallback Mechanisms**
1. **Git LFS**: Critical files are tracked via Git LFS for version control
2. **Backup Restoration**: Missing files are restored from timestamped backups
3. **Minimal Generation**: If no backup exists, minimal test data is generated
4. **Runtime Fallbacks**: Code includes fallback data for testing scenarios

### **Setup Process**
The `scripts/setup_data.py` script ensures all critical files exist:
```bash
python scripts/setup_data.py
```

This approach balances version control needs with repository size constraints while ensuring the pipeline never breaks due to missing data.

---

## 🛠️ Model-Aware Configuration

All chunking, embedding, indexing, and RAG operations are now **model-aware and config-driven**. The embedding model, FAISS index, and chunk metadata paths are centrally managed in [`rag/model_config.py`](./rag/model_config.py):

- To switch models (e.g., BGE-Large vs MiniLM), pass `--model` to any CLI tool, or set `model_id` in your code or UI.
- All file paths, model names, and embedding dimensions are set in one place.
- Consistency checks ensure the loaded model and index match in dimension, preventing silent errors.
- Enables easy A/B testing and reproducibility.

**Example:**
```python
from rag.query_engine import answer_query
from rag.model_config import DEFAULT_MODEL_ID

# Query using the default model (BGE-Large)
response = answer_query("What do laureates say about justice?", dry_run=True)

# Query using MiniLM
response = answer_query("What do laureates say about justice?", dry_run=True, model_id="miniLM")
```

**To add a new model:**
- Add its config to `rag/model_config.py`.
- All downstream code and scripts will pick it up automatically.

## 🧩 Mode-Agnostic Retriever Layer (June 2025 Refactor)

**New as of June 2025:** NobelLM now uses a modern, mode-agnostic retriever abstraction for all chunk retrieval, both factual and thematic.

- All retrieval is routed through a `BaseRetriever` interface, with two main implementations:
  - `InProcessRetriever`: Runs embedding and FAISS search in-process (Linux/prod, default).
  - `SubprocessRetriever`: Runs FAISS search in a subprocess for Mac/Intel safety (set `NOBELLM_USE_FAISS_SUBPROCESS=1`).
- A factory function (`get_mode_aware_retriever`) selects the correct backend based on environment.
- The interface is always `retrieve(query: str, top_k: int, filters: dict) -> List[dict]`.
- Thematic and factual queries both use this interface—no more shape/type bugs or mode-specific logic in callers.
- **Extensible:** You can add new backends (e.g., ElasticSearch, hybrid, remote API) by subclassing `BaseRetriever` and updating the factory.

**Example usage:**
```python
from rag.retriever import get_mode_aware_retriever
retriever = get_mode_aware_retriever(model_id)
chunks = retriever.retrieve("What did laureates say about justice?", top_k=10)
```

This refactor makes the pipeline robust, testable, and future-ready for multi-backend or hybrid search.

## 🎯 Intent Classifier Modernization (Phase 2 - June 2025)

**New as of June 2025:** NobelLM now features a modern, config-driven intent classification system with hybrid confidence scoring and enhanced transparency.

### Key Features

**1. Structured Intent Classification**
- Returns `IntentResult` objects with intent, confidence, matched terms, scoped entities, and decision trace
- Configurable keyword/phrase weights via `data/intent_keywords.json`
- Hybrid confidence scoring: pattern strength × (1 - ambiguity penalty)
- Support for multiple laureate detection in single queries

**2. Enhanced Transparency**
- Clear decision traces showing which patterns matched and why
- Confidence scores (0.1-1.0) indicating classification certainty
- Detailed logging for debugging and optimization
- Backward compatibility with legacy string/dict returns

**3. Robust Text Processing**
- Integration with existing `ThemeReformulator` for lemmatization
- Graceful fallback when spaCy is unavailable
- Improved matching for word variations (e.g., "themes" → "theme")

**Example Usage:**
```python
from rag.intent_classifier import IntentClassifier

classifier = IntentClassifier()
result = classifier.classify("What did Toni Morrison say about justice?")

print(f"Intent: {result.intent}")  # "thematic"
print(f"Confidence: {result.confidence:.2f}")  # 0.85
print(f"Scoped Laureate: {result.scoped_laureate}")  # "Toni Morrison"
print(f"Decision Trace: {result.decision_trace}")  # Detailed reasoning
```

## 🎯 Enhanced Retrieval Logic (Phase 4 - January 2025)

**New as of January 2025:** NobelLM now features unified retrieval logic with consistent score thresholds, standardized fallback behavior, and transparent filtering across all query types and retrieval paths.

### Phase 4: Retrieval Logic Enhancements ✅ **COMPLETED**

**Key Features:**
- **Centralized retrieval logic** in `rag/retrieval_logic.py` with unified fallback behavior
- **Standardized score thresholds** by query type:
  - Factual: 0.25 (higher precision for specific facts)
  - Thematic: 0.2 (balanced precision/recall for themes)
  - Generative: 0.2 (broader scope for creative content)
- **Consistent result formatting** with `ScoredChunk` objects and filtering metadata
- **Comprehensive logging** with performance metrics and decision transparency
- **Guaranteed minimum results** with intelligent fallback logic

**Real-World Impact:**
- **100% consistent results** for identical queries across all retrieval paths
- **Predictable response times** and standardized chunk counts
- **Transparent filtering decisions** with detailed logging and debugging
- **Better user experience** with explainable, high-quality results

**Example Usage:**
```python
from rag.query_engine import answer_query

# Factual query: Always gets 3-5 high-quality results (score ≥ 0.25)
response = answer_query("When did Toni Morrison win the Nobel Prize?")

# Thematic query: Gets 3-15 results (score ≥ 0.2) for comprehensive analysis
response = answer_query("What do laureates say about justice and equality?")

# Generative query: Gets 10 results (score ≥ 0.2) for creative inspiration
response = answer_query("Write a speech in the style of a Nobel laureate")
```

**Before vs After:**
- **Before**: Inconsistent results, mixed quality, confusing user experience
- **After**: Predictable quality, transparent decisions, reliable performance

See [`rag/PHASE4_COMPLETED.md`](rag/PHASE4_COMPLETED.md) for comprehensive documentation and implementation details.

## 🎯 Enhanced Thematic Retrieval (Phase 3A & 3B - January 2025)

**New as of January 2025:** NobelLM now features intelligent similarity-based thematic query expansion and weighted retrieval for significantly improved search quality.

### Phase 3A: Theme Embedding Infrastructure
- **Pre-computed embeddings** for all theme keywords with model-aware storage
- **Enhanced ThemeReformulator** with `expand_query_terms_ranked()` method
- **Quality filtering** with configurable similarity thresholds
- **Performance optimization** with lazy loading and caching

### Phase 3B: Weighted Retrieval Enhancement
- **Intelligent weighted retrieval** using similarity-based ranked expansion
- **Exponential weight scaling** (`exp(2 * similarity_score)`) for chunk scores
- **Source term attribution** for debugging and analysis
- **Backward compatibility** with legacy retrieval methods
- **Performance monitoring** with detailed logging and statistics

**Example Usage:**
```python
from rag.thematic_retriever import ThematicRetriever

# Enhanced weighted retrieval (default)
retriever = ThematicRetriever(similarity_threshold=0.3)
chunks = retriever.retrieve("What do laureates say about creativity and freedom?")

# Chunks now have weighted scores and source attribution
for chunk in chunks:
    print(f"Score: {chunk['score']:.3f}")
    print(f"Source term: {chunk['source_term']}")
    print(f"Boost factor: {chunk['boost_factor']:.3f}")

# Legacy retrieval (backward compatibility)
chunks = retriever.retrieve("What do laureates say about justice?", use_weighted_retrieval=False)
```

**Performance Benefits:**
- **20-40% higher relevance** through similarity ranking
- **Quality filtering** removes low-similarity expansions
- **Exponential weighting** prioritizes most relevant terms
- **Source attribution** enables debugging and analysis

## 🧠 Theme Embedding Infrastructure (Phase 3A - January 2025)

**New as of January 2025:** NobelLM now features intelligent similarity-based thematic query expansion with pre-computed embeddings and quality filtering.

### Key Features

**1. Pre-computed Theme Embeddings**
- Model-aware embeddings for all theme keywords (bge-large: 1024d, miniLM: 384d)
- Compressed storage as `.npz` files for efficient loading (~100-200ms)
- Automatic health checks and validation
- Lazy loading with caching for optimal performance

**2. Enhanced ThemeReformulator**
- **New Method**: `expand_query_terms_ranked()` - Returns ranked expansions with similarity scores
- **Hybrid Keyword Extraction**: Smart embedding strategy (theme keywords → preprocessed → full query)
- **Quality Filtering**: Configurable similarity thresholds (default: 0.3)
- **Backward Compatibility**: All existing methods work unchanged

**3. Production-Ready Infrastructure**
- Comprehensive test suite with >90% coverage
- Production deployment documentation and health checks
- CI/CD integration examples
- Monitoring and alerting guidelines

**Example Usage:**
```python
from config.theme_reformulator import ThemeReformulator

# Initialize with model-aware configuration
reformulator = ThemeReformulator("config/themes.json", model_id="bge-large")

# Before Phase 3A (simple expansion)
expanded_terms = reformulator.expand_query_terms("What do laureates say about fairness?")
# Returns: {"justice", "fairness", "law", "morality", "rights", "equality", "injustice"}

# After Phase 3A (ranked expansion)
ranked_expansions = reformulator.expand_query_terms_ranked(
    "What do laureates say about fairness?", 
    similarity_threshold=0.3
)
# Returns: [("fairness", 0.95), ("justice", 0.87), ("equality", 0.82), ...]

# Get expansion statistics for monitoring
stats = reformulator.get_expansion_stats("justice and equality")
print(f"Ranked expansions: {stats['ranked_expansion_count']}")
```

**Setup and Deployment:**
```bash
# Pre-compute theme embeddings for all models
python scripts/precompute_theme_embeddings.py

# Verify setup
python -c "
from config.theme_embeddings import ThemeEmbeddings
embeddings = ThemeEmbeddings('bge-large')
print(f'Loaded {embeddings.get_embedding_stats()[\"total_keywords\"]} theme embeddings')
"
```

**Performance Benefits:**
- **Higher Relevance**: Ranked expansions improve retrieval quality by 20%+
- **Reduced Noise**: Pruning eliminates 30-40% of low-quality expansions
- **Better Coverage**: Semantic variants improve recall for ambiguous queries
- **Fast Expansion**: <100ms for typical queries with pre-computed embeddings

See [`docs/THEME_EMBEDDINGS.md`](./docs/THEME_EMBEDDINGS.md) for comprehensive documentation and [`docs/PRODUCTION_DEPLOYMENT.md`](./docs/PRODUCTION_DEPLOYMENT.md) for deployment guidelines.

---

## 🔎 RAG Pipeline Overview

All retrieval-augmented generation (RAG) logic is implemented in [`rag/README.md`](rag/README.md). See that file for:
- File/class overview
- Full pipeline architecture diagram
- API usage and configuration
- Query router, intent classification, and thematic search details

---

## 🔍 Thematic Search & Query Reformulation

### Thematic Query Expansion

For queries about themes (e.g., "What do laureates say about justice?"), the system uses a two-step process:

1. **ThemeReformulator** (see `config/theme_reformulator.py`):
   - Loads a mapping of canonical themes to keywords (see `config/themes.json`).
   - Lemmatizes both the user query and the theme keywords using spaCy for robust matching.
   - Expands the query to include all related terms for each detected theme.

2. **ThematicRetriever** (see `rag/thematic_retriever.py`):
   - Reformulates the query using the expanded set of theme keywords.
   - Embeds the reformulated query and retrieves the top-k most relevant chunks from the vector store.
   - Logs both the original and reformulated query for transparency.

**Example:**

User query: `"What do laureates say about morality?"`

- ThemeReformulator expands to: `justice fairness law morality rights equality injustice`
- ThematicRetriever embeds this expanded string for semantic search, improving recall and relevance.

### Modularity & Testability
- Thematic logic is encapsulated in dedicated, testable classes.
- Easy to extend with new themes, keywords, or retrieval strategies.
- Logging and docstrings throughout for transparency and maintainability.

### Usage Example
```python
from rag.thematic_retriever import ThematicRetriever
from config.theme_reformulator import ThemeReformulator

# Instantiate with your embedder and retriever
reformulator = ThemeReformulator("config/themes.json")
thematic_retriever = ThematicRetriever(embedder, retriever)

query = "What do laureates say about morality?"
chunks = thematic_retriever.retrieve(query, top_k=15)
# Use chunks for prompt construction, etc.
```

---

## 🧪 **Testing**

See [`tests/README.md`](tests/README.md) for comprehensive testing documentation.

**Quick Test Commands:**
```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest tests/unit/          # Unit tests
python -m pytest tests/integration/   # Integration tests  
python -m pytest tests/e2e/           # End-to-end tests
python -m pytest tests/validation/    # Data validation tests

# Run with coverage
python -m pytest --cov=rag --cov=embeddings --cov=scraper
```

---

## 🔮 **Known Gaps / Future Work**

### **Deferred Features**
The following features have been explicitly deferred and are not planned for immediate implementation:

**Phase 3C - Paraphraser (DEFERRED):**
- Semantic term generation using T5-small or similar models
- Integration with ThemeReformulator for semantic variants
- **Reason**: Current similarity-based expansion provides sufficient coverage without complexity overhead

**Phase 5B/5C - Advanced Chunk Sampling (DEFERRED):**
- Tone classification and style-aware chunk selection
- Diversity balancing algorithms (laureate, temporal, regional)
- Wildcard chunk inclusion for creative inspiration
- Advanced attribution tracking (source URL, date, location)
- **Reason**: Core prompt building system is complete and production-ready

**Phase 5E - Template Analytics (DEFERRED):**
- Template usage analytics and recommendation system
- Template quality metrics and optimization
- Template search and filtering utilities
- **Reason**: Basic template system is sufficient for current needs

### **Remaining TODOs**
The following items are still marked as TODO in documentation but may be implemented based on user feedback:

**CI/CD Integration:**
- Automated test matrix for model-aware testing
- Performance test execution and reporting
- Test coverage reporting and optimization
- Parallel test execution and caching

**Documentation Updates:**
- Keep all phase docs, READMEs, and SPEC.md in sync with codebase status
- Add missing unit/integration tests for advanced features (if implemented)
- Expand documentation for any new features added

### **Future Enhancements (Post-MVP)**
These features are planned for future phases based on user feedback and performance requirements:

**Advanced RAG Features:**
- Prompt suggestion engine (Claude-style examples)
- Memory/context provider for session-aware follow-ups
- RAG evaluation logging (e.g., with Weights & Biases)
- Support for additional Nobel categories (Peace, Physics, etc.)

**UI/UX Enhancements:**
- Timeline or cluster visualization by theme, decade, or demographic
- Gender/region topic analysis
- Per-year or per-laureate comparison UX
- Advanced filtering and search capabilities

**Performance Optimizations:**
- Further tuning based on real-world usage
- Advanced chunk selection algorithms
- Model performance optimization
- Caching and retrieval improvements

---

## 📚 **Documentation**

| Document                                 | Description                                                      |
|------------------------------------------|------------------------------------------------------------------|
| [SPEC.md](SPEC.md)                       | Master project specification, schema, data sources, and goals.   |
| [rag/README.md](rag/README.md)           | Detailed RAG pipeline documentation and API reference.           |
| [tests/README.md](tests/README.md)       | Comprehensive test coverage, environment notes, and test philosophy. |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Milestones, phases, and planned features.                |
| [META_ANALYSIS.md](META_ANALYSIS.md)      | Strategy, design notes, and meta-level analysis.                 |

---

## 📋 **Changelog**

### **June 2025 - Major RAG Pipeline Enhancements**
- **Phase 5A/5F**: Intelligent Prompt Builder System with metadata-aware formatting and citation scaffolding
- **Phase 4**: Unified retrieval logic with consistent score thresholds and guaranteed minimum results
- **Phase 3A/3B**: Enhanced thematic retrieval with similarity-based expansion and weighted scoring
- **Phase 2**: Enhanced intent classification with structured results and confidence scoring
- **Phase 1**: Mode-aware retriever abstraction and comprehensive validation system

### **January 2025 - Core Infrastructure Completion**
- **Theme Embedding Infrastructure**: Pre-computed embeddings with similarity-based expansion
- **Weighted Retrieval**: Exponential weight scaling for improved relevance
- **Test Suite Consolidation**: Comprehensive test coverage with organized structure
- **Model-Aware Configuration**: Centralized config for all embedding and retrieval operations

### **2024 - Foundation & MVP**
- **Data Pipeline**: Nobel Literature scraping, chunking, and embedding
- **RAG Pipeline**: FAISS indexing, retrieval, and LLM integration
- **Frontend**: Streamlit UI with query interface
- **Testing**: Unit, integration, and validation test suites

---

## 📄 **License**

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

✍️ Author
Built by Joe Gonwa as a structured learning project in GenAI and RAG systems.
Feedback, PRs, and suggestions are always welcome!

## Running the Backend (FastAPI)

To run the backend, always start from the NobelLM project root directory. This ensures that the `rag` module and other top-level packages are importable by Python.

**Example (development):**

```bash
cd /path/to/NobelLM
uvicorn backend.app.main:app --reload --port 8000
```

**If you run from within the `backend/` directory, you will get an error like:**

```
ModuleNotFoundError: No module named 'rag'
```

**Troubleshooting:**
- Always run commands from the NobelLM root.
- Alternatively, set the `PYTHONPATH` to the project root:
  ```bash
  PYTHONPATH=$(pwd) uvicorn backend.app.main:app --reload --port 8000
  ```
- This is required for all scripts that import from top-level packages like `rag`, `embeddings`, etc.
