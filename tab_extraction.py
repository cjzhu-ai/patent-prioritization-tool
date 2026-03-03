"""Data Extraction tab: upload PDFs, extract with GPT, download CSV."""

import os
from io import BytesIO

import pandas as pd
import streamlit as st

from config import DEFAULT_OPENAI_API_KEY
from patent_extraction import extract_patent_with_gpt, extract_text_from_pdf


def render() -> None:
    st.header("Data Extraction")
    st.caption(
        "Upload patent PDFs. GPT will extract abstract, embodiment, and independent claims. "
        "Scanned PDFs are supported via OCR (requires Tesseract: e.g. `brew install tesseract` on Mac)."
    )
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        key="tab1_api_key",
        value=DEFAULT_OPENAI_API_KEY,
        help="Required for GPT extraction. Or set OPENAI_API_KEY in .env",
    )
    claim_numbers_str = st.text_input(
        "Independent claim numbers (optional)",
        placeholder="e.g. 1, 5, 10",
        key="tab1_claim_numbers",
        help="Comma-separated claim numbers that are independent. Improves extraction accuracy.",
    )
    pdf_files = st.file_uploader("Upload patent PDF(s)", type=["pdf"], accept_multiple_files=True)

    if not pdf_files or not st.button("Extract from PDFs"):
        return

    openai_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        st.error("Please provide an OpenAI API key or set OPENAI_API_KEY.")
        return

    independent_claim_numbers = None
    if claim_numbers_str.strip():
        try:
            independent_claim_numbers = [
                int(x.strip()) for x in claim_numbers_str.split(",") if x.strip()
            ]
        except ValueError:
            st.error(
                "Independent claim numbers must be integers separated by commas (e.g. 1, 5, 10)."
            )
            return

    results = []
    bar = st.progress(0)
    for i, f in enumerate(pdf_files):
        bar.progress((i + 1) / len(pdf_files), text=f"Processing {f.name}...")
        try:
            pdf_bytes = BytesIO(f.read())
            text = extract_text_from_pdf(pdf_bytes)
            if not text.strip():
                st.warning(f"No text extracted from {f.name}. Skipping.")
                continue
            out = extract_patent_with_gpt(
                text, openai_key, independent_claim_numbers=independent_claim_numbers
            )
            out["source_file"] = f.name
            results.append(out)
        except Exception as e:
            st.error(f"Error processing {f.name}: {e}")
    bar.empty()

    if not results:
        st.info("No patents extracted.")
        return

    df = pd.DataFrame(results)
    cols = ["patent_number", "patent_title", "abstract", "embodiment", "claims", "source_file"]
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    df = df[[c for c in cols if c in df.columns]]
    st.session_state.extraction_results = df.to_dict("records")
    st.success(f"Extracted {len(df)} patent(s).")
    st.dataframe(df, use_container_width=True)
    buf = BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    st.download_button(
        "Download CSV", buf, file_name="patent_extraction.csv", mime="text/csv"
    )
