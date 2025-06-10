import sys
import os
from pathlib import Path
import argparse
import logging
import json
from typing import Dict, Any

# Ensure project root is in sys.path for relative imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rag.query_engine import answer_query, get_query_router, build_prompt
from rag.utils import format_chunks_for_prompt
from rag.faiss_index import health_check

def parse_args():
    parser = argparse.ArgumentParser(description="NobelLM CLI Query Harness")
    return parser.parse_args()

def main():
    print("[FAISS] Running health check...")
    try:
        health_check()
    except Exception as e:
        print(f"[FAISS] Health check failed: {e}")
    else:
        print("[FAISS] Health check passed.")

    print(f"[Config] Subprocess mode: {'ENABLED' if os.getenv('NOBELLM_USE_FAISS_SUBPROCESS') == '1' else 'DISABLED'}")

    args = parse_args()
    print("\nNobelLM CLI Query Harness\n-------------------------")
    user_query = input("Enter your NobelLM query: ").strip()
    if not user_query:
        print("No query entered. Exiting.")
        return

    print("\n[1/4] Classifying intent...")
    # Classify intent using the router
    router = get_query_router()
    route_result = router.route_query(user_query)
    intent = route_result.intent
    print(f"[{intent}]")

    print("[2/4] Retrieving relevant chunks and metadata...")
    # If thematic, show expanded keywords
    expanded_terms = route_result.logs.get('thematic_expanded_terms') if route_result.logs else None
    if intent == "thematic":
        if expanded_terms:
            print(f"[ThemeReformulator] Expanded keywords: {sorted(expanded_terms)}")
        else:
            print("[ThemeReformulator] No expanded keywords found.")

    # Run the query pipeline (always runs full pipeline now)
    response = answer_query(user_query)

    print("[3/4] Building prompt and compiling answer...")
    try:
        # Reconstruct minimal chunks for prompt preview (exclude full text)
        minimal_chunks = []
        for src in response.get("sources", []):
            minimal_chunk = src.copy()
            minimal_chunk["text"] = "[CHUNK TEXT OMITTED]"
            if "text_snippet" in minimal_chunk:
                minimal_chunk["text_snippet"] = "[SNIPPET OMITTED]"
            minimal_chunks.append(minimal_chunk)

        # Format context properly
        context = format_chunks_for_prompt(minimal_chunks)
        prompt = build_prompt(user_query, context)

        print("[Prompt Preview, chunk text omitted]:\n----------------")
        print(prompt)
    except Exception as e:
        print(f"[Prompt preview failed: {e}]")

    print("[4/4] Calling LLM...\n")

    print("=== NobelLM Answer ===\n")
    print(f"\033[1mQuery:\033[0m {user_query}\n")
    print(f"\033[1mAnswer Type:\033[0m {response.get('answer_type', 'N/A')}")
    print(f"\033[1mAnswer:\033[0m\n{response.get('answer', '[No answer returned]')}\n")
    print("Sources:")
    for i, src in enumerate(response.get('sources', []), 1):
        snippet = src.get('text_snippet', '')
        year = src.get('year', src.get('year_awarded', ''))
        laureate = src.get('laureate', src.get('full_name', ''))
        print(f"  {i}. {snippet[:80]}... (Year: {year}, Laureate: {laureate})")
    if not response.get('sources'):
        print("  [No sources returned]")
    print("\n---\n")

    print("Done.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
