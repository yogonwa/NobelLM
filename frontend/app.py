"""
Nobel Laureate Speech Explorer – Streamlit Frontend

This app provides a minimalist, modern UI for querying and exploring Nobel Prize laureate speeches and metadata.
- Query input with Enter or button
- Suggested prompts as buttons
- Rich answer and source rendering
- Minimalist navigation, multipage-ready
- Robust error handling

Author: NobelLM Team
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
from rag.query_engine import answer_query  # You must implement this module
import textwrap

# Debug prints to diagnose import issues
print("sys.path:", sys.path)
print("cwd:", os.getcwd())
print("answer_query repr:", repr(answer_query))
print("answer_query type:", type(answer_query))
print("answer_query module:", getattr(answer_query, '__module__', None))

st.set_page_config(
    page_title="NobelLM",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS to style buttons and layout ---
st.markdown("""
    <style>
    .stButton > button {
        background-color: #f5f5f5;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.2rem;
        margin: 0.2rem;
        font-size: 0.95rem;
    }
    .css-1v0mbdj.ef3psqc12 {
        display: flex;
        justify-content: center;
    }
    .suggestions-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        margin-top: 1rem;
    }
    .st-expander {
        border-radius: 12px;
        margin-bottom: 14px;
    }
    .st-expander > summary {
        font-weight: 600;
    }
    .stMarkdown h3 {
        margin-top: 2rem;
        margin-bottom: 0.5rem;
    }
    .stButton>button {
        margin-top: 1rem;
    }
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
    button[kind='secondary'] {
        font-size: 0.85rem;
        margin-top: 0.25rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- Top-right navigation links ---
def nav_link(label, page):
    st.markdown(f"<a href='/{page}' target='_self' class='nav-link'>{label}</a>", unsafe_allow_html=True)

st.markdown("""
    <div class='top-nav'>
        <a href='/' target='_self' class='home-link'>Home</a>
        <a href='/About' target='_self' class='about-link'>About</a>
    </div>
""", unsafe_allow_html=True)

# --- Centered logo and title ---
# The logo is 1024x1024, so it will be sharp at 200x200.
logo_path = os.path.join(os.path.dirname(__file__), "assets", "nobel_logo.png")
st.image(logo_path, width=200)
st.markdown("## **NobelLM**", unsafe_allow_html=True)
st.markdown(
    "Ask questions and discover insights from over a century of Nobel Prize lectures and acceptance speeches.",
    unsafe_allow_html=True
)

# --- Ensure query is always initialized ---
if "query" not in st.session_state:
    st.session_state["query"] = ""

# --- Input box and search form ---
with st.form("main_query_form", clear_on_submit=False):
    query = st.text_input(
        "Ask a question about Nobel Prize laureates...",
        value=st.session_state["query"],
        label_visibility="collapsed",
        key="main_query_input"
    )
    submit = st.form_submit_button("🔍 Search")

# --- Main query logic ---
if submit and query and "results_shown" not in st.session_state:
    with st.spinner("Thinking..."):
        try:
            # Expect answer_query to return a dict with answer_type, answer, metadata_answer, sources
            response = answer_query(query)
            # Clear any old answer/sources to prevent stale display
            st.session_state.pop("answer", None)
            st.session_state.pop("sources", None)
            st.session_state["response"] = response
            st.session_state["results_shown"] = True
        except Exception as e:
            st.error(f"Sorry, something went wrong. ({type(e).__name__}: {e})")

# --- Helper: Render metadata (factual) answer card ---
def render_metadata_card(answer, rule=None):
    """Display a compact card for factual/metadata answers."""
    st.success(answer)
    if rule:
        st.caption(f"Answered from Nobel metadata (Rule: {rule})")

# --- Show results ---
if st.session_state.get("results_shown"):
    response = st.session_state["response"]
    if response["answer_type"] == "metadata":
        # Render factual/metadata answer card only (no sources)
        rule = response.get("metadata_answer", {}).get("source", {}).get("rule")
        render_metadata_card(response["answer"], rule)
    else:
        # --- Existing RAG/LLM rendering (to be refactored later) ---
        st.markdown("### Answer")
        st.markdown(response["answer"])

        st.markdown("### Sources")
        def get_chip(source_type):
            if source_type == "nobel_lecture":
                return "🎓 Lecture"
            elif source_type == "ceremony_speech":
                return "🏅 Ceremony"
            elif source_type == "acceptance_speech":
                return "🗯 Speech"
            return ""

        st.markdown("""
        <style>
            button[kind='secondary'] {
                font-size: 0.85rem;
                margin-top: 0.25rem;
            }
        </style>
        """, unsafe_allow_html=True)

        for i, s in enumerate(response.get("sources", [])):
            year = s.get("year_awarded", "?")
            name = s.get("laureate", "?")
            text = s.get("text_snippet", "").strip()
            source_type = s.get("source_type", "")
            chip = get_chip(source_type)

            # --- Header formatting ---
            header_html = f"""
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div><strong>{year} – {name}</strong> &nbsp;
                    <span style='background:#f0f0f0;border-radius:6px;padding:2px 6px;font-size:0.8rem;'>{chip}</span>
                </div>
            </div>
            """

            with st.expander("", expanded=True):
                st.markdown(header_html, unsafe_allow_html=True)
                st.markdown(text)

        # Try Again button
        if st.button("🔄 Try Again"):
            st.session_state.clear()
            st.session_state["query"] = ""
            st.rerun()

# --- Example prompts ---
if not st.session_state.get("results_shown"):
    st.markdown("#### Try asking")
    suggestions = [
        "What do laureates say about justice?",
        "Which country has won the most Nobel Prizes in Literature?",
        "How have peace laureates addressed climate change?",
        "What themes connect Physics and Chemistry laureates?",
        "How have acceptance speeches evolved over the last century?",
    ]
    col1, col2 = st.columns(2)
    for i, prompt in enumerate(suggestions):
        if i % 2 == 0:
            with col1:
                if st.button(prompt, key=f"suggestion_{i}"):
                    st.session_state.clear()
                    st.session_state["query"] = prompt
                    response = answer_query(prompt)
                    st.session_state["response"] = response
                    st.session_state["results_shown"] = True
                    st.rerun()
        else:
            with col2:
                if st.button(prompt, key=f"suggestion_{i}"):
                    st.session_state.clear()
                    st.session_state["query"] = prompt
                    response = answer_query(prompt)
                    st.session_state["response"] = response
                    st.session_state["results_shown"] = True
                    st.rerun()
