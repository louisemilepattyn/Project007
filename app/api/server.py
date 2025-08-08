# app/api/server.py
from fastapi import FastAPI, UploadFile
from app.pipeline.pipeline import run_pipeline
import tempfile
from pathlib import Path

app = FastAPI()

@app.post("/extract")
async def extract(file: UploadFile):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(await file.read())
        tmp.flush()
        result = run_pipeline(Path(tmp.name))
    return {"items": [i.model_dump() for i in result.items],
            "warnings": result.warnings}
