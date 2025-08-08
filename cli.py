# cli.py
import sys
import pathlib
from app.pipeline.pipeline import run_pipeline
from app.io.export import to_csv_wide

def main():
    if len(sys.argv) < 2:
        print("Usage: python cli.py <file.pdf>")
        sys.exit(1)

    pdf_path = pathlib.Path(sys.argv[1])
    result = run_pipeline(pdf_path)

    out_csv = pdf_path.with_suffix('.extracted.csv')
    to_csv_wide(result.items, out_csv)
    print(f"[ok] Wrote {out_csv}")

if __name__ == "__main__":
    main()
