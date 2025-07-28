import streamlit as st
from PIL import Image
import os
from frontend.nav import render_nav

logo_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "assets", "nobel_logo.png")
favicon_img = Image.open(logo_path)

st.set_page_config(
    page_title="About NobelLM",
    page_icon=favicon_img,
    layout="centered",
    initial_sidebar_state="collapsed"
)

render_nav()

st.title("About NobelLM")

st.markdown("""
The **NobelLM** is a data-driven tool for exploring, searching, and analyzing speeches and metadata from Nobel Prize laureates, with an initial focus on Literature.

**Features:**
- Semantic search and Q&A over a century of Nobel Laureate lectures and speeches
- Rich metadata and source citations
- Modern, minimalist UI
- Powered by local embeddings, FAISS, and OpenAI (RAG)

**How it works:**
1. Scrapes and normalizes NobelPrize.org data
2. Chunks and embeds speech text for semantic search
3. Retrieves relevant passages and generates answers using LLMs

**Source & License:**
- All data is public and used under fair use for educational purposes.
- [GitHub Repository](https://github.com/yogonwa/nobellm)

**Contact:**
- Maintained by Joe Gonwa
- For questions or contributions, open an issue on GitHub.
""") 