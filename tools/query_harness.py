import sys
import os
from pathlib import Path
import argparse

# Ensure project root is in sys.path for relative imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rag.query_engine import query
from rag.faiss_index import reload_index, health_check

def parse_args():
    parser = argparse.ArgumentParser(description="NobelLM CLI Query Harness")
    parser.add_argument("--dry_run", action="store_true", default=False, help="Run in dry mode (no LLM call)")
    parser.add_argument("--prompt_dump", action="store_true", help="Print the constructed prompt (dry_run only)")
    return parser.parse_args()

def main():
    # Force reload of FAISS index for CLI/test safety
    reload_index()
    print("[FAISS] Index reloaded for CLI run.")
    try:
        health_check()
    except Exception as e:
        print(f"[FAISS] Health check failed: {e}")
    args = parse_args()
    print("\nNobelLM CLI Query Harness\n-------------------------")
    user_query = input("Enter your NobelLM query: ").strip()
    if not user_query:
        print("No query entered. Exiting.")
        return

    print("\n[1/4] Classifying intent...")
    # Classify intent using the router
    from rag.query_engine import get_query_router
    router = get_query_router()
    route_result = router.route_query(user_query)
    intent = route_result.intent
    print(f"[{intent}]")

    print("[2/4] Retrieving relevant chunks and metadata...")
    # If thematic, show expanded keywords
    if intent == "thematic":
        # Try to get expanded terms from route_result.logs if present
        expanded_terms = route_result.logs.get('thematic_expanded_terms')
        if expanded_terms:
            print(f"[ThemeReformulator] Expanded keywords: {sorted(expanded_terms)}")
        else:
            print("[ThemeReformulator] No expanded keywords found.")

    # Run the query pipeline (default: dry_run=True for safety)
    response = query(user_query, dry_run=args.dry_run)

    print("[3/4] Building prompt and compiling answer...")
    # Build the prompt but exclude full chunk text
    try:
        from rag.query_engine import build_prompt
        # Reconstruct minimal chunks for prompt preview (exclude full text)
        minimal_chunks = []
        for src in response.get("sources", []):
            minimal_chunk = src.copy()
            # Remove or mask text fields
            minimal_chunk["text"] = "[CHUNK TEXT OMITTED]"
            if "text_snippet" in minimal_chunk:
                minimal_chunk["text_snippet"] = "[SNIPPET OMITTED]"
            minimal_chunks.append(minimal_chunk)
        prompt = build_prompt(minimal_chunks, user_query)
        print("[Prompt Preview, chunk text omitted]:\n----------------")
        print(prompt)
    except Exception as e:
        print(f"[Prompt preview failed: {e}")

    print("[4/4] (Optional) Calling LLM (if not dry_run)...\n")

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