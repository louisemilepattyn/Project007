# app/ml/ocr_doctr.py
from pathlib import Path
from typing import List
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from app.ir.schema import DocIR, PageIR, Token

# Single global model to avoid reload per page
_model = None

def _get_model():
    global _model
    if _model is None:
        _model = ocr_predictor(pretrained=True)  # PyTorch backend
        _model.eval()
    return _model

def pdf_to_tokens_ir(pdf_path: Path) -> DocIR:
    """
    OCR each page once; return tokens with absolute pixel coords.
    """
    doc = DocumentFile.from_pdf(str(pdf_path))
    model = _get_model()
    result = model(doc)

    pages: List[PageIR] = []
    for p_idx, page in enumerate(result.pages):
        width, height = page.dimensions  # pixels
        tokens: List[Token] = []
        for block in page.blocks:
            for line in block.lines:
                for word in line.words:
                    # geometry is relative (x0,y0,x1,y1) in 0..1
                    geometry = word.geometry
                    if len(geometry) != 4:
                        print(f"Warning: word.geometry has {len(geometry)} values, expected 4. Values: {geometry}")
                        continue
                    (rx0, ry0, rx1, ry1) = geometry
                    x0, y0 = rx0 * width, ry0 * height
                    x1, y1 = rx1 * width, ry1 * height
                    tokens.append(Token(text=word.value, x0=x0, y0=y0, x1=x1, y1=y1, page=p_idx))
        pages.append(PageIR(page=p_idx, width=width, height=height, tokens=tokens, tables=[]))
    return DocIR(pages=pages)
