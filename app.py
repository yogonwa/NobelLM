---
title: NobelLM
emoji: 📚
colorFrom: indigo
colorTo: blue
sdk: streamlit
sdk_version: "1.32.2"
app_file: app.py
pinned: false
---




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

import subprocess
import os
import sys

# Ensure spaCy model is available by running setup.sh
setup_path = os.path.join(os.path.dirname(__file__), "setup.sh")
subprocess.run(["bash", setup_path], check=True)

# Now continue with the rest of the app setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
from rag.query_engine import answer_query  # You must implement this module
import textwrap
from PIL import Image
from frontend.nav import render_nav
# --- Analytics and Logging ---
from utils.analytics import init_plausible, track_pageview, track_event
from utils.logger import log_query
import spacy

# Import the country_to_flag utility
try:
    from utils.country_utils import country_to_flag
except ImportError:
    def country_to_flag(country):
        return ""

# Debug prints to diagnose import issues
print("sys.path:", sys.path)
print("cwd:", os.getcwd())
print("answer_query repr:", repr(answer_query))
print("answer_query type:", type(answer_query))
print("answer_query module:", getattr(answer_query, '__module__', None))

# Load logo for favicon
favicon_img = Image.open(os.path.join(os.path.dirname(__file__), "frontend", "assets", "nobel_logo.png"))

st.set_page_config(
    page_title="NobelLM",
    page_icon=favicon_img,
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize Plausible analytics (set your domain here or use env var)
init_plausible(os.getenv("PLAUSIBLE_DOMAIN", "nobellm-demo.hf.space"))

render_nav()

# Track pageview for home (main view)
track_pageview("home")

# Ensure en_core_web_sm is available
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # setup.sh handles this now
    nlp = spacy.load("en_core_web_sm")

# --- Custom CSS to style buttons and layout ---
st.markdown("""
    <style>
    .stButton > button {
        background-color: #f5f5f5;
        color: var(--text-color, #222) !important;
        border: none;
        border-radius: 10px;
        padding: 0.4rem 1.2rem 0.4rem 1.2rem;
        margin: 0.2rem;
        font-size: 1rem;
        height: 2.2rem;
        min-width: 110px;
        width: auto;
        display: inline-flex;
        align-items: center;
        transition: background 0.18s;
    }
    .stButton > button:hover,
    .stButton > button:active,
    .stButton > button:focus {
        background-color: #f4be19 !important;
        color: var(--text-color, #222) !important;
        outline: none;
    }
    @media (prefers-color-scheme: dark) {
        .stButton > button:hover,
        .stButton > button:active,
        .stButton > button:focus {
            background-color: #ffe066 !important;
            color: var(--text-color, #222) !important;
        }
    }
    /* Style for the form submit button (Search) */
    .stFormSubmitButton button {
        background-color: #fff !important;
        color: var(--text-color, #222) !important;
        border: 1px solid #222 !important;
        outline: none;
        transition: background 0.18s;
    }
    .stFormSubmitButton button:hover,
    .stFormSubmitButton button:active,
    .stFormSubmitButton button:focus {
        background-color: #f4be19 !important;
        color: var(--text-color, #222) !important;
        border: none;
        outline: none;
    }
    @media (prefers-color-scheme: dark) {
        .stFormSubmitButton button:hover,
        .stFormSubmitButton button:active,
        .stFormSubmitButton button:focus {
            background-color: #ffe066 !important;
            color: var(--text-color, #222) !important;
        }
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
    .stPageLinkButton {
        background: none !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 0.5em;
        margin-left: 0.5em;
        font-size: 1.05rem;
        color: #3366cc;
        font-weight: 400;
        text-decoration: none;
        transition: color 0.15s;
        cursor: pointer;
    }
    .stPageLinkButton:hover {
        color: #f7c825 !important;
        font-weight: 400;
        text-decoration: none;
    }
    .stPageLinkButton.selected, .stPageLinkButton[aria-current="page"] {
        color: #f7c825 !important;
        font-weight: bold !important;
        text-decoration: underline !important;
        background: none !important;
        box-shadow: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Top-right navigation links ---
# Remove custom HTML/CSS nav and related CSS

# --- Centered logo and title ---
# The logo is 1024x1024, so it will be sharp at 200x200.
logo_path = os.path.join(os.path.dirname(__file__), "frontend", "assets", "nobel_logo.png")
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
result_placeholder = st.empty()
with st.form("main_query_form", clear_on_submit=False):
    query = st.text_input(
        "Ask a question about Nobel Prize laureates...",
        value=st.session_state["query"],
        label_visibility="collapsed",
        key="main_query_input"
    )
    # Button aligned right using columns
    cols = st.columns([5, 1])
    with cols[1]:
        submit = st.form_submit_button("🔍 Search")

# --- Main query logic ---
if submit and query and "results_shown" not in st.session_state:
    with result_placeholder.container():
        with st.spinner("Analyzing Nobel archives..."):
            try:
                response = answer_query(query, model_id="BAAI/bge-large-en-v1.5")
                st.session_state.pop("answer", None)
                st.session_state.pop("sources", None)
                st.session_state["response"] = response
                st.session_state["results_shown"] = True
                # --- Analytics and query logging ---
                track_event("search_executed", {"query_length": len(query)})
                log_query(query, source="home")
            except Exception as e:
                st.error(f"Sorry, something went wrong. ({type(e).__name__}: {e})")
                # Optionally track errors
                track_event("error", {"type": str(type(e)), "msg": str(e)})

# --- Helper: Reset app state ---
def reset_app_state():
    st.session_state.clear()
    st.rerun()

# --- Helper: Render metadata (factual) answer card ---
def render_metadata_card(answer, metadata_answer):
    """Display a visually distinct card for factual/metadata answers."""
    laureate = metadata_answer.get("laureate")
    year = metadata_answer.get("year_awarded")
    country = metadata_answer.get("country")
    category = metadata_answer.get("category")
    motivation = metadata_answer.get("prize_motivation") or None

    # Remove motivation from the answer string if present
    answer_main = answer
    if motivation and "The laureate was recognized for:" in answer:
        answer_main = answer.split("The laureate was recognized for:")[0].strip()
        # Remove trailing punctuation or whitespace
        answer_main = answer_main.rstrip('. ')
        if answer_main:
            answer_main += "."

    flag = country_to_flag(country) if country else ""

    # Build the card lines
    lines = [
        f"<div style='font-size:1.1em; margin-bottom:0.3em;'>🔍 {answer_main}</div>",
    ]
    if motivation:
        lines.append(f"<div style='font-size:0.98em; color:#666; margin-bottom:0.3em;'>&ldquo;{motivation}&rdquo;</div>")
    if year:
        lines.append(f"<div style='margin-bottom:0.1em;'><strong>Year won:</strong> {year}</div>")
    if country:
        lines.append(f"<div style='margin-bottom:0.1em;'><strong>Country:</strong> {flag} {country}</div>")

    card_html = "\n".join(lines)

    st.markdown(
        f"""
        <div style='border-radius:12px; border:2px solid #e0e0e0; background:#f9f9f9; padding:1.2em 1.2em 1em 1.2em; margin-bottom:1em;'>
            {card_html}
        </div>
        """,
        unsafe_allow_html=True
    )

    # Clear button
    if st.button("Clear", key="clear_button"):
        reset_app_state()

# --- Show results ---
if st.session_state.get("results_shown"):
    response = st.session_state["response"]
    if response["answer_type"] == "metadata":
        metadata_answer = response.get("metadata_answer", {})
        render_metadata_card(response["answer"], metadata_answer)
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

        # Clear button (consistent with factual results)
        if st.button("Clear", key="clear_button_llm"):
            reset_app_state()

# --- Example prompts ---
if not st.session_state.get("results_shown"):
    st.markdown("#### Try asking")
    suggestions = [
        "In what year did Toni Morrison win the Nobel Prize?",
        "Who won the Nobel Prize in 1972?",
        "How do laureates describe the creative writing process?",
        "Draft a job acceptance email in the style of a Nobel Prize winner.",
        "What themes are most commonly expressed in Nobel lectures?",
    ]
    for i, prompt in enumerate(suggestions):
        prompt_with_emoji = f"✨ {prompt}"
        button_style = (
            "width: 100%; margin-top: 0.1em; margin-bottom: 0.1em; font-size: 1.08em; border-radius: 12px; "
            "text-align: left; padding-top: 0.2em; padding-bottom: 0.2em;"
        )
        if st.button(prompt_with_emoji, key=f"suggestion_{i}", help=None, type="secondary"):
            # Do NOT call reset_app_state() here; just set the prompt and trigger search
            st.session_state["query"] = prompt
            response = answer_query(prompt, model_id="BAAI/bge-large-en-v1.5")
            st.session_state["response"] = response
            st.session_state["results_shown"] = True
            # --- Analytics and query logging for suggestion button ---
            track_event("search_executed", {"query_length": len(prompt), "source": "suggestion"})
            log_query(prompt, source="suggestion")
            st.rerun()
        st.markdown(f"<style>div[data-testid='stButton'] > button{{ {button_style} }}</style>", unsafe_allow_html=True)

# --- Home button logic ---
query_params = st.query_params
if query_params.get("reset", [None])[0] == "1":
    reset_app_state()

# Optionally, in your nav.py or wherever you render the Home button, link to app.py?reset=1
