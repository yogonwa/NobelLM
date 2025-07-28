# NobelLM

**Semantic search and AI-powered exploration of Nobel Prize laureate speeches**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![Deploy Status](https://img.shields.io/badge/Deploy-Fly.io-blue.svg)](https://fly.io)

---

## Overview

NobelLM is a web app that scrapes, structures, and semantically searches over 100 years of Nobel Literature lectures and speeches. Powered by embeddings and generative AI, it lets users ask open-ended questions and receive grounded responses with citations from real source material.

**Live Application:** [nobellm.com](https://nobellm.com)

### Core Capabilities

- **Semantic Search**: AI-powered Q&A over a century of Nobel speeches
- **Source Citations**: Every response includes verified source material with metadata
- **Modern Architecture**: React TypeScript frontend with FastAPI backend
- **Advanced RAG**: Retrieval-Augmented Generation using local embeddings and OpenAI
- **Multi-Modal Queries**: Supports factual, thematic, and generative query types

---

## System Requirements

### Development Environment
- **Python**: 3.9+ (3.11+ recommended)
- **Node.js**: 18+ (20+ recommended)
- **Memory**: 8GB RAM minimum (16GB recommended)
- **Storage**: 10GB available space for models and data

### Production Environment
- **CPU**: 2+ cores
- **Memory**: 4GB RAM minimum
- **Storage**: 20GB for embeddings and vector database
- **Network**: Stable internet connection for API calls

---

## Quick Start

### Prerequisites
- OpenAI API key with GPT-3.5 access
- (Optional) Qdrant cloud instance for production deployment

### Local Development Setup

1. **Clone and navigate to the repository**
   ```bash
   git clone https://github.com/yogonwa/nobellm.git
   cd nobellm
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp backend/env.production.template .env
   # Edit .env with your OpenAI API key and other credentials
   ```

4. **Set up frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

5. **Start the backend service**
   ```bash
   uvicorn backend.app.main:app --reload --port 8000
   ```

6. **Start the frontend development server**
   ```bash
   cd frontend
   npm run dev
   ```

7. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

---

## Architecture

### System Design

NobelLM follows a modern microservices architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Vector DB     │
│   (React SPA)   │◄──►│   (FastAPI)     │◄──►│   (Qdrant)      │
│   Port 5173     │    │   Port 8000     │    │   Cloud         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Embedding     │    │   RAG Pipeline  │    │   Data Pipeline │
│   Service       │    │   (Local/Modal) │    │   (Scraping)    │
│   (Modal)       │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack

#### Frontend Layer
- **Framework**: React 18.3.1 with TypeScript 5.8.3
- **Build Tool**: Vite 6.3.5 for fast development and optimized builds
- **Styling**: Tailwind CSS 3.4.1 with custom animations
- **Routing**: React Router DOM 7.6.2
- **Testing**: Vitest with React Testing Library

#### Backend Layer
- **Framework**: FastAPI with async/await support
- **RAG Engine**: Modular retrieval system with intent classification
- **Vector Database**: Qdrant Cloud (production) / FAISS (development)
- **Embedding Service**: Modal cloud service (production) / Local sentence transformers (development)
- **LLM Integration**: OpenAI GPT-3.5-turbo for answer generation

#### Data Pipeline
- **Web Scraping**: Automated collection from NobelPrize.org
- **Text Processing**: Advanced chunking with semantic boundary detection
- **Embedding Models**: BGE-Large (1024d) and MiniLM (384d) support
- **Vector Search**: Cosine similarity with configurable thresholds

### Key Design Decisions

1. **Separation of Concerns**: Frontend and backend are completely decoupled
2. **Environment-Aware Embedding**: Automatic routing between local and cloud embedding services
3. **Model-Aware Architecture**: Support for multiple embedding models with automatic configuration
4. **Production-Ready**: Built-in health checks, monitoring, and error handling

---

## Production Deployment

### Deployment Architecture

NobelLM is deployed on **Fly.io** with the following configuration:

- **Frontend**: `nobellm-web.fly.dev` (React SPA with CDN)
- **Backend**: `nobellm-api.fly.dev` (FastAPI with auto-scaling)
- **Vector Database**: Qdrant Cloud with persistent storage
- **Embedding Service**: Modal cloud functions for scalable inference

### Deployment Commands

```bash
# Deploy backend service
fly deploy --config fly.toml

# Deploy frontend application
cd frontend
fly deploy --config fly.toml
```

### Environment Configuration

Required environment variables for production:
```bash
OPENAI_API_KEY=sk-your-openai-key
QDRANT_URL=https://your-qdrant-instance.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key
MODAL_TOKEN_ID=your-modal-token-id
MODAL_TOKEN_SECRET=your-modal-token-secret
```

See [`PRODUCTION_DEPLOYMENT_GUIDE.md`](PRODUCTION_DEPLOYMENT_GUIDE.md) for comprehensive deployment instructions.

---

## API Reference

### Core Endpoints

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/api/query` | POST | Submit query and receive AI response | None |
| `/api/health` | GET | Health check endpoint | None |
| `/api/readyz` | GET | Kubernetes-style readiness probe | None |
| `/docs` | GET | Interactive API documentation | None |

### Query API Example

```bash
curl -X POST "https://nobellm-api.fly.dev/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What did Toni Morrison say about justice and race?",
    "model_id": "bge-large"
  }'
```

### Response Format

```json
{
  "answer": "Toni Morrison's response about justice and race...",
  "answer_type": "rag",
  "sources": [
    {
      "chunk_id": "1993_morrison_nobel_lecture_2",
      "laureate": "Toni Morrison",
      "year_awarded": 1993,
      "source_type": "nobel_lecture",
      "text": "Excerpt from the speech...",
      "score": 0.89
    }
  ],
  "metadata": {
    "processing_time": 1.23,
    "tokens_used": 150,
    "model": "gpt-3.5-turbo"
  }
}
```

---

## Testing

### Test Suite Overview

The project includes a comprehensive, multi-layered testing strategy:

```bash
# Run complete test suite
pytest

# Run specific test categories
pytest tests/unit/          # Unit tests (fast)
pytest tests/integration/   # Integration tests (medium)
pytest tests/e2e/          # End-to-end tests (slow)
pytest tests/validation/   # Data validation tests

# Frontend testing
cd frontend
npm run test              # Unit tests
npm run test:coverage     # Coverage report
```

### Test Coverage

- **Unit Tests**: Individual component testing with mocked dependencies
- **Integration Tests**: Component interaction testing with realistic data flow
- **End-to-End Tests**: Full workflow validation with minimal mocking
- **Validation Tests**: Data quality and schema validation

See [`tests/README.md`](tests/README.md) for detailed testing documentation and patterns.

---

## Project Structure

```
NobelLM/
├── frontend/                 # React TypeScript application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── types/          # TypeScript definitions
│   │   └── utils/          # Frontend utilities
│   ├── package.json
│   └── fly.toml           # Frontend deployment config
├── backend/                  # FastAPI backend service
│   ├── app/
│   │   ├── main.py         # Application entry point
│   │   ├── routes.py       # API route definitions
│   │   ├── config.py       # Configuration management
│   │   └── deps.py         # Dependency injection
│   ├── requirements.txt
│   └── Dockerfile
├── rag/                     # RAG pipeline and retrieval logic
│   ├── query_engine.py     # Main query processing
│   ├── retriever.py        # Vector search interface
│   ├── intent_classifier.py # Query intent classification
│   └── prompt_builder.py   # LLM prompt construction
├── embeddings/              # Text processing and embedding
├── scraper/                 # Data collection from NobelPrize.org
├── tests/                   # Comprehensive test suite
├── utils/                   # Shared utilities and helpers
├── config/                  # Configuration files
├── data/                    # Processed data and embeddings
└── docs/                    # Documentation
```

---

## Development Guidelines

### Code Standards

- **Python**: Follow PEP 8 with type hints for all public functions
- **TypeScript**: Strict mode enabled with comprehensive type definitions
- **Testing**: Minimum 80% code coverage for new features
- **Documentation**: Docstrings for all public APIs and complex functions

### Commit Conventions

Follow semantic commit messages:
```
feat: add new query routing logic
fix: resolve embedding dimension mismatch
docs: update API documentation
test: add integration tests for Qdrant
refactor: simplify retriever factory pattern
```

### Pull Request Process

1. Create feature branch from `main`
2. Implement changes with comprehensive tests
3. Update documentation as needed
4. Ensure all tests pass locally
5. Submit PR with clear description and testing notes

---

## Troubleshooting

### Common Issues

#### Backend Startup Problems
```bash
# Module import errors
export PYTHONPATH=$(pwd)
uvicorn backend.app.main:app --reload

# Missing dependencies
pip install -r requirements.txt
```

#### Frontend Build Issues
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 18+
```

#### Vector Database Connection
```bash
# Test Qdrant connectivity
python tests/e2e/test_qdrant_health.py

# Verify environment variables
echo $QDRANT_URL
echo $QDRANT_API_KEY
```

### Performance Optimization

- **Embedding Caching**: Enable Modal caching for repeated queries
- **Vector Index**: Use appropriate Qdrant index configuration
- **Frontend**: Implement query result caching and debouncing

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Nobel Prize Foundation** for making laureate speeches publicly available
- **OpenAI** for GPT-3.5 API access and support
- **Qdrant** for vector database infrastructure
- **Modal** for cloud-based embedding services
- **Fly.io** for hosting infrastructure

---

## Contact & Support

- **Maintainer**: Joe Gonwa
- **Website**: [nobellm.com](https://nobellm.com)
- **GitHub**: [yogonwa/nobellm](https://github.com/yogonwa/nobellm)
- **Technical Blog**: [Behind-the-scenes series](https://joegonwa.com/projects/nobellm/)

For technical questions, bug reports, or feature requests, please open an issue on GitHub with appropriate labels and detailed information.
