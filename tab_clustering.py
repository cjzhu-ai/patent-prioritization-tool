"""Embedding & Clustering tab: upload CSV, build composite text, run embedding and clustering."""

import pandas as pd
import streamlit as st

from clustering import run_clustering, run_embedding
from data_utils import build_composite_text, get_patent_columns, row_label_by_title


def render() -> None:
    st.header("Embedding & Clustering")
    st.caption(
        "Upload a CSV with patent key info, build composite text, then run embedding and clustering."
    )
    csv_file = st.file_uploader("Upload patent CSV", type=["csv"], key="tab2_csv")
    preview_all = st.checkbox(
        "Preview all rows (otherwise first 5)", value=False, key="tab2_preview_all"
    )

    if not csv_file:
        return

    df = pd.read_csv(csv_file)
    n_show = len(df) if preview_all else min(5, len(df))
    st.subheader("Data preview")
    st.dataframe(df.head(n_show), use_container_width=True)

    columns = get_patent_columns(df)
    col_abstract = columns["abstract"]
    col_embodiment = columns["embodiment"]
    col_claims = columns["claims"]
    col_title = columns["title"]
    col_family = columns.get("family")
    if not all([col_abstract, col_embodiment, col_claims, col_title]):
        st.warning(
            "Could not find all columns. Using: "
            f"abstract={col_abstract}, embodiment={col_embodiment}, claims={col_claims}, title={col_title}. "
            "Rename CSV columns if needed."
        )

    df = build_composite_text(df, columns)
    st.session_state.clustering_df = df
    st.session_state.composite_texts = dict(zip(df.index, df["_composite_text"]))

    # Use Patent Family for preview selector if present, else fall back to title
    preview_col = col_family if col_family else col_title
    st.subheader("Composite text preview")
    idx_choice = st.selectbox(
        "Select by patent family to preview composite text",
        range(len(df)),
        format_func=lambda i: row_label_by_title(df, i, preview_col),
    )
    if idx_choice is not None:
        st.text_area("Composite text", value=df.iloc[idx_choice]["_composite_text"], height=200)

    n_clusters = st.slider(
        "Number of clusters",
        min_value=2,
        max_value=min(20, max(2, len(df) - 1)),
        value=5,
        key="tab2_n_clusters",
    )
    if st.button("Run embedding and clustering"):
        texts = df["_composite_text"].fillna("").tolist()
        with st.spinner("Loading model and computing embeddings..."):
            emb = run_embedding(texts)
        st.session_state.embeddings = emb
        with st.spinner("Clustering..."):
            labels, sil = run_clustering(emb, n_clusters)
        st.session_state.cluster_labels = labels
        st.session_state.refined_assignments = labels.tolist()
        df["cluster"] = labels
        st.session_state.clustering_df = df
        st.metric("Silhouette score", f"{sil:.4f}")
        st.success(
            "Clustering done. Go to **Review & Refine** to adjust groups and name clusters."
        )

    # Performance summary when we have results
    if st.session_state.cluster_labels is not None and st.session_state.clustering_df is not None:
        from sklearn.metrics import silhouette_score
        sil = silhouette_score(
            st.session_state.embeddings, st.session_state.cluster_labels
        )
        st.subheader("Model performance summary")
        st.write(f"Silhouette score: **{sil:.4f}** (higher = better separation).")
