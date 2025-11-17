from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import glob
import os
import mne
import mne_bids
from typing import List
from io import BytesIO

MOUNT_PATH = "/data"

class TopoRequest(BaseModel):
    path: str
    tmin: float
    tmax: float

app = FastAPI(
    title="EEGNet API",
    description="API for the EEGNet project to build montages and topographies.",
    version="0.1.0",
    contact={
        "name": "Tyler Collins",
        "url": "https://github.com/andesha",
        "email": "collins.tyler.k@gmail.com",
    },
    license={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)


def load_helper(path: str) -> mne.io.Raw:
    """
    Helper function to load a raw dataset from the given path.

    Parameters
    ----------
    path : str
        The path to the raw dataset.

    Returns
    -------
    mne.Raw
        The loaded raw dataset.
    """

    try:
        raw = mne.io.read_raw(path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return raw

@app.get(
    "/montage",
    response_class=StreamingResponse,
    summary="Generate a basic montage image",
    description=(
        "Creates a simple montage image for the given path and returns it as a PNG image.\n\n"
        "The image is streamed directly in the response, without writing to disk."
    ),
    responses={
        200: {
            "description": "PNG image containing the generated plot.",
            "content": {
                "image/png": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def base_montage(path: str) -> StreamingResponse:
    """
    Base montage endpoint for the given path.

    Parameters
    ----------
    path : str
        The path to the raw dataset.

    Returns
    -------
    StreamingResponse
        A streaming response containing the montage image.
    """

    # Load helper is fine, setting montage for test case
    raw = load_helper(path)
    raw = raw.set_montage('biosemi128', on_missing='ignore')
    fig = raw.plot_sensors(show_names=True, show=False)

    # Write figure to buffer for streaming
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    buffer.seek(0) # Reset buffer to start?

    return StreamingResponse(buffer, media_type="image/png")


# Remove this for security purposes later
@app.get("/")
def read_mount():
    return {"message": ', '.join(glob.glob(os.path.join(f'{MOUNT_PATH}/*')))}
