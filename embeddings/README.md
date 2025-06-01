# Embeddings Module

## Chunking and Tagging Nobel Literature Speeches

### Purpose
This module prepares Nobel Literature speech texts for embedding by chunking them into semantically meaningful blocks and tagging each chunk with rich metadata. The chunking script is implemented in `chunk_literature_speeches.py`.

### Input Files
- `data/nobel_literature.json` (laureate metadata)
- `data/nobel_lectures/*.txt` (cleaned lecture texts)
- `data/acceptance_speeches/*.txt` (cleaned acceptance speeches)
- `data/ceremony_speeches/*.txt` (cleaned ceremony speeches)

### Output File
- `data/chunks_literature_labeled_{model}.jsonl` (newline-delimited JSON, one chunk per line, model-specific)

### Chunk Schema
Each chunk is a JSON object with the following fields:
- `chunk_id`: unique identifier for the chunk, formatted as `{year_awarded}_{lastname}_{source_type}_{chunk_index}`
- `source_type`: e.g., nobel_lecture, acceptance_speech, ceremony_speech, prize_motivation, life_blurb, work_blurb
- `category`: always "Literature" for this phase
- `laureate`: full name of the laureate
- `year_awarded`: year of the award
- `chunk_index`: index of the chunk within the source
- `gender`: gender of the laureate
- `country`: country of the laureate
- `specific_work_cited`: boolean
- `prize_motivation`: string
- `text`: the cleaned speech or metadata text for this chunk

*Note: `chunk_id` is useful for traceability, logging, and deduplication. There is no distinction between raw and clean text; input files are already cleaned. The fields `language` and `declined` are not included in the schema.*

### Chunking Logic
- Speech texts are split into paragraphs using double newlines.
- Paragraphs are accumulated into chunks of approximately 300–500 words, avoiding mid-sentence splits.
- If a paragraph is very long, it is split at sentence boundaries.
- If the last chunk is very short, it is merged with the previous chunk if appropriate.
- Short fields (`prize_motivation`, `life_blurb`, `work_blurb`) are treated as single chunks.

### Example Chunk Object
```json
{
  "chunk_id": "2017_ishiguro_nobel_lecture_0",
  "source_type": "nobel_lecture",
  "category": "Literature",
  "laureate": "Kazuo Ishiguro",
  "year_awarded": 2017,
  "chunk_index": 0,
  "gender": "Male",
  "country": "United Kingdom",
  "specific_work_cited": false,
  "prize_motivation": "who, in novels of great emotional force, has uncovered the abyss beneath our illusory sense of connection with the world",
  "text": "My lecture begins with a memory from my childhood..."
}
```

## Model-Aware Embedding Pipeline

All chunking, embedding, and index scripts are now **model-aware and config-driven**. The embedding model, FAISS index, and chunk metadata paths are centrally managed in [`rag/model_config.py`](../rag/model_config.py):

- To switch models (e.g., BGE-Large vs MiniLM), pass `--model` to any CLI tool.
- All file paths, model names, and embedding dimensions are set in one place.
- Consistency checks ensure the loaded model and index match in dimension, preventing silent errors.
- Enables easy A/B testing and reproducibility.

**Example:**
```bash
python -m embeddings.chunk_literature_speeches --model bge-large
python -m embeddings.embed_texts --model bge-large
python -m embeddings.build_index --model bge-large
```

**To add a new model:**
- Add its config to `rag/model_config.py`.
- All downstream code and scripts will pick it up automatically.

---

## Generating Embeddings for Literature Chunks

### Purpose
This step generates dense vector embeddings for each chunked speech or metadata block using a state-of-the-art sentence transformer. These embeddings are used for semantic search, retrieval, and downstream RAG (retrieval-augmented generation) tasks.

### Model
- **Model:** Configurable via `--model` (see `rag/model_config.py` for supported models)
- **Why this model?** MiniLM and BGE-Large offer a balance of speed, memory usage, and semantic accuracy. Both are compatible with FAISS and other vector stores.

### Input File
- `data/chunks_literature_labeled_{model}.jsonl` (one chunk per line, model-specific)

### Output File
- `data/literature_embeddings_{model}.json` (list of JSON objects, one per chunk, with embedding)

### Embedding Schema
Each output object contains all chunk metadata plus an additional `embedding` field:
- All fields from the chunk schema above
- `embedding`: list of floats (the dense vector representation of the chunk's text)

#### Example Output Object
```json
{
  "chunk_id": "2017_ishiguro_nobel_lecture_0",
  "source_type": "nobel_lecture",
  "category": "Literature",
  "laureate": "Kazuo Ishiguro",
  "year_awarded": 2017,
  "chunk_index": 0,
  "gender": "Male",
  "country": "United Kingdom",
  "specific_work_cited": false,
  "prize_motivation": "who, in novels of great emotional force, has uncovered the abyss beneath our illusory sense of connection with the world",
  "text": "My lecture begins with a memory from my childhood...",
  "embedding": [0.021, -0.034, ...]  // model-specific vector
}
```

### How to Reproduce
Run the following commands from the project root (ensure your virtual environment is active):

```sh
python -m embeddings.chunk_literature_speeches --model bge-large
python -m embeddings.embed_texts --model bge-large
python -m embeddings.build_index --model bge-large
```

This will read the chunked JSONL file, generate embeddings for each chunk, and write the output JSON file. Progress and errors are logged to the console. All outputs are model-specific and versioned.

## Building and Querying the FAISS Index

### Purpose
This step builds a FAISS vector index for fast semantic search over Nobel Literature speech embeddings. The index enables efficient retrieval of the most relevant text chunks for a given query embedding, supporting downstream RAG and search tasks.

### Input Files
- `data/literature_embeddings_{model}.json` (output from embedding step; list of dicts with `embedding` and metadata)

### Output Files
- `data/faiss_index_{model}/index.faiss` (FAISS index file, model-specific)
- `data/faiss_index_{model}/chunk_metadata.jsonl` (list of metadata dicts, one per chunk, excluding the embedding vector, model-specific)

### How to Build the Index
Run the following command from the project root (ensure your virtual environment is active):

```sh
python -m embeddings.build_index --model bge-large
```

This will:
- Load all embeddings from `data/literature_embeddings_{model}.json`
- Normalize vectors for cosine similarity
- Build a FAISS index (`IndexFlatIP`)
- Save the index and metadata mapping to `data/faiss_index_{model}/`
- Log progress and errors to the console

### API: Index Build and Query Functions

#### `build_index`
```python
def build_index(
    embeddings_path: str = "data/literature_embeddings.json",
    index_dir: str = "data/faiss_index/"
) -> None:
    """
    Build a FAISS cosine similarity index from embedding vectors and save index + metadata mapping.
    """
```

#### `load_index`
```python
def load_index(
    index_dir: str = "data/faiss_index/"
) -> Tuple[faiss.Index, List[Dict[str, Any]]]:
    """
    Load the FAISS index and metadata mapping from disk.
    Returns:
        index: FAISS index object
        metadata: List of chunk metadata dicts (excluding embeddings)
    """
```

#### `query_index`
```python
def query_index(
    index: faiss.Index,
    metadata: List[Dict[str, Any]],
    query_embedding: np.ndarray,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Query the FAISS index and return top_k most similar chunks with metadata.
    Args:
        index: FAISS index object
        metadata: List of chunk metadata dicts
        query_embedding: 1D numpy array (should be normalized)
        top_k: Number of results to return
    Returns:
        List of metadata dicts for top_k results, each with a 'score' field
    """
```

### Example Usage
```python
import numpy as np
from embeddings.build_index import load_index, query_index

# Load the index and metadata
index, metadata = load_index()

# Prepare a query embedding (must be a 1D np.ndarray, normalized)
query_embedding = np.random.rand(index.d)

# Query the index for top 3 most similar chunks
results = query_index(index, metadata, query_embedding, top_k=3)
for r in results:
    print(r["chunk_id"], r["score"], r["text"][:100])
```

### Notes
- All vectors are normalized to unit length for cosine similarity.
- The index and metadata mapping must be kept in sync; do not modify one without the other.
- For production or multi-user scenarios, consider file locks or atomic writes.
- All logging is handled via the `logging` module.

## FAISS Index Build & Test – Task Complete

The FAISS index build and test harness are now robust to macOS threading issues. The script sets OMP_NUM_THREADS=1 at startup to prevent segmentation faults when using FAISS and PyTorch together. If you encounter segfaults, this is handled automatically, but you can also set this variable manually:

```sh
export OMP_NUM_THREADS=1
```

This is only needed on macOS. On Linux, no action is required. 