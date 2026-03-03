"""
Patent Analysis Tool — Data extraction, embedding & clustering, review & refine, white space (TBD).
Entry point: streamlit run app.py
"""

import streamlit as st

from state import init_session_state
from tab_clustering import render as render_clustering
from tab_extraction import render as render_extraction
from tab_review import render as render_review
from tab_whitespace import render as render_whitespace

st.set_page_config(page_title="Patent Analysis Tool", layout="wide")
init_session_state()

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Data Extraction",
    "2. Embedding & Clustering",
    "3. Review & Refine",
    "4. White Space Analysis",
])

with tab1:
    render_extraction()

with tab2:
    render_clustering()

with tab3:
    render_review()

with tab4:
    render_whitespace()
