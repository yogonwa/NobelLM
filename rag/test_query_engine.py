"""
Test script for the NobelLM Query Engine.

Demonstrates dry run and real query modes, with and without metadata filters.
"""
import logging
from rag.query_engine import query

def main():
    logging.basicConfig(level=logging.INFO)
    print("\n=== NobelLM Query Engine Test ===\n")

    # Example 1: Dry run, no filters
    print("[Dry Run] General query (no filters):")
    response = query(
        "What do laureates say about justice?",
        dry_run=True
    )
    print(f"Answer:\n{response['answer']}\nSources:")
    for src in response['sources']:
        print(f"  - {src}")
    print("\n" + "-"*40 + "\n")

    # Example 2: Dry run, with filters
    print("[Dry Run] Filtered by country and source_type:")
    # Use 'USA' for American laureates; use 'United Kingdom' for English/British laureates
    response = query(
        "What do USA winners talk about in their lectures?",
        filters={"country": "USA", "source_type": "nobel_lecture"},
        dry_run=True
    )
    print(f"Answer:\n{response['answer']}\nSources:")
    for src in response['sources']:
        print(f"  - {src}")
    print("\n" + "-"*40 + "\n")

    # Example 3: Real query (requires OpenAI API key)
    # Uncomment to run a real OpenAI call
    print("[Real Query] General query (no filters):")
    response = query(
        "How do laureates describe the role of literature in society?",
        dry_run=False
    )
    print(f"Answer:\n{response['answer']}\nSources:")
    for src in response['sources']:
        print(f"  - {src}")
    print("\n" + "-"*40 + "\n")

if __name__ == "__main__":
    main() 