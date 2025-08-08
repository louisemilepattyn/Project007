# app/ir/schema.py
from pydantic import BaseModel
from typing import List, Optional, Tuple

BBox = Tuple[float, float, float, float]  # x0,y0,x1,y1 in page pixels

class Token(BaseModel):
    text: str
    x0: float; y0: float; x1: float; y1: float
    page: int

class TableCell(BaseModel):
    row: int
    col: int
    bbox: BBox
    page: int
    text: str = ""

class TableBlock(BaseModel):
    page: int
    bbox: BBox
    cells: List[TableCell]
    n_rows: int
    n_cols: int

class PageIR(BaseModel):
    page: int
    width: int
    height: int
    tokens: List[Token]
    tables: List[TableBlock]

class DocIR(BaseModel):
    pages: List[PageIR]
