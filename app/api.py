from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import uuid
import shutil
import mne

UPLOAD_DIR = Path("app/storage")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()

def extract_metadata(raw):
    return {
        "n_channels": raw.info["nchan"],
        "sfreq": raw.info["sfreq"],
        "duration_sec": raw.n_times / raw.info["sfreq"],
        "ch_names": raw.info["ch_names"],
        "meas_date": str(raw.info["meas_date"]),
    }

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    # Save to disk
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Attempt loading via MNE (basic check)
    try:
        raw = mne.io.read_raw(file_path, preload=False)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file with MNE: {e}")

    return {"message": "File uploaded successfully", "file_id": file_id, "filename": file.filename}

@router.get("/metadata/{file_id}")
def get_metadata(file_id: str):
    # Find matching file
    matches = list(UPLOAD_DIR.glob(f"{file_id}_*"))
    if not matches:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = matches[0]
    try:
        raw = mne.io.read_raw(file_path, preload=False)
        metadata = extract_metadata(raw)
        return JSONResponse(content=metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {e}")
