# 📦 Mini Implementation Plan: Subprocess-Based RAG Retrieval

### 🧠 Problem:
On macOS with Intel CPUs, **PyTorch and FAISS conflict when loaded in the same process**, causing segmentation faults. This happens when using `bge-large` for embedding alongside FAISS indexing.

---

## ✅ Solution Strategy

**Split query embedding and FAISS retrieval into two separate Python processes:**

1. **Main Driver (query_driver.py)**  
   - Accepts a user query string
   - Embeds it using SentenceTransformer (`bge-large`)
   - Saves embedding to `query_embedding.npy`
   - Launches subprocess: `python faiss_query_worker.py`
   - Reads back results from `retrieval_results.json`

2. **FAISS Worker (faiss_query_worker.py)**  
   - Loads `query_embedding.npy`
   - Calls `query_index()` from `retriever.py` using `bge-large`
   - Outputs results to `retrieval_results.json`

---

## 📁 Files to Create

### 1. `query_driver.py`
\`\`\`python
import numpy as np
import json
import subprocess
from sentence_transformers import SentenceTransformer
from model_config import get_model_config

user_query = "What do laureates say about the creative process?"

# Step 1: Embed query
model_id = "bge-large"
config = get_model_config(model_id)
model = SentenceTransformer(config["model_name"])
embedding = model.encode(user_query, normalize_embeddings=True)

# Step 2: Save query embedding
np.save("query_embedding.npy", embedding)

# Step 3: Run FAISS worker
subprocess.run(["python", "faiss_query_worker.py", "--model", model_id])

# Step 4: Load results
with open("retrieval_results.json", "r", encoding="utf-8") as f:
    results = json.load(f)

print("Retrieved Chunks:")
for r in results:
    print(f"Score: {r.get('score', 0):.2f} — {r.get('laureate', 'Unknown')} ({r.get('year_awarded', '?')})")
    print(f"  {r.get('text', '')[:200]}...")
\`\`\`

---

### 2. `faiss_query_worker.py`
\`\`\`python
import numpy as np
import json
import argparse
from retriever import query_index

def main(model_id: str):
    query_vector = np.load("query_embedding.npy")
    results = query_index(query_vector, model_id=model_id, top_k=5)
    with open("retrieval_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="bge-large")
    args = parser.parse_args()
    main(args.model)
\`\`\`

---

## 🧪 Test Instructions

\`\`\`bash
python query_driver.py
\`\`\`

Expected:
- `query_embedding.npy` is created
- `faiss_query_worker.py` runs in isolation (no PyTorch involved)
- `retrieval_results.json` contains top-k results with metadata

---

## 📁 Summary of Files

| File                     | Purpose                              |
|--------------------------|---------------------------------------|
| `query_driver.py`        | Embeds query, runs FAISS subprocess   |
| `faiss_query_worker.py`  | Isolated FAISS-based retriever        |
| `query_embedding.npy`    | Query vector (inter-process shared)   |
| `retrieval_results.json` | Retrieved chunks with metadata        |

---

## ✅ Deliverables for Cursor

- Create both scripts as above
- Test the full flow with a sample query
- Ensure compatibility with `bge-large` model and current FAISS index
- Log output paths and retrieval results clearly


---
# 🌐 Environment-Aware Execution Strategy

To support seamless development on macOS (Intel) and production deployment on Hugging Face Spaces or cloud servers, maintain both subprocess and single-process FAISS query modes.

## 🔁 Toggle Between Modes Using Environment Variable

Define a global toggle in `query_engine.py`:

```python
import os

USE_FAISS_SUBPROCESS = os.getenv("NOBELLM_USE_FAISS_SUBPROCESS", "0") == "1"
```

### In Dev (MacOS Intel):
```bash
export NOBELLM_USE_FAISS_SUBPROCESS=1
python query_engine.py
```

Uses subprocess flow to avoid PyTorch/FAISS conflicts.

### In Production (Hugging Face, Docker, EC2):
```bash
unset NOBELLM_USE_FAISS_SUBPROCESS
python query_engine.py
```

Uses fast, unified in-process pipeline.

## 🔧 Implementation Recommendation

Inside `query_engine.py`:

```python
if USE_FAISS_SUBPROCESS:
    from subprocess_faiss import query_faiss_via_subprocess
    results = query_faiss_via_subprocess(query_embedding, model_id)
else:
    from retriever import query_index
    results = query_index(query_embedding, model_id=model_id)
```

This toggle gives you flexibility, safety, and clarity across environments.

---

## ✅ Summary

| Environment       | Execution Mode         | Why                                  |
|-------------------|------------------------|---------------------------------------|
| macOS Intel (dev) | Subprocess (isolated)  | Prevent FAISS/PyTorch segfaults      |
| Hugging Face      | Unified process        | Fast, stable Linux container runtime |
| Cloud (EC2, GPU)  | Unified process        | Standard production path             |

Maintain both modes for developer ergonomics and production reliability.
