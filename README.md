# Patent Analysis Tool

A web app to organize and analyze patents: extract key information from PDFs, group similar patents into clusters, and match new invention disclosures to those groups.

**No coding required** — you work through tabs in your browser and upload files or paste an API key when asked.

---

## What you need before starting

- **Python** installed on your computer (version 3.9 or newer). If you’re not sure, ask your IT team or follow [python.org/downloads](https://www.python.org/downloads/).
- An **OpenAI API key** (used so the app can call GPT for extraction and naming). You get this from [platform.openai.com](https://platform.openai.com/) after creating an account. The app will ask for it in the relevant tabs; you can also put it in a `.env` file (see below) so you don’t have to type it every time.
- **Optional:** For **scanned PDFs** (image-only, no selectable text), install **Tesseract** so the app can read the text:
  - **Mac:** Install Homebrew if needed, then in Terminal run: `brew install tesseract`
  - **Windows:** Download the installer from [Tesseract for Windows](https://github.com/UB-Mannheim/tesseract/wiki)
  - **Linux:** Run: `sudo apt install tesseract-ocr` (or your package manager’s equivalent)

---

## How to open the app

1. **Open Terminal** (Mac/Linux) or **Command Prompt** / **PowerShell** (Windows).
2. **Go to the project folder** — the folder that contains `app.py`. For example:
   ```text
   cd path/to/patent-prioritization-tool-v2
   ```
   (Replace `path/to/` with the real location on your computer.)
3. **Install dependencies** (only needed the first time):
   ```text
   pip install -r requirements.txt
   ```
4. **Start the app:**
   ```text
   streamlit run app.py
   ```
5. Your browser should open automatically to a local address (e.g. `http://localhost:8501`). If it doesn’t, copy the link shown in the terminal and paste it into your browser.

You can close the app by pressing `Ctrl+C` in the terminal.

---

## What each tab does

You work **left to right** across the tabs. Later tabs use results from earlier ones.

1. **Data Extraction**  
   Upload patent PDFs (e.g. USPTO style). The app extracts **abstract**, **embodiment**, and **independent claims** and lets you **download a spreadsheet (CSV)**. You can optionally enter which claim numbers are independent to improve accuracy. Scanned PDFs are supported if Tesseract is installed.

2. **Embedding & Clustering**  
   Upload the spreadsheet from step 1 (or any CSV with patent abstract, embodiment, claims, and title). The app groups similar patents into **clusters**. You can change how many clusters you want and see a short quality score (Silhouette score). You can also preview the combined text used for each patent.

3. **Review & Refine**  
   Review the automatic groupings. You can **move patents between clusters** with dropdowns. When you’re happy, you can **generate short names and descriptions** for each cluster (using GPT) so they’re easy to understand.

4. **New Patent Grouping**  
   Upload a **spreadsheet of invention disclosure forms** (e.g. from an internal form). The app uses the key columns (e.g. title, summary, description) to decide whether each invention fits an **existing cluster** or should start a **new cluster**, and you can download the results as a CSV.

5. **White Space Analysis**  
   Reserved for future features (e.g. competitor landscape and prioritization). Currently a placeholder.

---

## Saving your API key (optional)

If you don’t want to type your OpenAI API key every time:

1. In the project folder, create a file named **`.env`** (with the dot at the start).
2. Put this line in the file (use your real key):
   ```text
   OPENAI_API_KEY=your_key_here
   ```
3. Save the file. The app will read this when it runs. **Do not share this file or commit it to a shared drive** — treat it like a password.

---

## Troubleshooting

- **“No text extracted from PDF”** — The PDF might be image-only. Install Tesseract (see “What you need before starting”) and try again. If the PDF is unusual, extraction may still fail.
- **“Please provide an OpenAI API key”** — Enter your key in the box on the tab you’re using, or add it to a `.env` file as above.
- **App won’t start** — Make sure you’re in the correct folder (the one that contains `app.py`) and that you ran `pip install -r requirements.txt` once.
- **Clustering or New Patent Grouping says to complete earlier steps** — Run the **Embedding & Clustering** tab first, then **Review & Refine** and generate cluster names, so the app has clusters to use.

---

## For developers

- **Run:** `streamlit run app.py`
- **Project layout:** `app.py` is the entry point; each tab has its own module under `tab_*.py`. Shared logic lives in `data_utils.py`, `clustering.py`, and `patent_extraction.py`. Config and session state are in `config.py` and `state.py`.
