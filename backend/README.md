# NobelLM Backend

FastAPI backend for the NobelLM application, providing the RAG pipeline and API endpoints for semantic search of Nobel Prize speeches.

## Important Setup Notes

**Always run the backend from the NobelLM project root directory.** This ensures that the `rag` module and other top-level packages are importable by Python.

### Correct Usage

```bash
# From project root (correct)
cd /path/to/NobelLM
uvicorn backend.app.main:app --reload --port 8000
```

### Common Error

If you run from within the `backend/` directory, you will get:
```
ModuleNotFoundError: No module named 'rag'
```

### Alternative Setup

If you need to run from a different directory, set the `PYTHONPATH`:
```bash
PYTHONPATH=$(pwd) uvicorn backend.app.main:app --reload --port 8000
```

---

## Architecture

### RAG Pipeline
- **Query Processing**: Intent classification and routing
- **Retrieval**: Vector search with FAISS (local) or Qdrant (production)
- **Generation**: OpenAI GPT-3.5 integration
- **Response Compilation**: Answer formatting with source citations

### Vector Database Support
The backend supports both local and cloud vector databases:

- **FAISS** (local/development): Fast local vector search
- **Qdrant** (production): Cloud-native vector database

### Embedding Service
- **Development**: Local embedding using sentence transformers
- **Production**: Modal cloud service for scalable embedding

---

## Configuration

### Environment Variables

Create a `.env` file in the project root with:

```bash
# Required
OPENAI_API_KEY=your-openai-api-key

# Optional - for production
QDRANT_URL=https://your-qdrant-instance.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key

# Optional - for Modal embedding service
MODAL_TOKEN_ID=your-modal-token-id
MODAL_TOKEN_SECRET=your-modal-token-secret
```

### Environment Templates

Use the provided template:
```bash
cp backend/env.production.template .env
```

---

## API Endpoints

### Core Endpoints
- `POST /api/query` - Submit a query and receive AI-generated response
- `GET /api/health` - Health check endpoint
- `GET /api/readyz` - Kubernetes-style readiness probe

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

### Example Usage

```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What did Toni Morrison say about justice?",
    "model_id": "bge-large"
  }'
```

---

## Development

### Prerequisites
- Python 3.9+
- Virtual environment activated
- Dependencies installed: `pip install -r requirements.txt`

### Running Locally

1. **Start the backend**
   ```bash
   # From project root
   uvicorn backend.app.main:app --reload --port 8000
   ```

2. **Access the API**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/api/health

### Development Features
- **Hot Reload**: Automatic server restart on code changes
- **Debug Mode**: Detailed error messages and CORS debugging
- **API Documentation**: Interactive Swagger UI

---

## Production Deployment

The backend is deployed on Fly.io with the following configuration:

- **App Name**: `nobellm-api`
- **URL**: https://nobellm-api.fly.dev
- **Resources**: 1 CPU, 2GB RAM
- **Health Checks**: Automatic monitoring

### Deployment Commands

```bash
# Deploy to production
fly deploy --config fly.toml

# Check deployment status
fly status

# View logs
fly logs
```

---

## Troubleshooting

### Common Issues

1. **Module Import Errors**
   - Ensure you're running from the project root
   - Check that `PYTHONPATH` includes the project root

2. **Qdrant Connection Issues**
   - Verify `QDRANT_URL` and `QDRANT_API_KEY` are set correctly
   - Check network connectivity to Qdrant instance

3. **OpenAI API Errors**
   - Verify `OPENAI_API_KEY` is valid and has sufficient credits
   - Check rate limits and API quotas

4. **Embedding Service Issues**
   - For production: Verify Modal credentials
   - For development: Ensure sentence-transformers models are downloaded

### Logging

The backend uses structured logging with different levels:
- `INFO`: General application flow
- `DEBUG`: Detailed debugging information
- `ERROR`: Error conditions and exceptions

---

## License

Part of the NobelLM project - see main project LICENSE for details. 