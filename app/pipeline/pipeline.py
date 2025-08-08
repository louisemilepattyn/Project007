# app/pipeline/pipeline.py
from pathlib import Path
from app.ml.ocr_doctr import pdf_to_tokens_ir
from app.ml.hf_table_transformer import add_hf_tables
from app.parsers.hf_table_to_rows import tables_to_lineitems
from app.io.schema import LineItem, ExtractionResult
from app.validators.accounting_rules import reconcile

def run_pipeline(pdf_path: Path) -> ExtractionResult:
    # 1) OCR tokens for all pages
    ir = pdf_to_tokens_ir(pdf_path)
    # 2) Detect table structure and build cell grid
    ir = add_hf_tables(ir, pdf_path)
    # 3) Convert tables → LineItems (heuristics for acc/name/amount/year)
    items = tables_to_lineitems(ir)
    # 4) Validate & return
    warnings = reconcile(items)
    return ExtractionResult(
        items=items,
        warnings=warnings,
        diagnostics={
            "flow": "huggingface+doctr",
            "n_pages": len(ir.pages),
            "n_items": len(items),
        }
    )
