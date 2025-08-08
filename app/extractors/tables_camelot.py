# app/extractors/tables_camelot.py
import camelot
from pathlib import Path

def extract_tables_camelot(pdf_path: Path):
    """Try extracting tables using Camelot stream mode first."""
    try:
        tables = camelot.read_pdf(str(pdf_path), flavor="stream", pages="all")
        return [t.df for t in tables]
    except Exception as e:
        print(f"[camelot] extraction failed: {e}")
        return []
