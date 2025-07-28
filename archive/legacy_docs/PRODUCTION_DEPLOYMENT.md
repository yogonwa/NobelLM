# Production Deployment Checklist - Theme Embeddings

## Pre-Deployment Checklist

### ✅ Dependencies
- [ ] `sentence-transformers==2.2.2` installed
- [ ] `numpy==1.23.5` installed (compatible version)
- [ ] All other requirements from `requirements.txt` installed

### ✅ File Structure
- [ ] `data/theme_embeddings/` directory exists and is writable
- [ ] `config/themes.json` is present and valid
- [ ] `config/theme_embeddings.py` and `config/theme_similarity.py` are deployed

### ✅ Pre-computation
- [ ] Theme embeddings pre-computed for all models:
  ```bash
  python scripts/precompute_theme_embeddings.py
  ```
- [ ] Verify files created:
  - `data/theme_embeddings/theme_embeddings_bge-large.npz`
  - `data/theme_embeddings/theme_embeddings_miniLM.npz`

### ✅ File Permissions
- [ ] Directory permissions: `chmod 755 data/theme_embeddings/`
- [ ] File permissions: `chmod 644 data/theme_embeddings/*.npz`
- [ ] Application user has read/write access

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy NobelLM with Theme Embeddings

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Pre-compute theme embeddings
        run: |
          python scripts/precompute_theme_embeddings.py
        env:
          PYTHONPATH: ${{ github.workspace }}
      
      - name: Verify theme embeddings
        run: |
          python -c "
          from config.theme_embeddings import ThemeEmbeddings
          for model in ['bge-large', 'miniLM']:
              embeddings = ThemeEmbeddings(model)
              stats = embeddings.get_embedding_stats()
              print(f'{model}: {stats[\"total_keywords\"]} keywords')
          "
      
      - name: Deploy to production
        run: |
          # Your deployment commands here
          # Ensure data/theme_embeddings/ is included in deployment
```

### Docker Integration
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Pre-compute theme embeddings during build
RUN python scripts/precompute_theme_embeddings.py

# Create data directory and set permissions
RUN mkdir -p data/theme_embeddings && \
    chmod 755 data/theme_embeddings && \
    chmod 644 data/theme_embeddings/*.npz

# Expose port and run application
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

## Environment-Specific Setup

### Local Development
```bash
# One-time setup
pip install -r requirements.txt
python scripts/precompute_theme_embeddings.py

# Verify setup
python -c "
from config.theme_embeddings import ThemeEmbeddings
embeddings = ThemeEmbeddings('bge-large')
print('Setup complete!')
"
```

### Production Server
```bash
# Install dependencies
pip install -r requirements.txt

# Pre-compute embeddings (may take 1-2 minutes)
python scripts/precompute_theme_embeddings.py

# Set proper permissions
chmod 755 data/theme_embeddings/
chmod 644 data/theme_embeddings/*.npz

# Verify deployment
python -c "
from config.theme_embeddings import ThemeEmbeddings
for model in ['bge-large', 'miniLM']:
    embeddings = ThemeEmbeddings(model)
    stats = embeddings.get_embedding_stats()
    print(f'{model}: {stats[\"total_keywords\"]} keywords, {stats[\"mean_norm\"]:.3f} mean norm')
"
```

### Cloud Deployment (AWS, GCP, Azure)
```bash
# Ensure data directory is persistent
mkdir -p /var/lib/nobellm/data/theme_embeddings

# Pre-compute embeddings
python scripts/precompute_theme_embeddings.py

# Set proper ownership and permissions
chown -R appuser:appuser /var/lib/nobellm/data/
chmod 755 /var/lib/nobellm/data/theme_embeddings/
chmod 644 /var/lib/nobellm/data/theme_embeddings/*.npz
```

## Health Checks

### Application Health Check
```python
def check_theme_embeddings_health():
    """Health check for theme embeddings infrastructure."""
    try:
        results = {}
        
        for model_id in ["bge-large", "miniLM"]:
            embeddings = ThemeEmbeddings(model_id)
            stats = embeddings.get_embedding_stats()
            
            # Validate stats
            if stats["total_keywords"] < 100:
                return False, f"Too few keywords for {model_id}: {stats['total_keywords']}"
            
            if not (0.9 <= stats["mean_norm"] <= 1.1):
                return False, f"Abnormal embedding norms for {model_id}: {stats['mean_norm']}"
            
            if stats["zero_embeddings"] > 0:
                return False, f"Zero embeddings detected for {model_id}: {stats['zero_embeddings']}"
            
            results[model_id] = stats
        
        return True, f"Theme embeddings healthy: {results}"
        
    except Exception as e:
        return False, f"Theme embeddings health check failed: {e}"
```

### File System Health Check
```python
import os
from pathlib import Path

def check_theme_embedding_files():
    """Check that theme embedding files exist and are accessible."""
    embeddings_dir = Path("data/theme_embeddings")
    
    if not embeddings_dir.exists():
        return False, "Theme embeddings directory not found"
    
    for model_id in ["bge-large", "miniLM"]:
        file_path = embeddings_dir / f"theme_embeddings_{model_id}.npz"
        
        if not file_path.exists():
            return False, f"Missing embeddings file for {model_id}"
        
        if not os.access(file_path, os.R_OK):
            return False, f"Cannot read embeddings file for {model_id}"
        
        # Check file size (should be reasonable)
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb < 0.1:  # Less than 100KB is suspicious
            return False, f"Embeddings file too small for {model_id}: {size_mb:.2f} MB"
    
    return True, "Theme embedding files healthy"
```

## Monitoring and Alerting

### Key Metrics to Monitor
- **File existence**: Theme embedding files present
- **File size**: Reasonable file sizes (~0.3-1.0 MB)
- **Load time**: <500ms for theme embedding initialization
- **Memory usage**: ~2-3 MB total for both models
- **Error rates**: Similarity computation failures

### Logging Configuration
```python
import logging

# Configure logging for theme embeddings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/theme_embeddings.log'),
        logging.StreamHandler()
    ]
)
```

### Alerting Rules
```yaml
# Example Prometheus/Grafana alerting rules
groups:
  - name: theme_embeddings
    rules:
      - alert: ThemeEmbeddingsMissing
        expr: nobellm_theme_embeddings_files_present < 2
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Theme embedding files missing"
          
      - alert: ThemeEmbeddingsLoadTime
        expr: nobellm_theme_embeddings_load_time_seconds > 1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Theme embeddings taking too long to load"
```

## Backup and Recovery

### Backup Strategy
```bash
#!/bin/bash
# backup_theme_embeddings.sh

BACKUP_DIR="/backups/nobellm/theme_embeddings"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup theme embeddings
tar -czf "$BACKUP_DIR/theme_embeddings_$DATE.tar.gz" \
    data/theme_embeddings/ \
    config/themes.json

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "theme_embeddings_*.tar.gz" -mtime +7 -delete

echo "Theme embeddings backed up to $BACKUP_DIR/theme_embeddings_$DATE.tar.gz"
```

### Recovery Procedure
```bash
#!/bin/bash
# restore_theme_embeddings.sh

BACKUP_FILE="$1"
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

# Stop application if running
# systemctl stop nobellm

# Restore theme embeddings
tar -xzf "$BACKUP_FILE" -C /

# Set proper permissions
chmod 755 data/theme_embeddings/
chmod 644 data/theme_embeddings/*.npz

# Restart application
# systemctl start nobellm

echo "Theme embeddings restored from $BACKUP_FILE"
```

## Troubleshooting Production Issues

### Common Production Issues

1. **Missing embedding files**
   ```bash
   # Solution: Re-run pre-computation
   python scripts/precompute_theme_embeddings.py
   ```

2. **Permission denied errors**
   ```bash
   # Solution: Fix permissions
   chmod 755 data/theme_embeddings/
   chmod 644 data/theme_embeddings/*.npz
   ```

3. **Memory issues**
   ```bash
   # Solution: Check available memory
   free -h
   # Consider using miniLM model for lower memory usage
   ```

4. **Slow initialization**
   ```bash
   # Solution: Check disk I/O
   iostat -x 1
   # Consider SSD storage for better performance
   ```

### Emergency Recovery
```bash
# If theme embeddings are corrupted or missing
cd /path/to/nobellm

# Force recomputation
python -c "
from config.theme_embeddings import ThemeEmbeddings
for model in ['bge-large', 'miniLM']:
    embeddings = ThemeEmbeddings(model)
    embeddings.force_recompute_embeddings()
    print(f'Recomputed embeddings for {model}')
"
```

---

**Last Updated**: 2025-01-XX  
**Version**: 1.0  
**Author**: NobelLM Team 