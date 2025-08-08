# app/pipeline/pipeline.py
from pathlib import Path
from app.extractors.tables_camelot import extract_tables_camelot
from app.extractors.tables_pdfplumber import extract_tables_pdfplumber
from app.extractors.ocr_pytesseract import extract_ocr_blocks
from app.parsers.table_cleaners import normalize_tables, to_long_rows
from app.io.schema import LineItem, ExtractionResult
from app.validators.accounting_rules import reconcile

def run_pipeline(pdf_path: Path) -> ExtractionResult:
    tables = extract_tables_camelot(pdf_path)
    if not tables:
        tables = extract_tables_pdfplumber(pdf_path)
    if not tables:
        tables = extract_ocr_blocks(pdf_path)

    cleaned = normalize_tables(tables)
    rows = to_long_rows(cleaned)

    items = [LineItem(**r) for r in rows]
    warnings = reconcile(items)

    return ExtractionResult(items=items, warnings=warnings, diagnostics={"n_tables": len(tables)})
