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