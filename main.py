from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.status import *
from pathlib import Path
import shutil
import os
import datetime

app = FastAPI()

BASE_DIR = Path("storage")
BASE_DIR.mkdir(exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

def get_real_path(url_path: str) -> Path:
    return (BASE_DIR / url_path.lstrip("/")).resolve()

@app.put("/{file_path:path}")
async def upload_file(file_path: str, file: UploadFile = File(...)):
    dest = get_real_path(file_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"status": "uploaded"}

@app.get("/{file_path:path}")
async def get_file(file_path: str):
    real_path = get_real_path(file_path)
    if real_path.is_dir():
        files = [{"name": f.name, "is_dir": f.is_dir()} for f in real_path.iterdir()]
        return JSONResponse(content=files)
    if not real_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(real_path)

@app.head("/{file_path:path}")
async def get_file_info(file_path: str):
    real_path = get_real_path(file_path)
    if not real_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if real_path.is_file():
        stat = real_path.stat()
        headers = {
            "Content-Length": str(stat.st_size),
            "Last-Modified": datetime.datetime.utcfromtimestamp(stat.st_mtime).strftime('%a, %d %b %Y %H:%M:%S GMT')
        }
        return JSONResponse(content={}, headers=headers)
    raise HTTPException(status_code=400, detail="Not a file")

@app.delete("/{file_path:path}")
async def delete_path(file_path: str):
    real_path = get_real_path(file_path)
    if not real_path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    if real_path.is_dir():
        shutil.rmtree(real_path)
        return {"status": "directory deleted"}
    else:
        real_path.unlink()
        return {"status": "file deleted"}
