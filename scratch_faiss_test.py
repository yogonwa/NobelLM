from rag.retriever import load_index_and_metadata, query_index
from sentence_transformers import SentenceTransformer
import numpy as np


def main():
    query = "How many females have won the award?"
    model_id = "bge-large"  # Make sure this matches your config/model
    model = SentenceTransformer("BAAI/bge-large-en-v1.5")
    query_emb = model.encode(query, normalize_embeddings=True)

    # Test index loading directly
    index, metadata = load_index_and_metadata(model_id)
    print(f"Loaded index with {getattr(index, 'ntotal', 'N/A')} vectors and {len(metadata)} metadata entries.")

    # Query using the high-level function
    results = query_index(np.array(query_emb), model_id=model_id, top_k=5)
    print("Results:")
    for r in results:
        print(r)


if __name__ == "__main__":
    main() 