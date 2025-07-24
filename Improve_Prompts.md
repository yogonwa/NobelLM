# Task: Improve Thematic Answer Quality with Clean Synthesis Prompt

---

## Summary

This task introduces a new prompt template (`thematic_synthesis_clean`) designed to improve generative responses to thematic queries in the NobelLM RAG pipeline. It enforces:

- **Cohesive synthesis** across retrieved chunks
- **Elimination of literal references** to “speeches,” “excerpts,” or enumeration like “the first speech”
- **A natural, essay-like tone** written from the perspective of a cultural historian

This template aims to replace robotic, summary-style outputs with fluid and insightful thematic explorations.

---

## Target Files

- `config/prompt_templates.json`
- `rag/prompt_builder.py`
- (Optional) `rag/query_router.py` if adding routing logic

---

## Deliverables

### 1. Add New Prompt Template to `prompt_templates.json`

Append the following to the existing prompt configuration file:

```json
"thematic_synthesis_clean": {
  "template": "You are a cultural historian writing an essay on the theme of '{query}' as expressed through the voices of Nobel Literature laureates across time and place.\n\nYour goal is to synthesize their ideas into a coherent narrative. Do not reference the excerpts or speeches directly. Instead, express the insights as unified observations, drawing out tensions, shared values, and philosophical differences.\n\nUse a natural, flowing tone — one that feels human and thoughtful. You may reference specific cultures or authors sparingly when it adds depth.\n\nEssay:\n{context}",
  "intent": "thematic",
  "tags": ["thematic", "synthesis", "essay", "non-referential", "cohesive"],
  "chunk_count": 12,
  "citation_style": "inline",
  "tone_preference": "reflective",
  "version": "1.0"
}
```

---

### 2. Update `prompt_builder.py` (if needed)

- Ensure that the `PromptBuilder.build_thematic_prompt()` method selects this template based on:
  - Explicit match to `intent="thematic"` **and** tag `"non-referential"` or `"synthesis"`
- Or update `_get_template_for_intent()` to prefer this over `thematic_exploration` if present
- **Do not rename the method** — keep using `build_thematic_prompt()`

---

### 3. (Optional) Update Routing Logic

- In `query_router.py` (or wherever `QueryIntent.THEMATIC` is dispatched):
  - Add logic to prefer `thematic_synthesis_clean` when the query contains phrases like:
    - "synthesis", "draw connections", "how do laureates think about...", etc.
  - Fallback to existing `thematic_exploration` as needed

---

### 4. Update `README.md` in `config/` or `rag/`

Document the new template:

- **Name:** `thematic_synthesis_clean`
- **Purpose:** High-quality thematic synthesis with no literal reference to source text
- **Tags:** `["thematic", "synthesis", "non-referential"]`
- **Tone:** Reflective, essay-style, cohesive narrative

---

## Cursor Instructions

- Use exact template string in JSON with escaped `\n` line breaks
- Do **not** overwrite existing templates
- Maintain alphabetical key ordering if sorting is used
- If modifying query routing, **comment the fallback behavior clearly**
- Validate prompt formatting via test query (e.g. "What do laureates say about justice and freedom?")

---

## Example Output Improvement

**Old Style:**
> “The first speech presents… The second speech discusses…”

**New Style:**
> “Nobel laureates often frame justice not as a universal constant but as a reflection of cultural norms and personal conviction. Across generations, their voices express a struggle between moral clarity and societal ambiguity…”

---

## Status Checklist

- [x] Template added to `prompt_templates.json`
- [x] `PromptBuilder` behavior updated
- [ ] (Optional) Routing logic refined
- [x] Documentation updated

---

**Task ID:**

`cursor_task_thematic_synthesis_clean_prompt_v1`