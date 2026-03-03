"""Patent PDF text extraction and GPT-based parsing."""

import os
from typing import List, Optional

from pypdf import PdfReader


EXTRACTION_SYSTEM = """You are a precise patent pdf parser. Your goal is to extract abstract, embodiment, and independent claims from the pdf I shared with you.

Rules:
- If a section or field is not found in the text, output an empty string "".
- For independent claims: I will let you know the numbers of the independent claims. extract EVERY independent claim in full. Independent claims stand alone and do not reference any other claim (e.g. they do not start with "The method of claim 1" or "The system of claim 2"). Dependent claims typically reference another claim and must be excluded. Scan the entire claims section and include every independent claim, preserving numbering and full text. Merge all independent claims into one text block.
- For Embodiment: the section typically starts after "Description of embodiments of the invention", "Detailed description", or "DETAILED DESCRIPTION". You must extract the complete embodiment section: include ALL text from the start of that section until the next major section begins (e.g. "Claims", "What is claimed is", "Brief description of the drawings"). Important: Summarize the embodiment to ~500 words.
- For Abstract: the official abstract paragraph(s), keep original text without adding or omitting anything.

Also extract:
- patent_number: The patent application or publication number, usually found in the abstract page close to title, and typicallystarts with "US" (e.g. US 10,123,456 B2 or US 2020/0123456 A1). If not found use "".
- patent_title: The full title of the patent. If not found use "".

Respond in JSON only with exactly these keys: patent_number, patent_title, abstract, embodiment, claims
Use "claims" as the key for the merged independent claims text. No other text in your response."""


def _extract_with_pypdf(pdf_file) -> str:
    """Extract text using pypdf."""
    pdf_file.seek(0)
    reader = PdfReader(pdf_file)
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def _extract_with_pdfplumber(pdf_file) -> str:
    """Extract text using pdfplumber (fallback when pypdf returns little/no text)."""
    import pdfplumber
    pdf_file.seek(0)
    parts = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
    return "\n\n".join(parts)


def _extract_with_ocr(pdf_file) -> str:
    """Extract text via OCR (for scanned or image-based PDFs). Renders each page to image, then runs Tesseract."""
    import fitz  # PyMuPDF
    import pytesseract
    from PIL import Image

    pdf_file.seek(0)
    pdf_bytes = pdf_file.read()
    parts = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Render at 200 DPI for better OCR accuracy
            pix = page.get_pixmap(dpi=200, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img)
            if text and text.strip():
                parts.append(text.strip())
    finally:
        doc.close()
    return "\n\n".join(parts)


def extract_text_from_pdf(pdf_file) -> str:
    """Extract raw text from a PDF file. Tries pypdf → pdfplumber → OCR if needed."""
    text = _extract_with_pypdf(pdf_file)
    if not text or len(text.strip()) < 50:
        text = _extract_with_pdfplumber(pdf_file)
    if not text or len(text.strip()) < 50:
        try:
            text = _extract_with_ocr(pdf_file)
        except Exception as e:
            raise RuntimeError(
                "Text extraction and OCR failed. For OCR, install Tesseract (e.g. on Mac: "
                "brew install tesseract). Original error: " + str(e)
            ) from e
    return text or ""


def extract_patent_with_gpt(
    text: str,
    openai_api_key: str,
    independent_claim_numbers: Optional[List[int]] = None,
) -> dict:
    """Call GPT to parse patent text and return structured fields.
    independent_claim_numbers: optional list of claim numbers that are independent (e.g. [1, 5, 10]).
    When provided, GPT will extract only those claims for better accuracy."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_api_key or os.environ.get("OPENAI_API_KEY"))
    except Exception as e:
        raise RuntimeError(f"OpenAI client failed: {e}. Set OPENAI_API_KEY in .env or in the app.") from e

    # Truncate if too long (e.g. 120k chars for 4k context window with response)
    max_chars = 100_000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[... text truncated for API ...]"

    user_content = f"Extract from this patent text:\n\n{text}"
    if independent_claim_numbers:
        nums = ", ".join(str(n) for n in independent_claim_numbers)
        user_content = (
            f"The independent claims are numbered: {nums}. "
            "Extract ONLY those claims in full (preserve numbering and full text). "
            "Do not include dependent claims.\n\n"
            + user_content
        )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM},
            {"role": "user", "content": user_content},
        ],
        temperature=0,
    )
    import json
    content = response.choices[0].message.content.strip()
    # Handle markdown code blocks if present
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    return json.loads(content)
