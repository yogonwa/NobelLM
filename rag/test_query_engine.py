"""
Test script for the NobelLM Query Engine.

Demonstrates dry run and real query modes, with and without metadata filters.
"""
import logging
from rag.query_engine import query, build_prompt

def source_to_chunk(source):
    # Use the text_snippet as the 'text' field for prompt reconstruction
    return {**source, "text": source["text_snippet"]}

def main():
    logging.basicConfig(level=logging.INFO)
    print("\n=== NobelLM Query Engine Test ===\n")

    # Example 1: Dry run, no filters
    user_query = "What do laureates say about justice?"
    print("[Dry Run] General query (no filters):")
    response = query(
        user_query,
        dry_run=False
    )
    prompt = build_prompt([source_to_chunk(s) for s in response['sources']], user_query)
    print(f"User Query: {user_query}")
    print(f"Prompt to LLM:\n{prompt}\n")
    print(f"Answer:\n{response['answer']}\n")
    print(f"Filters: None")
    print(f"k Value: 3")
    print(f"Sources (count: {len(response['sources'])}):")
    for src in response['sources']:
        print(f"  - {src}")
    print("\n" + "-"*40 + "\n")

    # Example 2: Dry run, with filters
    user_query = "What do USA winners talk about in their lectures?"
    filters = {"country": "USA", "source_type": "nobel_lecture"}
    print("[Dry Run] Filtered by country and source_type:")
    response = query(
        user_query,
        filters=filters,
        dry_run=True
    )
    prompt = build_prompt([source_to_chunk(s) for s in response['sources']], user_query)
    print(f"User Query: {user_query}")
    print(f"Prompt to LLM:\n{prompt}\n")
    print(f"Answer:\n{response['answer']}\n")
    print(f"Filters: {filters}")
    print(f"k Value: 3")
    print(f"Sources (count: {len(response['sources'])}):")
    for src in response['sources']:
        print(f"  - {src}")
    print("\n" + "-"*40 + "\n")

    Example 3: Real query (requires OpenAI API key)
    Uncomment to run a real OpenAI call
    user_query = "How do laureates describe the role of literature in society?"
    print("[Real Query] General query (no filters):")
    response = query(
        user_query,
        dry_run=False
    )
    prompt = build_prompt([source_to_chunk(s) for s in response['sources']], user_query)
    print(f"User Query: {user_query}")
    print(f"Prompt to LLM:\n{prompt}\n")
    print(f"Answer:\n{response['answer']}\n")
    print(f"Filters: None")
    print(f"k Value: 3")
    print(f"Sources (count: {len(response['sources'])}):")
    for src in response['sources']:
        print(f"  - {src}")
    print("\n" + "-"*40 + "\n")

    # Example 4: Thematic (broad) query to test dynamic top_k
    user_query = "What themes are common across Nobel lectures?"
    filters = {"source_type": "nobel_lecture"}
    print("[Real Query] Thematic query (should trigger top_k=15):")
    response = query(
        user_query,
        filters=filters,
        dry_run=False
    )
    prompt = build_prompt([source_to_chunk(s) for s in response['sources']], user_query)
    print(f"User Query: {user_query}")
    print(f"Prompt to LLM:\n{prompt}\n")
    print(f"Answer:\n{response['answer']}\n")
    print(f"Filters: {filters}")
    print(f"k Value: 15")
    print(f"Sources (count: {len(response['sources'])}):")
    for src in response['sources']:
        print(f"  - {src}")
    print("\n" + "-"*40 + "\n")

if __name__ == "__main__":
    main() 