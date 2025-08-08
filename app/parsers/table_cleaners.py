# app/parsers/table_cleaners.py
import pandas as pd
import re

HEADER_KEYWORDS = ["totaal", "som", "subtotal", "rubriek", "sectie", "saldo"]

def normalize_tables(tables):
    """Clean tables: strip headers, normalize numbers."""
    cleaned = []
    for df in tables:
        pdf = pd.DataFrame(df)
        pdf = pdf.applymap(lambda x: str(x).strip() if x is not None else "")
        cleaned.append(pdf)
    return cleaned

def to_long_rows(tables):
    """Convert cleaned tables into dicts of (acc, name, amount, year, page)."""
    rows = []
    for df in tables:
        for _, row in df.iterrows():
            text_row = [str(c).strip() for c in row if c]
            if not text_row:
                continue
            acc_match = next((c for c in text_row if re.fullmatch(r"\d{4,8}", c)), None)
            if acc_match:
                name = next((c for c in text_row if c != acc_match), "")
                amount = _extract_amount(text_row)
                year = _extract_year(text_row)
                if amount is not None:
                    rows.append({
                        "rekeningnummer": acc_match,
                        "postnaam": name,
                        "amount": amount,
                        "fiscal_year": year,
                        "confidence": 0.85
                    })
    return rows

def _extract_amount(cells):
    for c in cells[::-1]:
        c_clean = c.replace(".", "").replace(",", ".")
        try:
            return float(c_clean)
        except ValueError:
            continue
    return None

def _extract_year(cells):
    for c in cells:
        if re.fullmatch(r"20\d{2}", c):
            return int(c)
    return 0
