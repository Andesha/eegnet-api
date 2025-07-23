import matplotlib.pyplot as plt
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
async def stream_eeg(websocket: WebSocket, file_id: str, chunk_size=512 * 1024):
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

        chunk_size = sfreq  # 1-second chunks
        idx = 0

        while idx < raw.n_times:
            data, times = raw[:, idx:idx+chunk_size]

            # Slice the data to only include every 10th sample
            data = data[:, ::10]
            times = times[::10]

            message = {
                "t": float(times[0]),
                "data": data.tolist()
            }

            await websocket.send_text(json.dumps(message))  # This could be failing silently
            percent_complete = (idx / total_samples) * 100
            print(f"Sent chunk - {percent_complete:.1f}% complete")
            idx += chunk_size

        # close the websocket
        await websocket.close()

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        await websocket.send_text(json.dumps({"error": str(e)}))
        await websocket.close()

# Topo plot generation endpoint which returns a PNG image
# Takes two parameters: start_time and end_time
@router.get("/topo/{file_id}")
def get_topo(file_id: str, start_time: float, end_time: float):
    # Find matching file
    matches = list(UPLOAD_DIR.glob(f"{file_id}_*"))
    if not matches:
        raise HTTPException(status_code=404, detail="File not found")
    file_path = matches[0]

    # Load the file
    raw = mne.io.read_raw(file_path, preload=False).pick('eeg')
    raw = raw.crop(tmin=start_time, tmax=end_time)
    raw = raw.drop_channels(['EXG1', 'EXG2', 'EXG3', 'EXG4', 'EXG5', 'EXG6', 'EXG7', 'EXG8', 'GSR1', 'GSR2', 'Erg1', 'Erg2', 'Resp', 'Plet', 'Temp'], on_missing='ignore')
    raw = raw.set_montage('biosemi128', on_missing='ignore')

    # Average over time
    data_avg = raw.get_data().mean(axis=1)

    fig, ax = plt.subplots()
    im, _ = mne.viz.plot_topomap(
        data_avg,
        raw.info,
        axes=ax,
        show=False,
        contours=0,
    )
    # fig.savefig("topo.png")

    # Save figure to in-memory buffer
    import io
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300)
    plt.close(fig)
    buf.seek(0)

    # Return as StreamingResponse
    return StreamingResponse(buf, media_type="image/png")
