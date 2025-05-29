import streamlit as st

def render_nav():
    """Render a minimal, right-aligned navigation bar using st.page_link."""
    cols = st.columns([8, 1, 1])  # More space on left, nav on right
    with cols[1]:
        st.markdown("""
        <div class='top-nav'>
            <a href='app.py?reset=1' class='stPageLinkButton'>Home</a>
        </div>
        """, unsafe_allow_html=True)
    with cols[2]:
        st.page_link("pages/About.py", label="About") 