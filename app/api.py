from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pathlib import Path
import uuid
import shutil
import mne
import json
import asyncio
from fastapi.websockets import WebSocket, WebSocketDisconnect
from io import BytesIO

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

@router.websocket("/ws/stream/{file_id}")
async def stream_eeg(websocket: WebSocket, file_id: str):
    await websocket.accept()

    print("WebSocket connected")

    # Find matching file
    matches = list(UPLOAD_DIR.glob(f"{file_id}_*"))
    if not matches:
        raise HTTPException(status_code=404, detail="File not found uh oh")
    file_path = matches[0]

    try:
        raw = mne.io.read_raw(file_path, preload=False)
        sfreq = int(raw.info["sfreq"])
        total_samples = raw.n_times

        print("Loaded file successfully")
        print(f"Number of samples: {raw.n_times}")
        print(f"Sampling rate: {raw.info['sfreq']}")

        chunk_size = sfreq  # 1-second chunks
        idx = 0

        while idx < raw.n_times:
            print(f"Loop at index {idx}")
            data, times = raw[:, idx:idx+chunk_size]

            message = {
                "t": float(times[0]),
                "data": data.tolist()
            }

            await websocket.send_text(json.dumps(message))  # This could be failing silently
            print("Sent chunk")
            idx += chunk_size
            await asyncio.sleep(1.0)


    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        await websocket.send_text(json.dumps({"error": str(e)}))
        await websocket.close()