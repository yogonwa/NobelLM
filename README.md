# NobelLM

**Semantic search + Retrieval-Augmented Generation (RAG) for Nobel Prize speeches**  
Explore the words of Nobel laureates through embeddings, vector search, and a lightweight Streamlit UI.

---

## 🎯 Project Overview

NobelLM is a modular, full-stack GenAI project that:

- Scrapes and normalizes NobelPrize.org metadata and speeches (starting with the Literature category)
- Embeds speech content using sentence-transformers (MiniLM)
- Supports natural language Q&A via RAG using OpenAI's GPT-3.5
- Exposes a simple interactive UI powered by Streamlit
- Deploys publicly via Hugging Face Spaces

This project is designed for learning, modularity, and extensibility.

---

## 🧠 Key Features

- 🗂 Structured metadata and full-text speech extraction
- 🔎 Local embedding + FAISS vector search
- 🤖 RAG-powered question answering with GPT-3.5
- 🖥 Streamlit interface for live semantic search
- 🚀 Public deployment via Hugging Face Spaces

---

## 📁 Folder Structure

```text
NobelLM/
├── data/                 # Raw and processed data (JSON, CSV, text, embeddings)
├── scraper/              # NobelPrize.org scraping scripts
├── embeddings/           # Chunking and vector embedding logic
├── rag/                  # Retrieval-augmented generation pipeline
├── frontend/             # Streamlit UI app
├── utils/                # Shared helpers (e.g., cleaning)
├── tests/                # Pytest test modules
├── .env.example          # Environment variable template
├── requirements.txt      # Project dependencies
├── IMPLEMENTATION_PLAN.md
├── SPEC.md
├── TASKS.md
├── NOTES.md
├── .cursorrules          # Cursor AI execution rules


## ⚙️ Tech Stack

- **Language**: Python 3.11+
- **Scraping**: `requests`, `beautifulsoup4`
- **Text Parsing**: `PyMuPDF`, custom HTML/text cleaning
- **Embeddings**: `sentence-transformers` (MiniLM model), upgradeable to OpenAI `text-embedding-3-small`
- **Vector Store**: `FAISS` (cosine similarity, local CPU)
- **Frontend**: `Streamlit` (hosted on Hugging Face Spaces)
- **Testing**: `pytest`
- **Deployment**: GitHub + Hugging Face Spaces

---

## 📌 Roadmap

| Phase | Description |
|-------|-------------|
| **M1** | Scrape and normalize Nobel Literature data |
| **M2** | Generate text chunks and sentence embeddings |
| **M3** | Build FAISS index and RAG query pipeline |
| **M4** | Launch public Streamlit UI |
| **M5** | Add prompt templates and memory scaffolding |
| **M5b** | Extend pipeline to other Nobel Prize categories |
| **M6** | Migrate embedding generation to OpenAI API |

See [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md) and [`TASKS.md`](./TASKS.md) for detailed milestones.

---

## 🚀 Getting Started

1. **Clone the repo**  
   ```bash
   git clone https://github.com/yourusername/NobelLM.git
   cd NobelLM
Create a virtual environment

bash
Copy code
python -m venv venv
source venv/bin/activate  # or 'venv\Scripts\activate' on Windows
Install dependencies

bash
Copy code
pip install -r requirements.txt
Set up environment variables

bash
Copy code
cp .env.example .env
# Add your OpenAI API key to the .env file
Run an example module

bash
Copy code
python -m scraper.scrape_literature
📄 License
This project is for educational and exploratory purposes only. Source data is publicly available and usage falls under fair use.

✍️ Author
Built by Joe Gonwa as a structured learning project in GenAI and RAG systems.
Feedback, PRs, and suggestions are always welcome!

## Testing
Unit tests for extraction/parsing logic (e.g., HTML parsing, gender inference) are in `/tests/test_scraper.py`. Run `pytest` from the project root.
