# Query Engine – NobelLM RAG

**Status: COMPLETE as of June 2025.**

This module provides a modular, extensible, and testable interface for querying the Nobel Literature corpus using retrieval-augmented generation (RAG).

---

## 📂 RAG Module File/Class Overview

| File                      | Main Classes/Functions         | Description                                                                                 |
|---------------------------|-------------------------------|---------------------------------------------------------------------------------------------|
| `query_engine.py`         | `answer_query`                | Canonical entry point for the RAG pipeline. Routes queries via QueryRouter, handles all retrieval modes safely. |
| `query_router.py`         | `QueryRouter`, `IntentClassifier`, `PromptTemplateSelector` | Classifies queries, selects retrieval config, prompt template, and routes to metadata/RAG.   |
| `thematic_retriever.py`   | `ThematicRetriever`           | Expands thematic queries, embeds, and retrieves relevant chunks.                             |
| `retriever.py`            | `BaseRetriever`, `InProcessRetriever`, `SubprocessRetriever`, `query_index` | Retrieves top-k chunks from FAISS index, supports mode-aware (in-process/subprocess) logic. |
| `dual_process_retriever.py`| `retrieve_chunks_dual_process`| Subprocess-based FAISS retrieval for Mac/Intel safety.                                      |
| `faiss_index.py`          | `load_index`, `reload_index`, `health_check` | Loads, reloads, and checks FAISS index integrity.                                           |
| `model_config.py`         | `get_model_config`            | Central config for model names, paths, embedding dims.                                      |
| `intent_classifier.py`    | `IntentClassifier`            | Rule-based classifier for factual/thematic/generative queries.                              |
| `metadata_handler.py`     | `handle_metadata_query`       | Answers factual queries directly from laureate metadata.                                     |
| `metadata_utils.py`       | `flatten_laureate_metadata`   | Flattens and loads laureate metadata for factual QA.                                        |
| `utils.py`                | `format_chunks_for_prompt`    | Formats retrieved chunks (with metadata) for LLM prompt context.                             |
| `cache.py`                | `get_faiss_index_and_metadata`, `get_model` | Streamlit-cached loaders for index, metadata, and models.                                   |

---

## 🗺️ RAG Pipeline Architecture

View the interactive architecture diagram here:  
[NobelLM RAG Pipeline – Mermaid Chart](https://www.mermaidchart.com/app/projects/f11ebb0b-c097-43bd-80d5-e9740319bf5e/diagrams/4ac34c1b-cea0-40b8-a1d3-10014bbcf904/version/v0.1/edit)

---

## Features
- Embeds user queries using a **model-aware, config-driven approach** (BGE-Large or MiniLM, easily swappable)
- Retrieves top-k relevant chunks from the correct FAISS index (model-specific)
- Supports metadata filtering (e.g., by country, source_type)
- Constructs prompts for GPT-3.5
- Calls OpenAI API (with dry run mode)
- Returns answer and source metadata

---

## Mode-Agnostic Retriever Layer (June 2025 Refactor)

**New as of June 2025:** NobelLM now uses a modern, mode-agnostic retriever abstraction for all chunk retrieval, both factual and thematic.

- All retrieval is routed through a `BaseRetriever` interface, with two main implementations:
  - `InProcessRetriever`: Runs embedding and FAISS search in-process (Linux/prod, default).
  - `SubprocessRetriever`: Runs FAISS search in a subprocess for Mac/Intel safety (set `NOBELLM_USE_FAISS_SUBPROCESS=1`).
- A factory function (`get_mode_aware_retriever`) selects the correct backend based on environment.
- The interface is always `retrieve(query: str, top_k: int, filters: dict) -> List[dict]`.
- **Standard Default:** The retriever interface defines `top_k=5` as the standard default. All implementations (in-process, subprocess, thematic) must respect this value when passed from callers.
- **Score Threshold:** All retrieval paths now apply a consistent score threshold (default 0.2) with minimum and maximum return counts per query type. This ensures consistent prompt construction and prevents prompt bloat.
- **Index Type Requirement:** The retriever requires a FAISS `IndexFlatIP` index for metadata filtering. Other index types (IVF, PQ, HNSW) are not supported for filtered queries.
- Thematic and factual queries both use this interface—no more shape/type bugs or mode-specific logic in callers.
- **Extensible:** You can add new backends (e.g., ElasticSearch, hybrid, remote API) by subclassing `BaseRetriever` and updating the factory.

**Example usage:**
```python
from rag.query_engine import answer_query

# Simple query (uses default model)
response = answer_query("What do laureates say about justice?")
print(response["answer"])
print(response["sources"])

# Query with MiniLM
response = answer_query(
    "What do USA winners talk about in their lectures?",
    model_id="miniLM"
)
```

This refactor makes the pipeline robust, testable, and future-ready for multi-backend or hybrid search.

## Model-Aware Configuration

All RAG and embedding logic is now **model-aware and config-driven**. The embedding model, FAISS index, and chunk metadata paths are centrally managed in [`rag/model_config.py`](./model_config.py):

- To swap models (e.g., BGE-Large vs MiniLM), pass `model_id` to `answer_query()`, or change the default in the config.
- All file paths, model names, and embedding dimensions are set in one place.
- Consistency checks ensure the loaded model and index match in dimension, preventing silent errors.
- Enables easy A/B testing and reproducibility.
- **NEW: Standard defaults** (e.g., top_k=5) are defined in the config and respected by all implementations.

**Example:**
```python
from rag.query_engine import answer_query
from rag.model_config import DEFAULT_MODEL_ID, get_model_config

# Get config for a specific model
config = get_model_config("miniLM")
print(f"Using model: {config['model_name']}")
print(f"Index path: {config['index_path']}")

# Query using the default model (BGE-Large)
response = answer_query("What do laureates say about justice?")

# Query using MiniLM
response = answer_query("What do laureates say about justice?", model_id="miniLM")
```

**To add a new model:**
1. Add its config to `rag/model_config.py`:
   ```python
   MODEL_CONFIGS["new-model"] = {
       "model_name": "path/to/model",
       "embedding_dim": 512,
       "index_path": "data/faiss_index_new-model/index.faiss",
       "metadata_path": "data/faiss_index_new-model/chunk_metadata.jsonl",
   }
   ```
2. All downstream code will pick it up automatically.
3. Run the model-aware tests to verify behavior.

---

## API Usage

### Main Function
```python
from rag.query_engine import answer_query  # Recommended
# from rag.query_engine import query  # DEPRECATED
```

#### Signature
```python
def answer_query(
    query_string: str,
    model_id: str = None,
    score_threshold: float = 0.2,  # Minimum similarity score
    min_return: int = None,        # Minimum chunks to return (query-type specific)
    max_return: int = None         # Maximum chunks to return (query-type specific)
) -> Dict[str, Any]:
    """
    Unified entry point for the frontend. Routes query via QueryRouter.
    Uses model_id only to instantiate the retriever, then forgets it.
    Downstream logic (prompt building, answer formatting) sees only chunks/metadata.

    Args:
        query_string: The user's query
        model_id: Optional model identifier used only to get the appropriate retriever.
                 If None, uses DEFAULT_MODEL_ID from model_config.
        score_threshold: Minimum similarity score for chunks (default: 0.2)
        min_return: Minimum number of chunks to return (query-type specific)
        max_return: Maximum number of chunks to return (query-type specific)

    Returns:
        dict with 'answer_type', 'answer', 'metadata_answer', and 'sources'
    """
```

#### Example Usage
```python
# Simple query (uses default model and score threshold)
response = answer_query("What do laureates say about justice?")
print(response["answer"])
print(response["sources"])

# Query with custom score threshold and return limits
response = answer_query(
    "What do USA winners talk about in their lectures?",
    model_id="miniLM",
    score_threshold=0.3,
    min_return=3,
    max_return=10
)
```

#### Output Schema
```python
{
  "answer": "...",
  "sources": [
    {
      "chunk_id": "2016_dylan_acceptance_speech_0",
      "source_type": "acceptance_speech",
      "laureate": "Bob Dylan",
      "year_awarded": 2016,
      "score": 0.53,  # Always >= score_threshold unless min_return fallback
      "text_snippet": "Bob Dylan's speech at the Nobel Banquet ..."
    },
    # ...
  ],
  "answer_type": "rag",  # or "metadata" for factual queries
  "metadata_answer": None  # or dict for metadata answers
}
```

### Legacy Function (Deprecated)
```python
from rag.query_engine import query  # DEPRECATED
```

The legacy `query()` function is deprecated and will be removed in a future version. It has known issues:
1. Inconsistent score threshold handling
2. Subprocess mode (USE_FAISS_SUBPROCESS=1) passes embeddings instead of query strings
3. No support for min/max return counts

Use `answer_query()` instead for a fully consistent and robust retrieval + prompting pipeline.

---

## Model Consistency & Safety
- The pipeline checks that the loaded model and FAISS index have matching embedding dimensions.
- If there is a mismatch, a clear error is raised.
- This prevents silent failures and ensures reliable, reproducible results.

---

## Environment Variables
- `OPENAI_API_KEY` – Your OpenAI API key (required for real queries)
- `TOKENIZERS_PARALLELISM=false` – (Optional) Suppress HuggingFace tokenizers parallelism warning
- `NOBELLM_USE_FAISS_SUBPROCESS=1` – (Optional) Use subprocess mode for Mac/Intel safety

You can add these to your `.env` file:
```
OPENAI_API_KEY=sk-...
TOKENIZERS_PARALLELISM=false
NOBELLM_USE_FAISS_SUBPROCESS=1  # Only on Mac/Intel
```

---

## Notes
- The engine loads the embedding model and FAISS index only once per process for efficiency.
- Errors and warnings are logged using Python's logging module.
- **All chunking and embedding outputs are model-specific:**
  - `/data/chunks_literature_labeled_{model}.jsonl` (token-based, model-aware chunks)
  - `/data/literature_embeddings_{model}.json` (JSON array, each object contains chunk metadata and embedding vector)
  - `/data/faiss_index_{model}/index.faiss` and `/data/faiss_index_{model}/chunk_metadata.jsonl`

---

## Example CLI Test
See `rag/test_query_engine.py` for a ready-to-run test script demonstrating the canonical `answer_query()` function.

# Nobel Laureate Speech Explorer – RAG Module

## Query Router & Intent Classification

### Overview
The query router uses a modular, extensible intent classification system to determine how to handle user queries. The first implementation is a rule-based `IntentClassifier` that assigns each query to one of three types: **factual**, **thematic/analytical**, or **generative/stylistic**. This classification determines retrieval parameters, prompt templates, and downstream logic.

### Rule-Based IntentClassifier

#### Query Types & Routing Logic

**1. Factual Queries**
- **Definition:** Direct, specific questions seeking a fact, quote, or short summary from one or few sources.
- **Examples:**
  - "What did Toni Morrison say about justice?"
  - "When did Kazuo Ishiguro win the Nobel Prize?"
  - "Where was Camilo José Cela born?"
  - "Summarize the 1989 acceptance speech."
- **Trigger Keywords:** what, when, who, where, how many, quote, summarize, give me the speech
- **Rule:** If the query contains question words and does not include thematic or stylistic keywords → classify as factual
- **Routing:** Search metadata store or query RAG with `top_k = 5`

**2. Thematic / Analytical Queries**
- **Definition:** Queries looking for patterns, themes, or comparisons across time, demographics, or source types.
- **Examples:**
  - "What are common themes in Nobel lectures?"
  - "How have topics changed over time?"
  - "Compare speeches from U.S. vs. European laureates."
  - "What motifs are recurring across decades?"
- **Trigger Keywords:** theme, themes, pattern, patterns, motif, motifs, compare, comparison, differences, similarities, trend, trends, common, typical, recurring, across, evolution
- **Rule:** If the query includes any thematic/analytical keyword → classify as thematic
- **Routing:** Use RAG with `top_k = 15`; optionally summarize top-k results before answering

**3. Generative / Stylistic Queries**
- **Definition:** Requests for the LLM to generate or rewrite content in the tone, voice, or style of a Nobel laureate.
- **Examples:**
  - "Write a speech in the style of Toni Morrison."
  - "Compose a Nobel acceptance for a teacher."
  - "Paraphrase this text as if written by a laureate."
  - "Generate a motivational quote like a Nobel winner."
- **Trigger Keywords:** in the style of, like a laureate, write me, compose, mimic, generate, paraphrase, rewrite, as if you were, as a Nobel laureate, draft, emulate
- **Rule:** If the query includes generative or stylistic phrasing → classify as generative
- **Routing:** Retrieve relevant high-tone chunks (manually scored or tagged); format prompt to include samples + instruction; use GPT to generate output

#### Precedence
- If a query matches multiple types, **generative** takes precedence, then **thematic**, then **factual**.

#### Example Implementation
See `IntentClassifier` in `query_router.py` for the current rule-based logic. The classifier can be extended by adding new keywords, new query types, or swapping in an LLM-based classifier for more nuanced intent detection.

#### Extensibility
- Add new keywords as user patterns emerge
- Add new query types as needed
- Swap in an LLM-based classifier for ambiguous or complex queries (post-MVP)

---

For more details, see the docstrings in `rag/query_router.py` and the [META_ANALYSIS.md](../META_ANALYSIS.md) strategy document.

## Hybrid Thematic + Laureate-Scoped Queries (NEW)

The query router now supports hybrid queries that combine a thematic concept with a specific laureate, e.g.:

> "What did Toni Morrison say about justice?"

- If a query contains both a thematic keyword and a Nobel laureate's name, the intent classifier returns:
  ```python
  {"intent": "thematic", "scoped_entity": "Toni Morrison"}
  ```
- The query router sets `retrieval_config.filters = {"laureate": scoped_entity}` and uses the thematic prompt template.
- Only chunks authored by the specified laureate are retrieved and analyzed.
- The output remains thematically formatted, but is scoped to the laureate.

**Example queries:**
- "What did Gabriel García Márquez say about solitude?"
- "What did Bob Dylan say about music?"

**Notes:**
- Thematic queries without a laureate name still retrieve across all laureates.
- The laureate name list is loaded from `data/nobel_literature.json`.
- All chunk metadata includes a `laureate` field for filtering.

---

# NobelLM RAG Pipeline

## Environment-Aware FAISS Execution (Mac/Intel vs. Linux/Prod)

**On macOS Intel, set the following environment variable to avoid PyTorch/FAISS segfaults:**

```bash
export NOBELLM_USE_FAISS_SUBPROCESS=1
```

This will run FAISS retrieval in a subprocess, isolating it from PyTorch and preventing native library conflicts.

**On Linux, Hugging Face Spaces, or cloud servers, leave this variable unset for maximum speed:**

```bash
unset NOBELLM_USE_FAISS_SUBPROCESS
```

The pipeline will use a fast, unified in-process retrieval mode.

| Environment       | Execution Mode         | Why                                  |
|-------------------|------------------------|---------------------------------------|
| macOS Intel (dev) | Subprocess (isolated)  | Prevent FAISS/PyTorch segfaults      |
| Hugging Face      | Unified process        | Fast, stable Linux container runtime |
| Cloud (EC2, GPU)  | Unified process        | Standard production path             |

---

### Pre-retrieval Metadata Filtering

- Filters (e.g., by gender, country, source_type) are applied to chunk metadata before FAISS search.
- Supported in all retrieval modes (in-process and subprocess).
- Improves efficiency and explainability.
- Only output fields (e.g., chunk_id, text_snippet) are exposed to downstream consumers; internal metadata is not leaked.

---

## 📚 Further Reading & Related Documentation

| Document                       | Description                                                      |
|---------------------------------|------------------------------------------------------------------|
| [Root README.md](../README.md)  | Project overview, setup, features, and high-level architecture.  |
| [SPEC.md](../SPEC.md)           | Master project specification, schema, data sources, and goals.   |
| [tests/README.md](../tests/README.md) | Detailed test coverage, environment notes, and test philosophy. |
| [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) | Milestones, phases, and planned features.                      |
| [META_ANALYSIS.md](../META_ANALYSIS.md) | Strategy, design notes, and meta-level analysis.               |

---

## Mode-Agnostic Retriever Layer (June 2025 Refactor)

**New as of June 2025:** NobelLM now uses a modern, mode-agnostic retriever abstraction for all chunk retrieval, both factual and thematic.

- All retrieval is routed through a `BaseRetriever` interface, with two main implementations:
  - `InProcessRetriever`: Runs embedding and FAISS search in-process (Linux/prod, default).
  - `SubprocessRetriever`: Runs FAISS search in a subprocess for Mac/Intel safety (set `NOBELLM_USE_FAISS_SUBPROCESS=1`).
- A factory function (`get_mode_aware_retriever`) selects the correct backend based on environment.
- The interface is always `retrieve(query: str, top_k: int, filters: dict) -> List[dict]`.
- **Standard Default:** The retriever interface defines `top_k=5` as the standard default. All implementations (in-process, subprocess, thematic) must respect this value when passed from callers.
- **Score Threshold:** All retrieval paths now apply a consistent score threshold (default 0.2) with minimum and maximum return counts per query type. This ensures consistent prompt construction and prevents prompt bloat.
- **Index Type Requirement:** The retriever requires a FAISS `IndexFlatIP` index for metadata filtering. Other index types (IVF, PQ, HNSW) are not supported for filtered queries.
- Thematic and factual queries both use this interface—no more shape/type bugs or mode-specific logic in callers.
- **Extensible:** You can add new backends (e.g., ElasticSearch, hybrid, remote API) by subclassing `BaseRetriever` and updating the factory.

**Example usage:**
```python
from rag.retriever import get_mode_aware_retriever
retriever = get_mode_aware_retriever(model_id)
# Uses standard default top_k=5
chunks = retriever.retrieve("What did laureates say about justice?")
# Override top_k if needed
chunks = retriever.retrieve("What did laureates say about justice?", top_k=10)
```

This refactor makes the pipeline robust, testable, and future-ready for multi-backend or hybrid search. 