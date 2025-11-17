from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import glob
import os
import mne
import mne_bids
import json

MOUNT_PATH = "/data"

class TopoRequest(BaseModel):
    path: str
    tmin: float
    tmax: float

app = FastAPI()

@app.get("/montage")
def read_montages(path: str) -> str:
    try:
        raw = mne.io.read_raw(path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ', '.join(raw.info['ch_names'])


# Remove this for security purposes later
@app.get("/")
def read_mount():
    return {"message": ', '.join(glob.glob(os.path.join(f'{MOUNT_PATH}/*')))}
