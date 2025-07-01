import weaviate
import faiss
import json
import numpy as np
from uuid import uuid4

# Paths
INDEX_PATH = "data/faiss_index_bge-large/index.faiss"
METADATA_PATH = "data/faiss_index_bge-large/chunk_metadata.jsonl"

# Connect to Weaviate (v3 client)
client = weaviate.Client(
    url="https://a0dq8xtrtkw6lovkllxw.c0.us-east1.gcp.weaviate.cloud",
    auth_client_secret=weaviate.AuthApiKey("dFovQ01lNVRoUjdEOCtrRV9EQVlKd29GK1ZnWmNiclpFbmxSK2gxTjBrODBSMEZWVVQwMFBtSFhNYUVBPV92MjAw")  # ← Replace
)

# Load FAISS index and metadata
index = faiss.read_index(INDEX_PATH)

with open(METADATA_PATH, "r", encoding="utf-8") as f:
    metadata = [json.loads(line) for line in f]

vectors = index.reconstruct_n(0, index.ntotal)

# Upload to Weaviate
for i, meta in enumerate(metadata):
    vector = vectors[i].tolist()

    client.data_object.create(
        data_object=meta,
        class_name="SpeechChunk",
        vector=vector
    )


print(f"✅ Uploaded {len(metadata)} chunks to Weaviate.")
