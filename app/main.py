from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import glob
import os
import mne
import mne_bids
from typing import List
import json
import matplotlib.pyplot as plt
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

# @app.get("/montage")
# def read_montages(path: str) -> str:
#     try:
#         raw = mne.io.read_raw(path)
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

#     return ', '.join(raw.info['ch_names'])


@app.get(
    "/montage",
    response_class=StreamingResponse,
    summary="Generate a simple test plot",
    description=(
        "Creates a simple matplotlib line plot in memory and returns it as a PNG image.\n\n"
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
def build_base_montage(x: List[float] = [1, 2, 3], y: List[float] = [4, 5, 6]) -> StreamingResponse:
    """
    Generate a PNG plot based on the provided x/y numeric data.

    Parameters
    ----------
    x : List[float]
        X-axis values used for the plot. Defaults to `[1, 2, 3]`.
    y : List[float]
        Y-axis values used for the plot. Defaults to `[4, 5, 6]`.

    Returns
    -------
    StreamingResponse
        An HTTP response streaming a PNG image in memory.

    Notes
    -----
    - Uses matplotlib to generate the plot entirely in memory.
    - The PNG is not written to disk.
    - Returned with correct `image/png` media type.
    """
    # --- Create the figure ---
    fig, ax = plt.subplots()
    ax.plot(x, y, linewidth=2)
    ax.set_xlabel("X values")
    ax.set_ylabel("Y values")
    ax.set_title("Generated Plot")

    # --- Render to PNG in memory ---
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)

    # --- Stream back to client ---
    return StreamingResponse(buffer, media_type="image/png")


# Remove this for security purposes later
@app.get("/")
def read_mount():
    return {"message": ', '.join(glob.glob(os.path.join(f'{MOUNT_PATH}/*')))}
