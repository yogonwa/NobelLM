# 🚀 NobelLM Migration Plan: Streamlit → FastAPI + Vite (Fly.io Deployment)

This guide covers the end-to-end migration of **NobelLM** from Streamlit Cloud to a full-stack web app with:

- **FastAPI** backend (RAG logic)
- **Vite + React (TS)** frontend
- **Fly.io** for deployment
- **Docker** for environment reproducibility

---

## 📁 Suggested Project Structure

```
NobelLM/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI entrypoint
│   │   ├── routes.py             # POST /query route
│   │   ├── deps.py               # Dependency loaders
│   │   ├── config.py             # Env var loading
│   │   └── __init__.py
│   ├── Dockerfile               # Backend Docker setup
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   │   ├── favicon.ico
│   │   └── index.html
│   ├── src/
│   │   ├── App.tsx
│   │   ├── Home.tsx
│   │   ├── About.tsx
│   │   ├── main.tsx
│   │   ├── index.css
│   │   └── assets/nobel_logo.png
│   ├── Dockerfile               # Frontend Docker setup
│   ├── vite.config.ts
│   └── package.json
│
├── data/                        # FAISS index + metadata
│   └── faiss_index_bge-large/   # Mounted/packed into Docker
│
├── .env                         # Dev only
├── fly.toml                     # Fly deployment config
├── docker-compose.yml           # Local dev (optional)
└── README.md
```

---

## 🐳 Docker Setup

### backend/Dockerfile

```Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY data /app/data

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### frontend/Dockerfile

```Dockerfile
FROM node:20-alpine

WORKDIR /app
COPY frontend/package.json frontend/vite.config.ts ./
COPY frontend/src ./src
COPY frontend/public ./public

RUN npm install && npm run build

RUN npm install -g serve
CMD ["serve", "-s", "dist"]
```

### docker-compose.yml (for local dev)

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
```

---

## ☁️ Fly.io Setup

### 1. Install CLI

```bash
brew install flyctl
fly auth login
```

### 2. Create App

```bash
fly launch --name nobellm-api --region iad --no-deploy
```

### 3. fly.toml

```toml
app = "nobellm-api"

[build]
  dockerfile = "backend/Dockerfile"

[env]
  OPENAI_API_KEY = ""
  TOKENIZERS_PARALLELISM = "false"

[[mounts]]
  source = "faiss_data"
  destination = "/app/data"
```

### 4. Set Secrets

```bash
fly secrets set OPENAI_API_KEY=sk-...
```

### 5. Deploy

```bash
fly deploy --remote-only
```

Repeat these steps for frontend using its Dockerfile and a separate app name (e.g. `nobellm-web`). Or serve static files from backend if preferred.

---

## 🧠 Backend Notes

- Use `rag/query_engine.py` as backend logic
- Use `data/faiss_index_bge-large/` inside Docker
- Route handler in `routes.py` will:
  1. Parse user query
  2. Call RAG pipeline
  3. Return answer + metadata

---

## 💻 Frontend Notes

- Use `App.tsx`, `Home.tsx`, `main.tsx`, `About.tsx`, `index.css` from uploaded files
- Add loading state + spinner
- Show `nobel_logo.png` in header
- Add favicon via `public/favicon.ico`
- Use `axios` to POST to backend

---

## ✅ Launch Checklist

-

---

## 📎 Bonus Notes

- If Fly resource constraints occur, bump `VM size` via `fly scale vm shared-cpu-2x`
- Use `fly logs` for debugging backend errors
- Add HTTPS custom domain config via Fly dashboard

---

Ready to proceed with code scaffolding once approved ✅

