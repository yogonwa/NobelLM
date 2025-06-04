import argparse
import logging
from rag.model_config import get_model_config
from sentence_transformers import SentenceTransformer
from rag.dual_process_retriever import retrieve_chunks_dual_process

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retrieve_top_chunks(query: str, k: int = 10, score_threshold: float = 0.25, model_id="bge-large"):
    # 1. Load embedding model
    config = get_model_config(model_id)
    model = SentenceTransformer(config["model_name"])
    
    # 2. Embed the user query
    query_embedding = model.encode([query], normalize_embeddings=True)[0]  # shape: (dim,)
    logger.info(f"Query embedding shape: {query_embedding.shape}, dtype: {query_embedding.dtype}")
    
    # 3. Use dual-process retrieval for FAISS (safe on Mac/Intel)
    # retrieve_chunks_dual_process expects the query string, not the embedding
    results = retrieve_chunks_dual_process(query, model_id=model_id, top_k=k, filters=None)
    # 4. Filter by score_threshold
    filtered = [r for r in results if score_threshold is None or r.get("score", 0) >= score_threshold]
    logger.info(f"Returned {len(filtered)} chunks above threshold {score_threshold}.")
    logger.info(f"Score distribution: {[r.get('score', 0) for r in results]}")
    if not filtered:
        logger.warning("No chunks returned above threshold.")
    return filtered

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
        results = retrieve_top_chunks(term, k=args.k, score_threshold=args.score_threshold, model_id=args.model_id)
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