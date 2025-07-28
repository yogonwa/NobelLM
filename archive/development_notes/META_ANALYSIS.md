# Enhanced Retrieval & Prompting Strategy
_Nobel Laureate Speech Explorer – Strategy Module_

**June 2025–June 2024 Progress Update:**
- Hybrid scoped thematic queries (e.g., "What did Toni Morrison say about justice?") are now fully supported. The intent classifier detects both full and last name scoping, and the query router applies laureate filters for thematic queries as needed.
- Modular intent classification and routing are implemented and tested, with robust test coverage for all query types and hybrid scenarios.
- Prompt templates for factual, thematic, and generative queries are in place and used appropriately.
- All retrieval, prompt, and frontend logic for hybrid and scoped queries is integrated and documented.
- All related tasks (see TASKS.md Task NN and 13b) are **complete** and verified.

This document defines advanced strategies for query handling, retrieval, prompt formulation, and multi-dimensional scoring to support meta-analysis and thematic search.

## Overview

Current retrieval uses top-k cosine similarity search from a FAISS index of embedded speech chunks. While this works well for factual lookups, it needs refinement for analytical, thematic, and generative queries.

## Query Typology & Strategy Routing

A **Query Strategy Router** determines how to handle each query:

| Query Type         | Description                        | Retrieval Strategy                | Prompt Strategy                        |
|--------------------|------------------------------------|------------------------------------|----------------------------------------|
| Factual            | Direct fact lookup                 | top_k = 5, score threshold        | Insert raw chunks                      |
| Thematic/Analytical| Patterns, comparisons, themes      | top_k = 10–15, filter by type     | Insert more chunks or summarize them   |
| Generative/Stylistic| Writing, mimicry, tone            | No retrieval or sample curated     | Use as stylistic primers, not anchors  |

Detection methods:
- **Rule-based:** Keywords like "theme", "style", "typical", "patterns"
- **LLM-inferred:** (planned for post-MVP)

## Retrieval Strategy

### Dynamic Retrieval Configuration

- **Infer `top_k` dynamically** based on query intent
- **Optional filters:** `source_type`, `country`, `gender`, `category`
- **Similarity score behavior:**
  ```python
  if intent == 'thematic':
      use_top_k = 15
      ignore_score_threshold = True
  elif intent == 'factual':
      use_top_k = 5
      apply_score_threshold = 0.25
  ```

### Fallback Mechanisms
- If < N chunks retrieved: relax filters or threshold
- For thematic queries: ignore low scores to allow diverse input
- For factual queries: maintain higher similarity threshold (e.g., > 0.3)

## Prompt Engineering

### Base Structure
```
Answer the question using only the context below...
[Context Chunks]
Question: [User Query]
Answer:
```

### Query-Specific Prompting
- **Factual Queries:** Direct insertion of most relevant chunks
- **Thematic Queries:** 
  - Summarize 15+ chunks before prompt
  - Example: "Based on the following speeches, what themes emerge?"
- **Generative Queries:**
  - Use curated chunks as style examples
  - Focus on tone and structure, not content

## Generative & Stylistic Analysis

For creative prompts (e.g., "Write in the style of a Nobel laureate"), use:

### Chunk Selection Criteria
- High sentiment scores (awe, reverence, depth)
- Rich vocabulary and complex phrasing
- Preferably from `source_type = nobel_lecture`
- Sample 5–10 chunks as style primers

### Implementation Notes
- Tag chunks with style markers during preprocessing
- Consider caching "exemplar" chunks for common style requests
- Use embeddings to find stylistically similar passages

## Multi-Dimensional Scoring

Reference table for chunk analysis and filtering:

| Dimension         | Description                    | Tools / Libraries                |
|-------------------|-------------------------------|----------------------------------|
| Sentiment         | Positive/Negative/Neutral     | transformers, nltk, VADER        |
| Emotion           | Joy, sadness, trust, anger    | go-emotions, roberta-base        |
| Lexical Richness  | Vocabulary diversity          | spacy, textstat                  |
| Readability       | Grade level, complexity       | textstat                         |
| Style Similarity  | Compare to Nobel corpus       | Vector clustering, fine-tuning   |
| Topic Modeling    | Dominant themes               | BERTopic, KeyBERT                |

These scores enable:
- Intelligent chunk sampling
- Style-aware retrieval
- Theme clustering

## Implementation Tasks

```json
{
  "id": "13b",
  "title": "Enhanced Query Routing + Prompt Framing",
  "description": "Implement rule-based Query Strategy Router and retrieval tuning behavior based on query type. Refine prompt construction for each path.",
  "steps": [
    "Add rule-based intent classifier (keywords: theme, pattern, typical, style, write like)",
    "Route query to: Factual, Thematic, or Generative paths",
    "For Factual: Use top_k=5, apply score threshold",
    "For Thematic: Use top_k=15, ignore threshold, optionally summarize",
    "For Generative: Sample stylistic chunks, use as examples",
    "Update prompt templates for each type",
    "Expose inferred path and top_k choice in logs",
    "Document in `rag/README.md`"
  ],
  "status": "Complete",
  "priority": "High"
}
```

---

## Metadata Handler & Registry-Based Factual QA (**Complete**)

### Overview
To efficiently answer direct factual queries (e.g., "Who won in 2017?", "What country is Toni Morrison from?"), the system uses a registry-based metadata handler before invoking RAG or LLM logic.

### Implementation Approach
- **Registry Pattern:**
  - Each factual query type is represented as a `QueryRule` with a regex pattern and a handler function.
  - The registry (`FACTUAL_QUERY_REGISTRY`) is extensible—new rules can be added for new query types.
- **Handlers:**
  - Each handler extracts entities from the query, searches the metadata, and returns a formatted answer or fallback.
  - Examples include: year of award, country, first/last laureate by gender or country, birth/death dates, prize motivation, years with no award, and more.
- **Integration:**
  - The main handler (`handle_metadata_query`) uses `match_query_to_handler` to find and execute the right handler for a query.
  - If no handler matches, the system falls back to RAG.
- **Testing:**
  - Comprehensive unit tests cover all registry patterns, including edge cases and negative cases.

### Benefits
- **Efficiency:** Direct answers from metadata are fast and accurate, avoiding unnecessary LLM calls.
- **Extensibility:** New factual query types can be added with minimal code changes.
- **Transparency:** Each answer includes the rule used, aiding debugging and explainability.

### Status
- **Complete:** All planned factual patterns (A–F and more) are implemented, tested, and passing.
- **Ready for integration:** The handler is ready to be used in the query router pipeline.

---

## Progress Summary
- **Rule-based query router:** Complete and unit tested
- **Metadata handler/registry:** Complete and unit tested
- **Prompt template selector:** Factual, thematic, and generative templates implemented
- **Hybrid scoped thematic queries:** Complete and tested
- **All core factual QA and hybrid query logic is robust, extensible, and ready for integration**

---

## Next Steps
- [Placeholder for further discussion]
+ - All planned hybrid and scoped query features are implemented and tested. No immediate next steps required for core retrieval, routing, or prompt logic.

---

## References

- See `NOTES.md` for chunk retrieval strategy details
- See `rag/query_engine.py` for current implementation
- See project documentation for overall architecture

---

## Frontend Display Note: Metadata vs RAG Responses

As the system now supports both direct metadata answers and RAG/LLM-generated responses, the frontend results page may need to adapt its display logic:
- **Metadata answers** are structured, direct, and often include explicit source fields (e.g., laureate, year, country).
- **RAG/LLM answers** are contextual, may include cited text chunks, and are generated from retrieved passages.

**Recommendation:**
- The frontend should detect the response type and display metadata answers in a concise, fact-focused card, while RAG/LLM answers may include context snippets, citations, or expandable details.
- This distinction improves user clarity and supports future UI/UX enhancements as the system evolves.

---

## JSON Response: Include Answer Type

To support frontend display logic and downstream analytics, the JSON answer response should include a field indicating the answer type, such as:
- `'answer_type'`: `'factual'`, `'thematic'`, `'generative'`, `'metadata'`, or `'rag'`
- This enables the frontend to render the appropriate UI and allows for easy tracking of which pipeline path was used for each answer.

## June 2025 Update – Integration and Robustness

- The metadata handler and registry are now fully integrated into the query router pipeline.
- Laureate metadata is flattened at load time (see `flatten_laureate_metadata` in `rag/query_engine.py`), so all factual query handlers receive a flat list of laureate dicts (each with `full_name`, `year_awarded`, `country`, `category`, etc.).
- This design ensures all factual queries are robust and prevents KeyError bugs due to schema mismatches.
- The registry bug (mixing `pattern` and `patterns`) is fixed; all rules now use `patterns=[...]`.
- The backend always includes an `answer_type` field in responses, allowing the frontend to distinguish between metadata and RAG answers and render them appropriately.
- Unit tests for the metadata handler should use the flat structure; integration tests should cover both factual and RAG queries.
- If analytics or data scripts require the original nested structure, use a separate loader or document the difference.

### Remaining Work
- Expand prompt templates for thematic and generative queries.
- Add more logging and observability for routing decisions.
- Ensure analytics/data scripts use the correct metadata loader for their needs.
- Continue to expand the factual query registry as new types are identified.
- update tests for metadata flattening function and integration test with patterns registry [DONE]
- UI tweaks to factual responses- clear input, consider including prize motivation [DONE]

### July 2025 Progress – Pattern Robustness & Test Coverage

- All factual query patterns in the metadata handler are now robust to extra trailing context (e.g., "Nobel Prizes in Literature") and punctuation.
- The registry and tests cover all pattern variants, including those with additional phrasing at the end of the query.
- The metadata flattening utility is now in `rag/metadata_utils.py` for lightweight, decoupled import in tests and other modules.
- Test collection and execution is now fast due to modularization and lazy loading of heavy resources.

## Next Steps
- [Placeholder for further discussion]