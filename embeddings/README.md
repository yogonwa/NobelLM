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
- `data/chunks_literature_labeled.jsonl` (newline-delimited JSON, one chunk per line)

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