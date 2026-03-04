"""New Patent Grouping tab: match invention disclosure forms to existing clusters or suggest new cluster."""

import json
import os
from io import BytesIO

import pandas as pd
import streamlit as st

from config import DEFAULT_OPENAI_API_KEY
from data_utils import build_disclosure_text, get_disclosure_columns


def _cluster_summary_for_llm(cluster_names: dict) -> str:
    """Build a text summary of existing clusters (name + description) for the LLM."""
    lines = []
    for cid, info in sorted(cluster_names.items(), key=lambda x: x[0]):
        name = info.get("name", f"Cluster {cid}")
        desc = info.get("description", "")
        lines.append(f"- Cluster {cid} ({name}): {desc}")
    return "\n".join(lines) if lines else "(No clusters defined)"


def _assign_disclosure_to_cluster(
    disclosure_text: str,
    cluster_summary: str,
    openai_api_key: str,
) -> dict:
    """
    Call LLM to assign invention disclosure to an existing cluster or suggest a new cluster.
    Returns dict with: assigned_cluster_id (int or null), assigned_cluster_name (str or null),
    suggested_new_cluster (str or null), reasoning (str).
    """
    from openai import OpenAI

    client = OpenAI(api_key=openai_api_key)
    system = """You are an expert at matching inventions to patent clusters. You will be given:
1) A list of existing clusters, each with an ID, name, and short description.
2) An invention disclosure (title, industry, problem, summary, technical features, and value).

Your task: Determine if this invention fits within ONE of the existing clusters. If it clearly fits, return that cluster's ID and name. If it does not fit any existing cluster, suggest a new cluster name and short description.

Respond in JSON only with exactly these keys:
- "assigned_cluster_id": integer (0-based cluster ID) or null if no match
- "assigned_cluster_name": string (existing cluster name) or null
- "suggested_new_cluster": string (name for a new cluster) or null
- "suggested_new_description": string (1 sentence) or null
- "reasoning": string (1-2 sentences explaining your decision)

No other text in your response."""

    user = f"""Existing clusters:
{cluster_summary}

Invention disclosure:
{disclosure_text}

Return JSON only."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0,
    )
    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    return json.loads(content)


def render() -> None:
    st.header("New Patent Grouping")
    st.caption(
        "Upload an invention disclosure form (CSV). The LLM will match each invention to an existing cluster "
        "or suggest a new cluster based on key information columns."
    )

    cluster_names = st.session_state.get("cluster_names") or {}
    clustering_df = st.session_state.get("clustering_df")
    refined = st.session_state.get("refined_assignments")

    if not cluster_names or clustering_df is None or not refined:
        st.info(
            "Complete **Embedding & Clustering** and **Review & Refine** first (including generating cluster names) "
            "so existing clusters are available for matching."
        )
        return

    cluster_summary = _cluster_summary_for_llm(cluster_names)

    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        key="tab_new_grouping_api_key",
        value=DEFAULT_OPENAI_API_KEY,
        help="Required for LLM matching. Or set OPENAI_API_KEY in .env",
    )
    openai_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        st.warning("Enter an OpenAI API key to run matching.")

    csv_file = st.file_uploader(
        "Upload invention disclosure form (CSV)",
        type=["csv"],
        key="tab_new_grouping_csv",
    )
    if not csv_file:
        return

    df = pd.read_csv(csv_file)
    columns = get_disclosure_columns(df)
    title_col = columns.get("title")
    if not any(columns.values()):
        st.warning(
            "Could not detect key columns (title, summary, description). "
            "Ensure your CSV has columns like 'title', 'invention summary', 'description'."
        )
    else:
        #st.write("Detected columns:", {k: v for k, v in columns.items() if v})

    n_show = min(5, len(df))
    st.subheader("Preview")
    st.dataframe(df.head(n_show), use_container_width=True)

    if not st.button("Run cluster assignment", key="tab_new_grouping_run"):
        return

    if not openai_key:
        st.error("Please provide an OpenAI API key.")
        return

    results = []
    bar = st.progress(0)
    for i in range(len(df)):
        bar.progress((i + 1) / len(df), text=f"Assigning disclosure {i + 1}/{len(df)}...")
        row = df.iloc[i]
        disclosure_text = build_disclosure_text(row, columns)
        if not disclosure_text.strip():
            results.append({
                "row_index": i,
                "identifier": str(row.get(title_col, i)),
                "assigned_cluster_id": None,
                "assigned_cluster_name": None,
                "suggested_new_cluster": None,
                "suggested_new_description": None,
                "reasoning": "No key text found in row.",
            })
            continue
        try:
            out = _assign_disclosure_to_cluster(
                disclosure_text[:8000],
                cluster_summary,
                openai_key,
            )
            identifier = str(row.get(title_col, i)) if title_col else str(i)
            results.append({
                "row_index": i,
                "identifier": (identifier[:60] + "...") if len(identifier) > 60 else identifier,
                "assigned_cluster_id": out.get("assigned_cluster_id"),
                "assigned_cluster_name": out.get("assigned_cluster_name"),
                "suggested_new_cluster": out.get("suggested_new_cluster"),
                "suggested_new_description": out.get("suggested_new_description"),
                "reasoning": out.get("reasoning", ""),
            })
        except Exception as e:
            results.append({
                "row_index": i,
                "identifier": str(row.get(title_col, i)),
                "assigned_cluster_id": None,
                "assigned_cluster_name": None,
                "suggested_new_cluster": None,
                "suggested_new_description": None,
                "reasoning": f"Error: {e}",
            })
    bar.empty()

    result_df = pd.DataFrame(results)
    result_df["assignment"] = result_df.apply(
        lambda r: (
            f"Existing: {r['assigned_cluster_name']} (ID {r['assigned_cluster_id']})"
            if r["assigned_cluster_id"] is not None
            else f"New: {r['suggested_new_cluster'] or '—'}"
        ),
        axis=1,
    )
    st.success("Assignment complete.")
    st.dataframe(result_df, use_container_width=True)

    buf = BytesIO()
    result_df.to_csv(buf, index=False)
    buf.seek(0)
    st.download_button(
        "Download assignment results (CSV)",
        buf,
        file_name="disclosure_cluster_assignments.csv",
        mime="text/csv",
        key="tab_new_grouping_download",
    )
