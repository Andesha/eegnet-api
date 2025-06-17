from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import uuid
import shutil
import mne
import mne

app: FastAPI = FastAPI()

router = APIRouter()

UPLOAD_DIR = Path("app/storage")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Root endpoint returning a hello world message.
@app.get("/", response_class=JSONResponse)
def read_root() -> dict[str, str]:
    """Root endpoint returning a hello world message."""
    return {"message": "Hello, world!"}

# Extract metadata from the raw object.
def extract_metadata(raw):
    return {
        "n_channels": raw.info["nchan"],
        "sfreq": raw.info["sfreq"],
        "duration_sec": raw.n_times / raw.info["sfreq"],
        "ch_names": raw.info["ch_names"],
        "meas_date": str(raw.info["meas_date"]),
    }

# Endpoint to return the info attribute of the MNE sample dataset.
@app.get("/mne-info", response_class=JSONResponse)
def get_mne_info() -> dict[str, str]:
    """Endpoint to return the info attribute of the MNE sample dataset."""

    fname = mne.datasets.sample.data_path() / 'MEG' / 'sample' /  'sample_audvis_raw.fif'
    raw = mne.io.read_raw_fif(fname, preload=True).pick('eeg')

    return {"message": extract_metadata(raw)}

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
