# app/io/export.py
import pandas as pd
from pathlib import Path
from .schema import LineItem

def to_csv_wide(items: list[LineItem], out_path: Path):
    df = pd.DataFrame([i.model_dump() for i in items])
    wide = df.pivot_table(index=["rekeningnummer", "postnaam"], 
                          columns="fiscal_year", values="amount", fill_value=0)
    wide.to_csv(out_path, sep=";")
