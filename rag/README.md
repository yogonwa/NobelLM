# Query Engine – NobelLM RAG

**Status: COMPLETE as of June 2025.**

This module provides a modular, extensible, and testable interface for querying the Nobel Literature corpus using retrieval-augmented generation (RAG).

## Features
- Embeds user queries using MiniLM (all-MiniLM-L6-v2)
- Retrieves top-k relevant chunks from FAISS index
- Supports metadata filtering (e.g., by country, source_type)
- Constructs prompts for GPT-3.5
- Calls OpenAI API (with dry run mode)
- Returns answer and source metadata

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
    score_threshold: float = 0.25
) -> Dict[str, Any]:
    """
    Orchestrate the query pipeline: embed, retrieve, filter, prompt, and answer.
    Returns a dict with 'answer' and 'sources'.
    """
```

#### Example Usage
```python
# Simple query (dry run)
response = query("What do laureates say about justice?", dry_run=True)
print(response["answer"])
print(response["sources"])

# Filtered query (e.g., only USA Nobel lectures)
response = query(
    "What do USA winners talk about in their lectures?",
    filters={"country": "USA", "source_type": "nobel_lecture"},
    dry_run=True
)

# Real OpenAI call (requires API key)
response = query(
    "How do laureates describe the role of literature in society?",
    dry_run=False
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