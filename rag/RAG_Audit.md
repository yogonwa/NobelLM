🧠 Strategic RAG Pipeline Audit – EPIC Plan
Project Goal:
Elevate the semantic robustness, routing intelligence, and architectural maintainability of the NobelLM RAG pipeline by systematically auditing and improving each of the core logic nodes in the pipeline.

🎯 Motivation
Current pipeline is functionally solid but brittle under edge cases and lacking transparency or adaptability.

Several recent failures (e.g., scalar/segfaults, 0-results from valid queries) stem from implicit logic, inconsistent input/output contracts, and mode-dependent behavior.

Intent classification, routing, and thematic reformulation are static and hard-coded, limiting performance and evolvability.

🔍 Scope: Core Decision Points to Audit
Each area below will get a targeted review, followed by proposed improvements grouped into Phases.

1. Intent Classification
Current: Pattern-based matcher with keyword lists.

Goal: Add confidence scoring, explainability, and embedding fallback.

Refactor target: IntentClassifier.classify()

2. Laureate Scoping
Current: Full name or last name greedy match.

Goal: More granular, rankable, multi-entity support.

Refactor target: _find_laureate_in_query

3. Theme Reformulation
Current: Static expansion of hand-coded themes.

Goal: Add similarity scoring and thematic clustering.

Refactor target: ThemeReformulator.reformulate()

4. Retriever Abstraction
Current: Dual interface (string vs. embedding), manual mode checks.

Goal: Mode-aware retriever with a stable interface and self-contained logic.

Refactor target: retrieve_chunks, query_index, and their wrappers.

5. Prompt Builder
Current: Static templates per query type.

Goal: Add metadata awareness, citation scaffolding, explainable formatting.

Refactor target: build_prompt

6. Score Threshold + Fallback Logic
Current: Inconsistent filtering between old and refactor branches.

Goal: Make fallback behavior explicit and tunable.

Refactor target: retrieve_chunks, post-retrieval logic.

🛠️ Proposed Phases
Phase 1: Resilient Interfaces and Input Handling ✅ COMPLETED
 Wrap retriever in mode-aware abstraction (Retriever.get_top_k_chunks(query: str) always). ✅

 Patch thematic retriever to pass strings, not embeddings. ✅

 Ensure FAISS subprocess receives only valid inputs. ✅

 Add validation early to catch all-zero vectors, shape mismatches. ✅

Phase 2: Intent Classifier Modernization ✅ COMPLETED
 Return structured object: IntentResult { intent, confidence, matched_terms, scoped_entity } ✅

 Load keywords from JSON configs. ✅

 Log decision trace (terms matched, score, fallback reason). ✅

 Add test coverage for scoped queries and ambiguous inputs. ✅

Phase 3: Thematic Reformulation Expansion
 Refactor theme dictionary into config file.

 Support cosine-sim expansion using pre-embedded canonical themes.

 Rank expansions and prune low-similarity ones.

 Optional: Add paraphraser model to generate richer term variants.

Phase 4: Retrieval Logic Enhancements ✅ COMPLETED
 Consolidate score threshold handling and fallback logic.

 Add logging of top_k scores and filtering reasons.

 Ensure all branches guarantee min_k results when possible.

 Return scored results in explainable format.

Phase 5: Prompt Builder Improvements
 Standardize chunk rendering with metadata (e.g., 🎓/🏅 chips).

 Add scaffolding for answer type labeling.

 Include citations inline or footnote-style in prompt.

 Optional: Embed pre- and post-answer framing based on intent.

✅ Deliverables
 Updated and tested code in rag/, query_engine.py, retriever.py, intent_classifier.py

 Rich test suite covering edge cases

 Developer doc: docs/pipeline_audit_summary.md

 Optional blog: "How I Made My RAG Pipeline Smarter (and Safer)"

⏳ Timeline (Suggested)
Phase	Focus	Est. Effort
1	Interface Cleanup + Retrieval Safety	1–2 days
2	Intent Classifier Overhaul	2–3 days
3	Thematic Reformulation	2 days
4	Score/Fallback Logic	1 day
5	Prompt Refinement	1 day

🔄 Next Step
Create one umbrella GitHub issue or Notion epic for this project:
"RAG Pipeline Strategic Refactor & Robustness Initiative"

Break each phase into atomic PRs for clarity and testability.

- consider for future: 
stopword and Inverse Chunk Frequency
-----
 # EPIC: Generative Prompt Pipeline Refactor – Nobel Laureate Speech Explorer

**Date:** 2025-06-05  
**Owner:** Joe Gonwa  
**Goal:** Improve the context delivery and stylistic quality of generative responses using refined chunk sampling, dynamic prompt construction, and intent-aware templates.

---

## 🎯 Problem Statement

Current generative prompts are functional but lack rich context priming and stylistic anchoring. Chunks are retrieved solely by cosine similarity with no genre biasing, and the prompt wrapper is generic.

This leads to:
- Inconsistent tone fidelity to Nobel laureates
- Missed opportunities to reflect laureate diversity (gender, country, theme)
- Limited adaptability to specific creative tasks (e.g., writing an email)

---

## ✅ Objectives

- Improve LLM awareness of tone, genre, and intent
- Dynamically vary prompt structure based on query type
- Enhance chunk sampling logic to prioritize inspirational, thematic content
- Build reusability and future-proofing into the prompt pipeline

---

## 🧱 Key Features and Design

### 1. Intent-Specific Prompt Template
- Add `build_generative_prompt(task_description, chunks)` function
- Template includes:
  - Identity statement (e.g., "You are a Nobel laureate…")
  - Human-written task (e.g., "Draft a job acceptance email…")
  - Clear markers: `--- EXCERPTS START ---` and `--- EXCERPTS END ---`

### 2. Chunk Metadata Formatting
- Tag retrieved chunks with lightweight descriptors:
  - `[🎓 Lecture — Toni Morrison, 1993]`
  - or `[🏅 Ceremony — Gabriel García Márquez, 1982]`
- Helps LLM infer tone and speaker identity

### 3. Smart Chunk Sampling
- Top_k = 10–12 for generative queries
- Instead of purely top cosine matches:
  - Mix of `lecture` and `ceremony`
  - Bias toward gratitude/honor/responsibility tone
  - Optional: include 2–3 wildcards for surprise inspiration

### 4. Example Prompt Registration
- Add `"Draft a job acceptance email in the style of a Nobel Prize winner."` to `prompt_templates.json`
  - Tagged: `["generative", "email", "acceptance", "laureate-style"]`

---

## 🧪 Future Enhancements

- Add tone/theme classifier for chunk re-ranking
- Enable retrieval sampling by decade, region, or emotional tone
- Token-budget-aware prompt formatter (truncate dynamically)
- Integrate prompt logging and evaluation

---

## 🔧 Tasks Breakdown

| Task | Description | File(s) |
|------|-------------|---------|
| T1 | Create `prompt_builder.py` with `build_generative_prompt()` | `rag/prompt_builder.py` |
| T2 | Update `query_router.py` to detect specific generative intents and route accordingly | `rag/query_router.py` |
| T3 | Modify retrieval logic to select chunks by `speech_type`, tone keywords | `rag/query_engine.py` or `retriever.py` |
| T4 | Add tags to chunk metadata during embedding/chunking phase | `embeddings/chunk_text.py` |
| T5 | Add prompt entry: "Draft a job acceptance email…" | `data/prompt_templates.json` |
| T6 | Update documentation and `rag/README.md` to reflect changes | `rag/README.md` |

---

## 📁 Output Files Affected

- `rag/prompt_builder.py` (new)
- `rag/query_router.py`
- `rag/query_engine.py`
- `embeddings/chunk_text.py`
- `data/prompt_templates.json`
- `rag/README.md`

---

## 📌 Example Prompt Usage

> **Prompt:** Draft a job acceptance email in the style of a Nobel Prize winner.  
> **Generated Response:**  
> "It is with great humility and solemn joy that I accept this role. Like those who came before me, I do not regard this moment as a triumph, but as a commitment…"

---

## 🧠 Notes

- This epic builds on architectural principles from `CursorRules.pdf` and `ImplementationPlan.pdf`
- Initial implementation may re-use FAISS chunk metadata fields (`source`, `type`) but can be extended with tone hints
- Prompt templates are expected to grow — future UX may surface these as suggestions

