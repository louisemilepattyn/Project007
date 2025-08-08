# app/extractors/ocr_pytesseract.py
from pathlib import Path
import pdfplumber
import pytesseract
import pandas as pd

def extract_ocr_blocks(pdf_path: Path):
    """Last-resort OCR extraction."""
    dfs = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                img = page.to_image(resolution=300).original
                text = pytesseract.image_to_string(img)
                lines = [line.split() for line in text.split("\n") if line.strip()]
                if lines:
                    dfs.append(pd.DataFrame(lines))
        return dfs
    except Exception as e:
        print(f"[ocr] extraction failed: {e}")
        return []
