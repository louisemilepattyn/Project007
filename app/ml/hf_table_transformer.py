# app/ml/hf_table_transformer.py
from pathlib import Path
from typing import List, Tuple
import fitz  # PyMuPDF
import torch
from PIL import Image
from transformers import DetrFeatureExtractor, TableTransformerForObjectDetection
from app.ir.schema import DocIR, PageIR, TableBlock, TableCell

# Labels for structure-recognition model
LABELS = [
    "table", "table column", "table row", "table column header",
    "table projected row header", "table spanning cell"
]

_feature_extractor = None
_model = None

def _load_model():
    global _feature_extractor, _model
    if _model is None:
        _feature_extractor = DetrFeatureExtractor()  # auto works too; this is stable
        _model = TableTransformerForObjectDetection.from_pretrained(
            "microsoft/table-transformer-structure-recognition"
        )
        _model.eval()

def _predict_boxes(img: Image.Image) -> List[dict]:
    inputs = _feature_extractor(images=img, return_tensors="pt")
    with torch.no_grad():
        outputs = _model(**inputs)
    target_sizes = torch.tensor([img.size[::-1]])  # (h,w)
    results = _feature_extractor.post_process_object_detection(
        outputs, threshold=0.6, target_sizes=target_sizes
    )[0]
    preds = []
    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        preds.append({
            "label": LABELS[int(label)],
            "score": float(score),
            "box": tuple(box.tolist()),  # x0,y0,x1,y1
        })
    return preds

def _intersect(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    x0, y0 = max(ax0, bx0), max(ay0, by0)
    x1, y1 = min(ax1, bx1), min(ay1, by1)
    if x1 <= x0 or y1 <= y0:
        return None
    return (x0, y0, x1, y1)

def add_hf_tables(ir: DocIR, pdf_path: Path) -> DocIR:
    """
    For each page, detect table, row, column boxes and build a grid of cells (no text yet).
    """
    _load_model()
    doc = fitz.open(str(pdf_path))

    for page_ir in ir.pages:
        page = doc[page_ir.page]
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        preds = _predict_boxes(img)
        tables = [p for p in preds if p["label"] == "table"]
        rows   = [p for p in preds if p["label"] == "table row"]
        cols   = [p for p in preds if p["label"] == "table column"]

        page_tables: List[TableBlock] = []
        for t in tables:
            tbox = t["box"]
            # rows/cols that lie inside this table box
            t_rows = [r["box"] for r in rows if _intersect(r["box"], tbox)]
            t_cols = [c["box"] for c in cols if _intersect(c["box"], tbox)]
            # sort top-to-bottom / left-to-right
            t_rows = sorted(t_rows, key=lambda b: (b[1] + b[3]) / 2.0)
            t_cols = sorted(t_cols, key=lambda b: (b[0] + b[2]) / 2.0)

            cells: List[TableCell] = []
            for i, rbox in enumerate(t_rows):
                for j, cbox in enumerate(t_cols):
                    ib = _intersect(rbox, cbox)
                    if not ib:
                        # fallback small box within table if detection is imperfect
                        ib = _intersect(rbox, tbox) if _intersect(rbox, cbox) is None else None
                    if ib:
                        cells.append(TableCell(row=i, col=j, bbox=ib, page=page_ir.page))
            if cells:
                page_tables.append(TableBlock(
                    page=page_ir.page, bbox=tbox, cells=cells,
                    n_rows=len(t_rows), n_cols=len(t_cols)
                ))
        page_ir.tables = page_tables
    return ir
