"""
Migration script: Upload NobelLM chunk embeddings and metadata to Qdrant.

- Source: data/literature_embeddings_bge-large.json
- Target Qdrant collection: nobellm_bge_large
- Vector size: inferred from first record
- Distance: Cosine
- Batch size: 256
- Idempotent and restartable
- Qdrant Cloud credentials are loaded from .env (QDRANT_URL, QDRANT_API_KEY)
- Uses UUIDv5 for point IDs (deterministic, based on chunk_id)
"""
import json
import logging
import os
import uuid
from typing import List, Dict, Any
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Load environment variables from .env
load_dotenv()

DATA_PATH = Path("data/literature_embeddings_bge-large.json")
COLLECTION_NAME = "nobellm_bge_large"
BATCH_SIZE = 256

QDRANT_URL = os.environ.get("QDRANT_URL")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")


def load_embeddings(path: Path) -> List[Dict[str, Any]]:
    """Load all embedding records from the specified JSON file."""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def main() -> None:
    """Main migration logic: upload all points to Qdrant in batches."""
    if not QDRANT_URL or not QDRANT_API_KEY:
        logging.error("QDRANT_URL and QDRANT_API_KEY must be set in the environment or .env file.")
        return

    logging.info(f"Loading embeddings from {DATA_PATH} ...")
    records = load_embeddings(DATA_PATH)
    if not records:
        logging.error("No records found in the embeddings file.")
        return

    vector_size = len(records[0]["embedding"])
    logging.info(f"Loaded {len(records)} records. Vector size: {vector_size}")

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # Recreate collection (idempotent)
    logging.info(f"Recreating Qdrant collection '{COLLECTION_NAME}' ...")
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )

    # Prepare and upload in batches
    total = len(records)
    for i in range(0, total, BATCH_SIZE):
        batch = records[i:i+BATCH_SIZE]
        points = []
        for rec in batch:
            chunk_id = rec["chunk_id"]
            # Use UUIDv5 for deterministic, reproducible point IDs
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))
            vector = rec["embedding"]
            payload = {k: v for k, v in rec.items() if k != "embedding"}
            payload["chunk_id"] = chunk_id  # Ensure chunk_id is in payload
            points.append(PointStruct(id=point_id, vector=vector, payload=payload))
        try:
            client.upsert(
                collection_name=COLLECTION_NAME,
                wait=True,
                points=points,
            )
            logging.info(f"Uploaded batch {i} - {min(i+BATCH_SIZE, total)} / {total}")
        except Exception as e:
            logging.error(f"Error uploading batch {i} - {min(i+BATCH_SIZE, total)}: {e}")
            continue
    logging.info("Migration complete.")


if __name__ == "__main__":
    main() 