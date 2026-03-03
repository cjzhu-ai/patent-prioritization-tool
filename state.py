"""Streamlit session state initialization."""

import streamlit as st


def init_session_state() -> None:
    """Initialize all session state keys used across tabs."""
    defaults = {
        "extraction_results": [],
        "clustering_df": None,
        "composite_texts": {},
        "embeddings": None,
        "cluster_labels": None,
        "refined_assignments": None,  # list of int (cluster id per row)
        "cluster_names": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
