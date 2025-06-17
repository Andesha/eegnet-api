# eegnet-api
FastAPI demo for offloading EEG operations to Python

# FastAPI Hello World

## Running the App

1. Activate your virtual environment.
2. Run the app with:

```bash
uvicorn src.main:app --reload
```

The API will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Testing the Endpoint

Visit [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser or use curl:

```bash
curl http://127.0.0.1:8000/
```

You should see:

```json
{"message": "Hello, world!"}
```
