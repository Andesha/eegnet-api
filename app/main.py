from fastapi import FastAPI
from app.api import router

app = FastAPI(title="EEG File Processor")

app.include_router(router)

@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint returning a hello world message."""
    return {"message": "Hello, world!"}
