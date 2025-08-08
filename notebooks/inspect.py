# %%
# Setup: imports + project path
import sys, pathlib, pandas as pd
from ipywidgets import Dropdown, Button, Checkbox, HBox, VBox, Output, Label
from IPython.display import display

# Ensure we can import from /app
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.pipeline.pipeline import run_pipeline
from app.io.export import to_csv_wide

DATA_DIR = PROJECT_ROOT / "Data"
assert DATA_DIR.exists(), f"Data folder not found: {DATA_DIR}"

# %%
# Widget: choose a PDF in /Data
def list_pdfs():
    return sorted([p for p in DATA_DIR.glob("*.pdf") if p.is_file()])

pdf_dd = Dropdown(options=list_pdfs(), description="PDF:", layout={"width":"80%"})
refresh_btn = Button(description="↻ Refresh", tooltip="Reload PDF list")
run_btn = Button(description="Run Extract", button_style="primary")
autosave_chk = Checkbox(value=True, description="Auto-save CSV next to PDF")
out = Output()

def on_refresh(_):
    pdf_dd.options = list_pdfs()

refresh_btn.on_click(on_refresh)

# %%
# Extraction callback + display
def run_extraction(_):
    out.clear_output()
    pdf_path = pathlib.Path(pdf_dd.value) if pdf_dd.value else None
    if not pdf_path or not pdf_path.exists():
        with out: 
            print("Select a valid PDF.")
        return

    with out:
        print(f"Running pipeline on: {pdf_path.name}")
        result = run_pipeline(pdf_path)

        # Convert to DataFrame (long)
        df_long = pd.DataFrame([i.model_dump() for i in result.items])
        if df_long.empty:
            print("No items extracted.")
            if result.warnings:
                print("Warnings:", *result.warnings, sep="\n- ")
            print("Diagnostics:", result.diagnostics)
            return

        # Pivot (wide) for quick valuation use
        required_cols = ["rekeningnummer", "postnaam", "fiscal_year", "amount"]
        missing_cols = [col for col in required_cols if col not in df_long.columns]
        
        if missing_cols:
            print(f"Missing required columns: {missing_cols}")
            print(f"Available columns: {list(df_long.columns)}")
            return
            
        wide = df_long.pivot_table(index=["rekeningnummer","postnaam"],
                                   columns="fiscal_year", values="amount",
                                   aggfunc="sum", fill_value=0).sort_index()

        print("\n— Extracted items (first 15 rows) —")
        display(df_long.head(15))

        print("\n— Pivot by year (first 15 rows) —")
        display(wide.head(15))

        # Save CSV if checked
        if autosave_chk.value:
            out_csv = pdf_path.with_suffix(".extracted.csv")
            wide.to_csv(out_csv, sep=";")
            print(f"\n[ok] Saved CSV → {out_csv}")

        if result.warnings:
            print("\n— Warnings —")
            for w in result.warnings:
                print("-", w)

        print("\n— Diagnostics —")
        print(result.diagnostics)

run_btn.on_click(run_extraction)

# %%
# UI
ui = VBox([
    HBox([Label("Choose PDF in Data/"), refresh_btn]),
    pdf_dd,
    HBox([run_btn, autosave_chk]),
    out
])
display(ui)

# %%
# Convenience: open the last written CSV for the selected PDF (if exists)
def open_existing_csv():
    pdf_path = pathlib.Path(pdf_dd.value) if pdf_dd.value else None
    if not pdf_path or not pdf_path.exists():
        print("Select a valid PDF above first.")
        return
    csv_path = pdf_path.with_suffix(".extracted.csv")
    if csv_path.exists():
        print(f"Opening existing CSV: {csv_path.name}")
        df = pd.read_csv(csv_path, sep=";")
        display(df.head(20))
    else:
        print("No CSV found yet. Run Extract first.")

# Call this cell manually after selection if you just want to peek:
# open_existing_csv()
