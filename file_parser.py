# backend/file_parser.py

import io
import os
import sys
import docx
import pypdf
from bs4 import BeautifulSoup

from gemini_utils import structure_text_with_ai  # your AI structuring function


def _extract_text_from_docx_bytes(raw_bytes: bytes) -> str:
    doc = docx.Document(io.BytesIO(raw_bytes))
    return "\n".join(para.text for para in doc.paragraphs)


def _extract_text_from_pdf_bytes(raw_bytes: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
    texts = []
    for page in reader.pages:
        # some pages may return None
        txt = page.extract_text()
        if txt:
            texts.append(txt)
    return "\n".join(texts)


def parse_resume_file(source) -> dict:
    """
    Parses an uploaded resume (PDF or DOCX) into structured JSON via AI.

    Args:
      source: either a Flask FileStorage, any file-like with .read(),
              or a filesystem path string.

    Returns:
      {"parsedData": {...}} on success
      {"error": "..."} on failure
    """
    try:
        # --- 1) Load raw bytes exactly once ---
        if isinstance(source, str):
            # filesystem path
            raw_bytes = open(source, "rb").read()
            filename = os.path.basename(source)
        else:
            # FileStorage or file-like
            raw_bytes = source.read()
            filename = getattr(source, "filename", None) or ""

        # --- 2) Extract text based on extension ---
        lower = filename.lower()
        if lower.endswith(".docx"):
            raw_text = _extract_text_from_docx_bytes(raw_bytes)
        elif lower.endswith(".pdf"):
            raw_text = _extract_text_from_pdf_bytes(raw_bytes)
        else:
            return {"error": "Unsupported file type. Please upload a .docx or .pdf file."}

        if not raw_text.strip():
            return {"error": "Could not extract any text from the document."}

        # --- 3) Send to AI for structuring ---
        print("--- Successfully extracted text; sending to AI… ---")
        structured = structure_text_with_ai(raw_text)
        print("--- AI returned structured data. ---")

        return {"parsedData": structured}

    except Exception as e:
        # Log full traceback for debugging
        print(f"❗ Error in parse_resume_file: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()
        return {"error": f"An error occurred while parsing the file: {e}"}
