import streamlit as st

st.set_page_config(
    page_title="About NobelLM",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .top-nav {
        position: absolute;
        top: 18px;
        right: 32px;
        z-index: 100;
        font-size: 1rem;
    }
    .top-nav a {
        margin-left: 18px;
        color: #3366cc;
        text-decoration: none;
        font-weight: 500;
    }
    .top-nav a.active {
        color: #222;
        font-weight: bold;
        text-decoration: underline;
    }
    </style>
    <div class='top-nav'>
        <a href='/' class='home-link'>Home</a>
        <a href='/About' class='about-link'>About</a>
    </div>
""", unsafe_allow_html=True)

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