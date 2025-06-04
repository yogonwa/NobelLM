# Query Engine – NobelLM RAG

**Status: COMPLETE as of June 2025.**

This module provides a modular, extensible, and testable interface for querying the Nobel Literature corpus using retrieval-augmented generation (RAG).

---

## 📂 RAG Module File/Class Overview

| File                      | Main Classes/Functions         | Description                                                                                 |
|---------------------------|-------------------------------|---------------------------------------------------------------------------------------------|
| `query_engine.py`         | `query`                       | Orchestrates the full RAG pipeline: intent, retrieval, prompt, LLM, answer.                 |
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

## Model-Aware Configuration

All RAG and embedding logic is now **model-aware and config-driven**. The embedding model, FAISS index, and chunk metadata paths are centrally managed in [`rag/model_config.py`](./model_config.py):

- To swap models (e.g., BGE-Large vs MiniLM), pass `model_id` to the query or embedding functions, or change the default in the config.
- All file paths, model names, and embedding dimensions are set in one place.
- Consistency checks ensure the loaded model and index match in dimension, preventing silent errors.
- Enables easy A/B testing and reproducibility.

**Example:**
```python
from rag.query_engine import query
from rag.model_config import DEFAULT_MODEL_ID

# Query using the default model (BGE-Large)
response = query("What do laureates say about justice?", dry_run=True)

# Query using MiniLM
response = query("What do laureates say about justice?", dry_run=True, model_id="miniLM")
```

**To add a new model:**
- Add its config to `rag/model_config.py`.
- All downstream code will pick it up automatically.

---

## API Usage

### Main Function
```python
from rag.query_engine import query
```

#### Signature
```python
def query(
    query_string: str,
    filters: Optional[Dict[str, Any]] = None,
    dry_run: bool = False,
    k: int = 3,
    score_threshold: float = 0.25,
    model_id: str = None
) -> Dict[str, Any]:
    """
    Orchestrate the query pipeline: embed, retrieve, filter, prompt, and answer.
    Model-aware: uses the embedding model, index, and metadata for the specified model_id.
    Returns a dict with 'answer' and 'sources'.
    """
```

#### Example Usage
```python
# Simple query (dry run, default model)
response = query("What do laureates say about justice?", dry_run=True)
print(response["answer"])
print(response["sources"])

# Query with MiniLM
response = query(
    "What do USA winners talk about in their lectures?",
    filters={"country": "USA", "source_type": "nobel_lecture"},
    dry_run=True,
    model_id="miniLM"
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
      "score": 0.53,
      "text_snippet": "Bob Dylan's speech at the Nobel Banquet ..."
    },
    # ...
  ]
}
```

---

## Model Consistency & Safety
- The pipeline checks that the loaded model and FAISS index have matching embedding dimensions.
- If there is a mismatch, a clear error is raised.
- This prevents silent failures and ensures reliable, reproducible results.

---

## Environment Variables
- `OPENAI_API_KEY` – Your OpenAI API key (required for real queries)
- `TOKENIZERS_PARALLELISM=false` – (Optional) Suppress HuggingFace tokenizers parallelism warning

You can add these to your `.env` file:
```
OPENAI_API_KEY=sk-...
TOKENIZERS_PARALLELISM=false
```

---

## Notes
- Dry run mode (`dry_run=True`) does not call OpenAI and is safe for CI/testing.
- Filtering supports any metadata field present in your chunk index (e.g., country, source_type).
- The engine loads the embedding model and FAISS index only once per process for efficiency.
- Errors and warnings are logged using Python's logging module.
- **All chunking and embedding outputs are model-specific:**
  - `/data/chunks_literature_labeled_{model}.jsonl` (token-based, model-aware chunks)
  - `/data/literature_embeddings_{model}.json` (JSON array, each object contains chunk metadata and embedding vector)
  - `/data/faiss_index_{model}/index.faiss` and `/data/faiss_index_{model}/chunk_metadata.jsonl`

---

## Example CLI Test
See `rag/test_query_engine.py` for a ready-to-run test script demonstrating dry run, filtering, and real OpenAI queries.

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