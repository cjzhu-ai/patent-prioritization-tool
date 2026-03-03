# Patent Analysis Tool

A multi-tab Streamlit app for patent PDF extraction, embedding, clustering, and review.

## Setup

```bash
pip install -r requirements.txt
```

For **scanned/image-only PDFs**, install Tesseract OCR so the app can extract text:

- **macOS:** `brew install tesseract`
- **Windows:** [Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki)
- **Linux:** `sudo apt install tesseract-ocr` (or equivalent)

Create a `.env` file with your OpenAI API key (for GPT extraction and cluster naming):

```
OPENAI_API_KEY=your_key_here
```

## Run

```bash
streamlit run app.py
```

## Project structure

- **app.py** – Entry point; sets up tabs and delegates to tab modules.
- **config.py** – Config (e.g. `DEFAULT_OPENAI_API_KEY`, `EMBEDDING_MODEL`) and `load_dotenv`.
- **state.py** – Session state initialization for Streamlit.
- **patent_extraction.py** – PDF text extraction (pypdf, pdfplumber, OCR) and GPT parsing.
- **data_utils.py** – CSV helpers: column detection, composite text building, row labels.
- **clustering.py** – Embedding and agglomerative clustering (no UI).
- **tab_extraction.py** – Data Extraction tab UI.
- **tab_clustering.py** – Embedding & Clustering tab UI.
- **tab_review.py** – Review & Refine tab UI.
- **tab_whitespace.py** – White Space Analysis tab (placeholder).

## Tabs

1. **Data Extraction** – Upload USPTO-style patent PDFs; GPT extracts abstract, embodiment, and independent claims; download results as CSV.
2. **Embedding & Clustering** – Upload CSV, preview data, build composite text, run embeddings (all-mpnet-base-v2) and agglomerative clustering; adjust number of clusters and see performance summary.
3. **Review & Refine** – Review cluster assignments, move patents between clusters, then run GPT to name and describe clusters.
4. **White Space Analysis** – Placeholder (TBD).
# patent-prioritization-tool
