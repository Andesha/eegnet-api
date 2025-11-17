from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import glob
import os
import mne
import mne_bids
from io import BytesIO
import matplotlib.pyplot as plt


MOUNT_PATH = "/data"

class TopoRequest(BaseModel):
    path: str = Field("/data/large_demo.bdf", description="Path to the dataset file")
    tmin: float = Field(0.0, description="Start of time window in seconds.")
    tmax: float = Field(0.0, description="End of time window in seconds.")

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

    exclude_channels = [
        "EXG1", "EXG2", "EXG3", "EXG4", "EXG5", "EXG6", "EXG7", "EXG8",
        "GSR1", "GSR2", "Erg1", "Erg2", "Resp", "Plet", "Temp"
    ]
    raw = raw.drop_channels(exclude_channels, on_missing='ignore')

    raw = raw.set_montage('biosemi128', on_missing='ignore')

    raw = raw.pick('eeg')

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

    fig = raw.plot_sensors(show_names=True, show=False)

    # Write figure to buffer for streaming
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    buffer.seek(0) # Reset buffer to start?

    return StreamingResponse(buffer, media_type="image/png")



@app.post(
    "/topo",
    response_class=StreamingResponse,
    summary="Generate a topographic map based on a time window.",
    description=(
        "Generates a topographic map based on a time window for the given path and returns it as a PNG image.\n\n"
        "The image is streamed directly in the response, without writing to disk."
        "The time window is specified in seconds, with the default being the entire dataset."
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
def base_topo(topo_request: TopoRequest) -> StreamingResponse:
    """
    Base topo endpoint for the given request.

    Parameters
    ----------
    topo_request : TopoRequest
        The request containing the path and time window.

    Returns
    -------
    StreamingResponse
        A streaming response containing the topographic map.
    """

    # Load helper is fine, setting montage for test case
    raw = load_helper(topo_request.path)
    
    local_tmax = None if topo_request.tmin == 0.0 else topo_request.tmax
    data_raw = raw.crop(tmin=topo_request.tmin, tmax=local_tmax).get_data().mean(axis=1)

    fig, ax = plt.subplots()
    im, _ = mne.viz.plot_topomap(
        data_raw,
        raw.info,
        axes=ax,
        show=False,
        contours=0,
    )

    # Write figure to buffer for streaming
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0) # Reset buffer to start?

    return StreamingResponse(buffer, media_type="image/png")

# Remove this for security purposes later
@app.get("/")
def read_mount():
    return {"message": ', '.join(glob.glob(os.path.join(f'{MOUNT_PATH}/*')))}
