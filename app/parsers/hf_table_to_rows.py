# app/parsers/hf_table_to_rows.py
import re
import pandas as pd
from typing import List, Dict, Tuple
from app.ir.schema import DocIR, TableBlock, TableCell, Token
from app.io.schema import LineItem

RE_ACC = re.compile(r"^\d{4,8}$")
RE_YEAR = re.compile(r"\b(19|20)\d{2}\b")
RE_NUM = re.compile(r"[-–—]?\s*\(?\s*[\d\s.\u00A0’']+(?:[.,]\d{1,2})?\s*\)?$")

def _inside(cell: TableCell, tok: Token) -> bool:
    x0,y0,x1,y1 = cell.bbox
    cx = (tok.x0 + tok.x1) / 2.0
    cy = (tok.y0 + tok.y1) / 2.0
    return (x0 <= cx <= x1) and (y0 <= cy <= y1)

def _join_tokens_text(tokens: List[Token]) -> str:
    return " ".join(t.text for t in sorted(tokens, key=lambda t: (t.y0, t.x0)))

def _normalize_number(tok: str) -> float | None:
    s = tok
    s = s.replace("\u00A0"," ").replace("’","").replace("'","")
    s = s.replace("€","").replace("EUR","").replace("eur","")
    s = s.strip()
    neg = False
    if "(" in s and ")" in s:
        neg = True
        s = s.replace("(","").replace(")","")
    s = s.lstrip("–—-").strip()
    # both dot & comma → '.' thousands, ',' decimal
    if "," in s and "." in s:
        s = s.replace(".","").replace(",",".")
    else:
        # single comma as decimal
        if s.count(",")==1 and len(s.split(",")[-1]) in (1,2):
            s = s.replace(",",".")
        else:
            s = s.replace(" ","").replace(".","")
    try:
        val = float(s)
        return -val if neg else val
    except ValueError:
        return None

def _header_years_from_top_row(df: pd.DataFrame) -> Dict[int,int]:
    """
    Look for years in top 2 rows to map columns -> fiscal_year.
    Return dict col_index -> year.
    """
    mapping = {}
    for r in range(min(2, len(df))):
        for c in range(df.shape[1]):
            m = RE_YEAR.search(str(df.iat[r,c]))
            if m:
                mapping[c] = int(m.group(0))
    return mapping

def _best_amount_col_idx(df: pd.DataFrame) -> int | None:
    """
    If no year headers, pick the right-most column with most numeric-looking cells.
    """
    best = None; best_score = -1
    for c in range(df.shape[1]-1, -1, -1):
        col = df.iloc[:,c].astype(str)
        score = sum(bool(RE_NUM.search(x)) for x in col)
        if score > best_score:
            best_score = score; best = c
    return best

def tables_to_lineitems(ir: DocIR) -> List[LineItem]:
    items: List[LineItem] = []

    for page in ir.pages:
        # 1) Fill cell text from OCR tokens
        for tb in page.tables:
            # assign tokens to each cell
            for cell in tb.cells:
                tokens = [tok for tok in page.tokens if _inside(cell, tok)]
                cell.text = _join_tokens_text(tokens)

            # 2) Build a DataFrame view of the table
            n_rows = tb.n_rows; n_cols = tb.n_cols
            grid = [["" for _ in range(n_cols)] for _ in range(n_rows)]
            for cell in tb.cells:
                if 0 <= cell.row < n_rows and 0 <= cell.col < n_cols:
                    grid[cell.row][cell.col] = cell.text.strip()
            df = pd.DataFrame(grid)

            # 3) Map columns: try year headers; else pick numeric right-most
            col_to_year = _header_years_from_top_row(df)
            amount_cols: List[Tuple[int,int|None]] = []  # (col_idx, year or None)

            if col_to_year:
                for c, y in sorted(col_to_year.items()):
                    amount_cols.append((c, y))
            else:
                c = _best_amount_col_idx(df)
                if c is not None:
                    amount_cols.append((c, None))

            # 4) Identify account + name columns
            # heuristic: first column with many acc numbers is acc; the adjacent leftmost text is name
            acc_col = None
            best_hits = -1
            for c in range(df.shape[1]):
                hits = sum(bool(RE_ACC.match(str(x).strip())) for x in df.iloc[:,c])
                if hits > best_hits and hits > 1:
                    best_hits = hits; acc_col = c

            # name col: choose the leftmost non-acc col among first two columns
            name_col = 0 if acc_col != 0 else (1 if df.shape[1] > 1 else 0)

            # 5) Iterate data rows (skip header rows)
            start_row = 1  # skip first row (likely header)
            for r in range(start_row, df.shape[0]):
                acc = str(df.iat[r, acc_col]).strip() if acc_col is not None else ""
                if not RE_ACC.match(acc):
                    continue
                name = str(df.iat[r, name_col]).strip() if name_col is not None else ""

                # For each amount column, emit one item
                row_text_all = " ".join(str(x) for x in df.iloc[r,:].tolist())
                # if looks like “total/subtotal” skip
                if re.search(r"(total|totaal|subtotal|som|saldo|grand total)", row_text_all, flags=re.I):
                    continue

                for c, year in amount_cols:
                    raw = str(df.iat[r, c]).strip()
                    if not raw or not RE_NUM.search(raw):
                        continue
                    amt = _normalize_number(raw)
                    if amt is None:
                        continue

                    fy = year
                    if fy is None:
                        # try infer from any year token in the row
                        m = RE_YEAR.search(row_text_all)
                        fy = int(m.group(0)) if m else 0

                    items.append(LineItem(
                        rekeningnummer=acc, postnaam=name, amount=amt,
                        fiscal_year=int(fy) if fy else 0, currency="EUR",
                        source_page=page.page, confidence=0.75
                    ))
    return items
