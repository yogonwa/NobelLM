# 🚀 NobelLM Migration Plan: Streamlit → FastAPI + Vite (Fly.io Deployment)

*This document defines the implementation plan to migrate the Nobel Laureate Speech Explorer to a production-grade deployment stack.*

**Last Updated:** January 2025  
**Status:** Phase 2 Complete ✅  
**Branch:** `fastapi-vite-migration`

---

## 📊 Migration Progress Tracker

### ✅ Completed Phases

**Phase 1: Clean Up and Pre-Migration** ✅
- [x] Environment setup validation
- [x] Git LFS tracking confirmation  
- [x] FAISS index validation
- [x] RAG pipeline testing
- [x] Theme embeddings LFS integration

**Phase 2: Backend Setup (FastAPI)** ✅
- [x] FastAPI application structure created
- [x] Core API endpoints implemented:
  - `GET /` - API info
  - `GET /api/health` - Health check
  - `POST /api/query` - RAG query processing
  - `GET /api/models` - Available models
- [x] Pydantic request/response models
- [x] RAG pipeline integration with dependency injection
- [x] Environment configuration management
- [x] Comprehensive error handling and logging
- [x] Function signature mapping corrected and tested

**Technical Achievements:**
- Fixed Pydantic v2 compatibility issues
- Resolved function signature mismatches (answer_query parameters)
- Avoided Streamlit caching conflicts with direct FAISS/model loading
- Implemented proper async/await patterns for FastAPI
- Corrected parameter mapping: top_k → max_return

**Testing Results:**
- ✅ All endpoints respond correctly
- ✅ Query processing works with full RAG pipeline
- ✅ Error handling for invalid requests
- ✅ Model switching capability (bge-large working)
- ✅ Thematic query expansion working (815 chunks → 324 unique → 5 final)
- ✅ RAG pipeline returns proper answer structure with sources

**Final Testing Summary:**
- All API endpoints tested and working
- RAG pipeline integration successful with thematic query expansion
- Function signature mapping corrected (top_k → max_return)
- Production-ready backend ready for containerization

### 🔄 Remaining Phases

**Phase 3: Docker Environment Setup** ⬜️
**Phase 4: Frontend Setup (React + TypeScript)** ⬜️
**Phase 5: Fly.io Deployment** ⬜️

---

## 📋 Table of Contents

1. [Project Scope](#project-scope)
2. [Migration Context](#migration-context)
3. [Developer Guidelines](#developer-guidelines)
4. [Technical Architecture](#technical-architecture)
5. [Migration Tasks](#migration-tasks)
6. [Launch Checklist](#launch-checklist)
7. [Future Enhancements](#future-enhancements)

---

## 🎯 Project Scope

### **Current State**
- **Frontend:** Streamlit Cloud (Hugging Face Spaces)
- **Backend:** Streamlit app with embedded RAG pipeline
- **Deployment:** Hugging Face Spaces (no Docker, no custom domain)

### **Target State**
- **Frontend:** React + TypeScript + Vite
- **Backend:** FastAPI (Python) with RAG pipeline
- **Deployment:** Fly.io (Docker-based, custom domain support)
- **Architecture:** Full-stack separation with API-first design

---

## 🔄 Migration Context

**What We're Deprecating:**
- Streamlit Cloud deployment
- Hugging Face Spaces hosting
- Monolithic Streamlit app architecture

**What We're Implementing:**
- Docker containerization
- FastAPI backend with REST API
- React frontend with TypeScript
- Fly.io production deployment
- Custom domain and HTTPS

---

## 📌 Developer Guidelines

### **Before Making Changes**
1. **Repeat the intended change and strategy** out loud or in writing
2. **Get signoff** before writing code
3. **Search `/tests`** for relevant coverage before introducing changes
4. **Write new tests** where applicable

### **Code Standards**
All code must:
- Include **clear function/class docstrings**
- Follow **code styles from `.cursorrules`**
- Avoid **side effects and global state**
- Use **logging, not print statements**
- Include **type hints** for all functions

### **Documentation Requirements**
- Update **README.md** (root and `/rag`)
- Mark **related tasks complete** in this migration file
- Document **new scripts or folders**
- List **input/output formats** for all components

---

## 🏗️ Technical Architecture

### **Project Structure**
```
NobelLM/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI entrypoint
│   │   ├── routes.py             # API route handlers
│   │   ├── deps.py               # Dependency injection
│   │   ├── config.py             # Environment configuration
│   │   └── __init__.py
│   ├── Dockerfile               # Backend container
│   └── requirements.txt         # Python dependencies
│
├── frontend/
│   ├── public/
│   │   ├── favicon.ico
│   │   └── index.html
│   ├── src/
│   │   ├── App.tsx              # Main React component
│   │   ├── Home.tsx             # Query interface
│   │   ├── About.tsx            # About page
│   │   ├── main.tsx             # React entry point
│   │   ├── index.css            # Global styles
│   │   └── assets/
│   │       └── nobel_logo.png   # Nobel logo
│   ├── Dockerfile               # Frontend container
│   ├── vite.config.ts           # Vite configuration
│   └── package.json             # Node dependencies
│
├── data/                        # FAISS index + metadata
│   └── faiss_index_bge-large/   # Mounted into Docker
│
├── rag/                         # Existing RAG pipeline
├── embeddings/                  # Existing embedding logic
├── tests/                       # Test suite
├── .env                         # Development environment
├── fly.toml                     # Fly.io deployment config
├── docker-compose.yml           # Local development
└── README.md                    # Project documentation
```

### **Data Flow**
1. **User Query** → React Frontend
2. **API Request** → FastAPI Backend (`/api/query`)
3. **RAG Pipeline** → `rag/query_engine.py`
4. **FAISS Search** → `data/faiss_index_bge-large/`
5. **OpenAI Response** → Structured JSON
6. **UI Update** → React renders results

---

## 📋 Migration Tasks

### **Phase 1: Clean Up and Pre-Migration** ✅

- [x] **Confirm environment setup**
  - [x] Verify `.env` file configuration
  - [x] Confirm Git LFS tracking for large files
  - [x] Validate local FAISS index locations
  - [x] Test RAG pipeline functionality

- [x] **Archive current deployment**
  - [x] Document current Streamlit Cloud setup
  - [x] Backup current configuration
  - [x] Update documentation to reflect migration

- [x] **Review project structure**
  - [x] Audit existing code against `.cursorrules`
  - [x] Identify components to migrate vs. refactor
  - [x] Plan test coverage for new components

- [x] **Theme embeddings LFS integration**
  - [x] Regenerate theme embeddings for both models
  - [x] Add to Git LFS tracking
  - [x] Test persistence across branch switches
  - [x] Commit to migration branch

### **Phase 2: Backend Setup (FastAPI)** ✅

- [x] **Create FastAPI application structure**
  - [x] Set up `backend/app/` directory
  - [x] Create `main.py` with FastAPI app
  - [x] Implement `/api/query` endpoint
  - [x] Add request/response models with Pydantic

- [x] **Integrate RAG pipeline**
  - [x] Refactor `rag/query_engine.py` for API use
  - [x] Add dependency injection for FAISS index
  - [x] Implement proper error handling
  - [x] Add request validation and logging

- [x] **Environment configuration**
  - [x] Create `backend/app/config.py`
  - [x] Move environment variables to Fly.io secrets
  - [x] Add configuration validation
  - [x] Implement development vs. production settings

**Status:** ✅ **COMPLETE** - FastAPI backend is fully functional with RAG pipeline integration

### **Phase 3: Docker Environment Setup** ⬜️

- [ ] **Backend Dockerfile**
  ```dockerfile
  FROM python:3.10-slim
  
  WORKDIR /app
  
  # Install system dependencies
  RUN apt-get update && apt-get install -y \
      gcc \
      && rm -rf /var/lib/apt/lists/*
  
  # Install Python dependencies
  COPY backend/requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  
  # Copy application code
  COPY backend/app ./app
  COPY rag ./rag
  COPY data ./data
  
  # Expose port
  EXPOSE 8000
  
  # Start application
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

- [ ] **Frontend Dockerfile**
  ```dockerfile
  FROM node:20-alpine AS builder
  
  WORKDIR /app
  
  # Copy package files
  COPY frontend/package*.json ./
  
  # Install dependencies
  RUN npm ci
  
  # Copy source code
  COPY frontend/src ./src
  COPY frontend/public ./public
  COPY frontend/vite.config.ts ./
  
  # Build application
  RUN npm run build
  
  # Production stage
  FROM nginx:alpine
  
  # Copy built files
  COPY --from=builder /app/dist /usr/share/nginx/html
  
  # Copy nginx configuration
  COPY frontend/nginx.conf /etc/nginx/nginx.conf
  
  EXPOSE 80
  
  CMD ["nginx", "-g", "daemon off;"]
  ```

- [ ] **Docker Compose for development**
  ```yaml
  version: '3.8'
  services:
    backend:
      build: ./backend
      ports:
        - "8000:8000"
      env_file:
        - .env
      volumes:
        - ./data:/app/data:ro
    
    frontend:
      build: ./frontend
      ports:
        - "3000:80"
      depends_on:
        - backend
  ```

### **Phase 4: Frontend Setup (React + TypeScript)** ⬜️

- [ ] **Initialize Vite + React project**
  - [ ] Set up TypeScript configuration
  - [ ] Configure Tailwind CSS
  - [ ] Add ESLint and Prettier
  - [ ] Set up testing with Vitest

- [ ] **Implement core components**
  - [ ] Create `App.tsx` with routing
  - [ ] Build `Home.tsx` query interface
  - [ ] Add `About.tsx` information page
  - [ ] Implement loading states and error handling

- [ ] **API integration**
  - [ ] Create API client with axios
  - [ ] Implement query submission
  - [ ] Add response parsing and display
  - [ ] Handle error states gracefully

- [ ] **UI/UX improvements**
  - [ ] Integrate Nobel logo
  - [ ] Add favicon
  - [ ] Implement responsive design
  - [ ] Add loading spinners and animations

### **Phase 5: Fly.io Deployment** ⬜️

- [ ] **Backend deployment**
  ```toml
  # fly.toml
  app = "nobellm-api"
  
  [build]
    dockerfile = "backend/Dockerfile"
  
  [env]
    OPENAI_API_KEY = ""
    TOKENIZERS_PARALLELISM = "false"
  
  [[mounts]]
    source = "faiss_data"
    destination = "/app/data"
  
  [http_service]
    internal_port = 8000
    force_https = true
    auto_stop_machines = true
    auto_start_machines = true
    min_machines_running = 0
  ```

- [ ] **Frontend deployment**
  ```toml
  # fly.toml
  app = "nobellm-web"
  
  [build]
    dockerfile = "frontend/Dockerfile"
  
  [http_service]
    internal_port = 80
    force_https = true
    auto_stop_machines = true
    auto_start_machines = true
    min_machines_running = 0
  ```

- [ ] **Deployment commands**
  ```bash
  # Set secrets
  fly secrets set OPENAI_API_KEY=sk-...
  
  # Deploy backend
  fly deploy --remote-only
  
  # Deploy frontend
  fly deploy --remote-only
  ```

---

## ✅ Launch Checklist

| Task | Status | Notes |
|------|--------|-------|
| Dockerfile created and tested | ⬜️ | Backend and frontend |
| FastAPI endpoint returns results | ⬜️ | `/api/query` functional |
| Frontend consumes API | ⬜️ | React integration complete |
| FAISS index bundled correctly | ⬜️ | Data mounted in container |
| Fly.io secrets configured | ⬜️ | Environment variables set |
| Tests pass in new environment | ⬜️ | All test suites green |
| README.md updated | ⬜️ | Documentation current |
| Logo and favicon render | ⬜️ | UI assets working |
| HTTPS and custom domain | ⬜️ | Production ready |
| Performance monitoring | ⬜️ | Response times acceptable |

---

## 🚀 Future Enhancements (Post-Migration)

### **Infrastructure Improvements**
- [ ] Move FAISS index to persistent external volume or S3
- [ ] Add Redis caching for query results
- [ ] Implement database for query logging (SQLite/PostgreSQL)
- [ ] Add health checks and monitoring

### **Feature Enhancements**
- [ ] Add speech PDF previews (from `/data/nobel_lectures_pdfs`)
- [ ] Implement theme-based prompt selectors
- [ ] Add query history and favorites
- [ ] Implement user authentication
- [ ] Add export functionality (PDF, JSON)

### **Performance Optimizations**
- [ ] Implement query result caching
- [ ] Add CDN for static assets
- [ ] Optimize bundle sizes
- [ ] Add service worker for offline support

---

## 📚 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vite Documentation](https://vitejs.dev/)
- [Fly.io Documentation](https://fly.io/docs/)
- [React TypeScript Guide](https://react-typescript-cheatsheet.netlify.app/)

---

*This migration plan follows the project's cursor rules and maintains the existing RAG pipeline while modernizing the deployment architecture.*