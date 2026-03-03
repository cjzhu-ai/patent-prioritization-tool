"""Review & Refine tab: adjust cluster assignments, generate cluster names with GPT."""

import json
import os

import streamlit as st

from config import DEFAULT_OPENAI_API_KEY
from data_utils import get_patent_columns


def render() -> None:
    st.header("Review & Refine")
    df = st.session_state.clustering_df
    labels = st.session_state.cluster_labels

    if df is None or labels is None:
        st.info(
            "Run **Embedding & Clustering** first and upload a CSV, then run clustering."
        )
        return

    df = df.copy()
    df["cluster"] = labels
    n_clusters = int(labels.max()) + 1

    if st.session_state.refined_assignments is None:
        st.session_state.refined_assignments = (
            labels.tolist() if hasattr(labels, "tolist") else list(labels)
        )
    refined = st.session_state.refined_assignments

    columns = get_patent_columns(df)
    family_col = columns.get("family")
    title_col = columns.get("title")
    id_col = "patent_number" if "patent_number" in df.columns else df.columns[0]

    def _patent_label(idx: int) -> str:
        """Preferred: Patent Family; fallback: title; else id."""
        row = df.iloc[idx]
        if family_col and family_col in df.columns:
            val = row.get(family_col)
            if val is not None and str(val).strip():
                s = str(val).strip()
                return (s[:60] + "...") if len(s) > 60 else s
        if title_col and title_col in df.columns:
            val = row.get(title_col)
            if val is not None and str(val).strip():
                s = str(val).strip()
                return (s[:60] + "...") if len(s) > 60 else s
        return str(row.get(id_col, idx))

    st.subheader("Assign patents to clusters")
    st.caption(
        "Move patents between clusters using the dropdown; then confirm and generate cluster names."
    )

    clusters = {i: [] for i in range(n_clusters)}
    for idx in range(len(df)):
        cl = int(refined[idx])
        clusters[cl].append((idx, _patent_label(idx)))
    for c in range(n_clusters):
        with st.expander(f"Cluster {c} ({len(clusters[c])} patents)", expanded=True):
            for idx, label in clusters[c]:
                new_c = st.selectbox(
                    label,
                    range(n_clusters),
                    index=int(refined[idx]),
                    key=f"refine_{idx}",
                )
                st.session_state.refined_assignments[idx] = new_c

    st.write(
        "**Generate cluster names:** Enter your OpenAI API key below, then click the button."
    )
    api_key_t3 = st.text_input(
        "OpenAI API Key",
        type="password",
        key="tab3_api_key",
        value=DEFAULT_OPENAI_API_KEY,
        help="Or set OPENAI_API_KEY in .env",
    )

    if st.button("Confirm grouping and generate cluster names"):
        refined = st.session_state.refined_assignments
        clusters_final = {i: [] for i in range(n_clusters)}
        for idx in range(len(df)):
            c = int(refined[idx]) if idx < len(refined) else 0
            clusters_final[c].append(idx)

        openai_key = api_key_t3 or os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            st.error(
                "Provide an OpenAI API key above (or set OPENAI_API_KEY in .env) to generate cluster names."
            )
            return

        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
        except Exception as e:
            st.error(str(e))
            return

        names = {}
        for c, indices in clusters_final.items():
            if not indices:
                names[c] = {"name": f"Cluster {c}", "description": "No patents."}
                continue
            texts = [df.iloc[i]["_composite_text"][:2000] for i in indices]
            combined = "\n\n---\n\n".join(texts[:10])
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert at summarizing patent groups. For each group of patents, "
                            'output a short cluster name (a few words) and a 1–2 sentence description. '
                            'Reply in JSON: {"name": "...", "description": "..."}'
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Patents in this cluster (excerpts):\n\n{combined}\n\nGive a name and short description for this cluster.",
                    },
                ],
                temperature=0,
            )
            content = resp.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            names[c] = json.loads(content)

        st.session_state.cluster_names = names
        st.success("Cluster names generated.")
        for c, v in names.items():
            st.markdown(
                f"**Cluster {c}: {v.get('name', 'N/A')}** — {v.get('description', '')}"
            )
