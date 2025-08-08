# app/io/schema.py
from pydantic import BaseModel
from decimal import Decimal
from typing import Optional

class LineItem(BaseModel):
    rekeningnummer: str
    postnaam: str
    amount: Decimal
    fiscal_year: int
    currency: Optional[str] = "EUR"
    source_page: Optional[int] = None
    confidence: Optional[float] = None

class ExtractionResult(BaseModel):
    items: list[LineItem]
    warnings: list[str]
    diagnostics: dict
