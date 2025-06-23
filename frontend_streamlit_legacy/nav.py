import streamlit as st

def render_nav():
    """Render a minimal, right-aligned navigation bar using st.page_link."""
    cols = st.columns([8, 1, 1])  # More space on left, nav on right
    with cols[1]:
        st.page_link("app.py", label="Home")
    with cols[2]:
        st.page_link("pages/About.py", label="About") 