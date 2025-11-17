from fastapi import FastAPI
from pydantic import BaseModel
import glob
import os
import mne
import mne_bids

MOUNT_PATH = "/data"

class MontageRequest(BaseModel):
    path: str
    tmin: float
    tmax: float

app = FastAPI()


# Remove this for security purposes later
@app.get("/")
def read_mount():
    return {"message": ', '.join(glob.glob(os.path.join(f'{MOUNT_PATH}/*')))}
