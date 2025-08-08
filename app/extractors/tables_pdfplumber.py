# app/extractors/tables_pdfplumber.py
import pdfplumber
from pathlib import Path

def extract_tables_pdfplumber(pdf_path: Path):
    """Fallback extraction using pdfplumber table detection."""
    dfs = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for t in tables:
                    dfs.append(t)
        return dfs
    except Exception as e:
        print(f"[pdfplumber] extraction failed: {e}")
        return []
