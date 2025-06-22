# Theme Embeddings Infrastructure

## Overview

The Theme Embeddings Infrastructure provides pre-computed embeddings for all theme keywords defined in `config/themes.json`. This enables efficient similarity-based query expansion in the NobelLM RAG pipeline.

## Architecture

### Components

1. **`config/theme_embeddings.py`** - Core class for managing theme embeddings
2. **`config/theme_similarity.py`** - Similarity computation using existing FAISS patterns
3. **`scripts/precompute_theme_embeddings.py`** - Script to pre-compute embeddings for all models
4. **`data/theme_embeddings/`** - Directory storing pre-computed embeddings

### File Structure

```
data/
├── theme_embeddings/
│   ├── theme_embeddings_bge-large.npz    # 1024-dimensional embeddings
│   └── theme_embeddings_miniLM.npz       # 384-dimensional embeddings
config/
├── themes.json                           # Theme keyword definitions
├── theme_embeddings.py                   # Embedding management class
└── theme_similarity.py                   # Similarity computation
scripts/
└── precompute_theme_embeddings.py        # Pre-computation script
```

## Setup and Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Pre-compute Theme Embeddings

**First-time setup:**
```bash
python scripts/precompute_theme_embeddings.py
```

This will:
- Create `data/theme_embeddings/` directory
- Compute embeddings for all theme keywords using both models
- Save embeddings as compressed `.npz` files
- Validate embedding quality and dimensions

**Expected output:**
```
2025-01-XX 10:30:00 - __main__ - INFO - Starting theme embedding pre-computation...
2025-01-XX 10:30:00 - __main__ - INFO - Found 2 supported models: ['bge-large', 'miniLM']
2025-01-XX 10:30:00 - __main__ - INFO - Processing model: bge-large
2025-01-XX 10:30:05 - __main__ - INFO - Model bge-large stats: {'model_id': 'bge-large', 'embedding_dim': 1024, 'total_keywords': 156, ...}
2025-01-XX 10:30:05 - __main__ - INFO - Embeddings saved to data/theme_embeddings/theme_embeddings_bge-large.npz (0.85 MB)
2025-01-XX 10:30:05 - __main__ - INFO - Processing model: miniLM
2025-01-XX 10:30:08 - __main__ - INFO - Model miniLM stats: {'model_id': 'miniLM', 'embedding_dim': 384, 'total_keywords': 156, ...}
2025-01-XX 10:30:08 - __main__ - INFO - Embeddings saved to data/theme_embeddings/theme_embeddings_miniLM.npz (0.32 MB)
2025-01-XX 10:30:08 - __main__ - INFO - Theme embedding pre-computation completed!
```

### 3. Verify Setup

```python
from config.theme_embeddings import ThemeEmbeddings

# Test bge-large embeddings
embeddings_large = ThemeEmbeddings("bge-large")
stats = embeddings_large.get_embedding_stats()
print(f"bge-large stats: {stats}")

# Test miniLM embeddings  
embeddings_mini = ThemeEmbeddings("miniLM")
stats = embeddings_mini.get_embedding_stats()
print(f"miniLM stats: {stats}")
```

## Usage

### Basic Usage

```python
from config.theme_embeddings import ThemeEmbeddings
from config.theme_similarity import compute_theme_similarities

# Initialize theme embeddings
theme_embeddings = ThemeEmbeddings("bge-large")

# Get embedding for specific keyword
justice_embedding = theme_embeddings.get_theme_embedding("justice")

# Compute similarities for a query
from rag.cache import get_model
model = get_model("bge-large")
query = "What do laureates say about fairness?"
query_embedding = model.encode([query], normalize_embeddings=True)[0]

similarities = compute_theme_similarities(
    query_embedding=query_embedding,
    model_id="bge-large",
    similarity_threshold=0.3
)

print(f"Similar keywords: {list(similarities.keys())}")
```

### Advanced Usage

```python
# Get ranked theme keywords
from config.theme_similarity import get_ranked_theme_keywords

ranked_keywords = get_ranked_theme_keywords(
    query_embedding=query_embedding,
    model_id="bge-large",
    similarity_threshold=0.3,
    max_results=10
)

for keyword, score in ranked_keywords:
    print(f"{keyword}: {score:.3f}")

# Force recomputation (e.g., after updating themes.json)
theme_embeddings.force_recompute_embeddings()
```

## Production Deployment

### 1. Pre-computation in CI/CD

Add to your deployment pipeline:

```yaml
# .github/workflows/deploy.yml
- name: Pre-compute theme embeddings
  run: |
    python scripts/precompute_theme_embeddings.py
  env:
    PYTHONPATH: ${{ github.workspace }}
```

### 2. File Permissions

Ensure the application has write permissions to `data/theme_embeddings/`:

```bash
# Set appropriate permissions
chmod 755 data/theme_embeddings/
chmod 644 data/theme_embeddings/*.npz
```

### 3. Environment Variables

No additional environment variables required. The system uses existing model configuration.

### 4. Health Checks

Add health checks to your application:

```python
def check_theme_embeddings_health():
    """Health check for theme embeddings."""
    try:
        for model_id in ["bge-large", "miniLM"]:
            embeddings = ThemeEmbeddings(model_id)
            stats = embeddings.get_embedding_stats()
            
            # Check for reasonable stats
            if stats["total_keywords"] < 100:
                return False, f"Too few keywords for {model_id}: {stats['total_keywords']}"
            
            if not (0.9 <= stats["mean_norm"] <= 1.1):
                return False, f"Abnormal embedding norms for {model_id}: {stats['mean_norm']}"
        
        return True, "Theme embeddings healthy"
        
    except Exception as e:
        return False, f"Theme embeddings health check failed: {e}"
```

### 5. Monitoring

Monitor embedding file sizes and access patterns:

```python
import os
from pathlib import Path

def monitor_theme_embeddings():
    """Monitor theme embedding files."""
    embeddings_dir = Path("data/theme_embeddings")
    
    for model_id in ["bge-large", "miniLM"]:
        file_path = embeddings_dir / f"theme_embeddings_{model_id}.npz"
        
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"{model_id}: {size_mb:.2f} MB")
        else:
            print(f"WARNING: Missing embeddings for {model_id}")
```

## File Formats

### .npz Files

Theme embeddings are stored in NumPy's compressed format:

- **Structure**: `{'keywords': np.array, 'embeddings': np.array}`
- **Compression**: Automatic compression for efficient storage
- **Compatibility**: Works with NumPy 1.23.5+ (as specified in requirements.txt)

### File Sizes

Expected file sizes:
- `theme_embeddings_bge-large.npz`: ~0.8-1.0 MB
- `theme_embeddings_miniLM.npz`: ~0.3-0.4 MB

## Troubleshooting

### Common Issues

1. **Missing embeddings file**
   ```
   FileNotFoundError: Theme embeddings file not found
   ```
   **Solution**: Run `python scripts/precompute_theme_embeddings.py`

2. **Dimension mismatch**
   ```
   ValueError: Embedding dimension mismatch
   ```
   **Solution**: Force recomputation with `force_recompute_embeddings()`

3. **Memory issues**
   ```
   MemoryError: Unable to load embeddings
   ```
   **Solution**: Check available RAM, embeddings are loaded into memory

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Then use ThemeEmbeddings normally
embeddings = ThemeEmbeddings("bge-large")
```

### Performance Optimization

- **Caching**: Embeddings are cached in memory after first load
- **Batch processing**: Similarity computation uses efficient batch operations
- **Compression**: Files are compressed to reduce disk usage

## Integration with RAG Pipeline

The theme embeddings integrate seamlessly with the existing RAG pipeline:

1. **Phase 3A**: Theme embedding infrastructure (✅ Complete)
2. **Phase 3B**: Enhanced ThemeReformulator with ranked expansion
3. **Phase 3C**: ThematicRetriever updates with weighted retrieval

### Example Integration

```python
# Enhanced ThemeReformulator will use this internally
from config.theme_embeddings import ThemeEmbeddings
from config.theme_similarity import compute_theme_similarities

# ThematicRetriever will use weighted retrieval
# (Implementation in Phase 3B)
```

## Maintenance

### Updating Theme Keywords

When `config/themes.json` is updated:

1. **Automatic detection**: System will detect changes on next initialization
2. **Manual recomputation**: Use `force_recompute_embeddings()` for immediate update
3. **Validation**: Health checks ensure embedding quality

### Backup Strategy

Include theme embeddings in your backup strategy:

```bash
# Backup theme embeddings
tar -czf theme_embeddings_backup.tar.gz data/theme_embeddings/

# Restore theme embeddings
tar -xzf theme_embeddings_backup.tar.gz
```

## Security Considerations

- **File permissions**: Ensure appropriate read/write permissions
- **Model access**: Uses existing model cache, no additional security concerns
- **Data validation**: Built-in validation prevents corrupted embeddings

## Performance Benchmarks

### Initialization Time
- **First run** (compute + save): ~30-60 seconds per model
- **Subsequent runs** (load from disk): ~100-200ms per model

### Memory Usage
- **bge-large embeddings**: ~1.6 MB in memory
- **miniLM embeddings**: ~0.6 MB in memory

### Similarity Computation
- **Per query**: ~10-50ms depending on number of keywords
- **Batch processing**: Efficient for multiple queries

---

**Last Updated**: 2025-01-XX  
**Version**: 1.0  
**Author**: NobelLM Team 