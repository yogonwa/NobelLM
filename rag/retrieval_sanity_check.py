import argparse
import logging
from rag.model_config import get_model_config
from sentence_transformers import SentenceTransformer
from rag.dual_process_retriever import retrieve_chunks_dual_process
from typing import List, Dict, Any
from .retriever import query_index
from .utils import filter_top_chunks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retrieve_top_chunks(
    query: str,
    top_k: int = 5,
    filters: Dict[str, Any] = None,
    score_threshold: float = 0.2,
    min_return: int = 3,
    max_return: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve and filter top chunks for a query, using the same filtering logic
    as the main query pipeline. This ensures consistent behavior between
    sanity checks and real queries.

    Args:
        query: The query string
        top_k: Number of chunks to retrieve (default: 5)
        filters: Optional metadata filters
        score_threshold: Minimum similarity score (default: 0.2)
        min_return: Minimum number of chunks to return (default: 3)
        max_return: Maximum number of chunks to return (default: 5)

    Returns:
        List of filtered chunks, sorted by score
    """
    # Retrieve chunks using query_index
    chunks = query_index(query, top_k=top_k, filters=filters)
    
    # Apply consistent filtering using filter_top_chunks
    filtered_chunks = filter_top_chunks(
        chunks,
        score_threshold=score_threshold,
        min_return=min_return,
        max_return=max_return
    )
    
    # Log chunk details for debugging
    for i, chunk in enumerate(filtered_chunks):
        logger.info(
            f"[SanityCheck] Chunk {i+1}/{len(filtered_chunks)} — "
            f"Score: {chunk['score']:.3f}, "
            f"Source: {chunk.get('source_type', 'unknown')}, "
            f"Laureate: {chunk.get('laureate', 'unknown')}, "
            f"Year: {chunk.get('year_awarded', 'unknown')}"
        )
    
    return filtered_chunks

def main():
    parser = argparse.ArgumentParser(description="FAISS Retrieval Sanity Check (Subprocess Mode)")
    parser.add_argument("--query", type=str, required=True, help="User query to embed and search")
    parser.add_argument("--k", type=int, default=10, help="Top-k results to return per term")
    parser.add_argument("--score_threshold", type=float, default=0.25, help="Score threshold for filtering")
    parser.add_argument("--model_id", type=str, default="bge-large", help="Model ID to use")
    parser.add_argument("--expanded_terms", type=str, default=None, help="Comma-separated list of expanded thematic keywords (optional)")
    args = parser.parse_args()

    if args.expanded_terms:
        terms = [t.strip() for t in args.expanded_terms.split(",") if t.strip()]
        print(f"Using expanded terms: {terms}")
    else:
        # Hardcoded for the test case: 'what patterns emerge in how laureates discuss science in society?'
        terms = ['curiosity', 'discovery', 'knowledge', 'research', 'science']
        print(f"No --expanded_terms provided. Using hardcoded thematic terms: {terms}")

    all_results = []
    for term in terms:
        print(f"\nRetrieving for term: '{term}'")
        results = retrieve_top_chunks(term, k=args.k, score_threshold=args.score_threshold)
        print(f"  {len(results)} chunks returned for '{term}'")
        all_results.extend(results)

    # Deduplicate by chunk_id
    unique_chunks = {}
    for r in all_results:
        cid = r.get('chunk_id')
        if cid and (cid not in unique_chunks or r['score'] > unique_chunks[cid]['score']):
            unique_chunks[cid] = r
    print(f"\nTotal unique chunks across all terms: {len(unique_chunks)}\n")
    for r in unique_chunks.values():
        print(f"[{r['score']:.3f}] {r.get('chunk_id', '?')}: {r.get('text_snippet', '')[:80]}...")
    print(f"\nTotal returned: {len(unique_chunks)}\n")

if __name__ == "__main__":
    main() 