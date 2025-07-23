# eegnet-api
FastAPI demo for offloading EEG operations to Python

# FastAPI Hello World

## Running the App

1. Activate your virtual environment.
2. Run the app with:

```bash
uvicorn app.main:app --reload
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

## Uploading a demo file

Assuming you have a BDF file called `large_demo.bdf`, you can upload the file via:

`curl -X POST "http://localhost:8000/upload/" -F "file=@large_demo.bdf"`

You should be given a message that looks something like:
```
{"message":"File uploaded successfully","file_id":"ce6c64c7-cc81-4855-807c-9a3711528f3c","filename":"large_demo.bdf"}
```

The `file_id` parameter is used to pass to other API endpoints so that the internal system knows which file you are talking about.

For testing purposes, these can be renamed or shortened internally to make demo queries simpler.

## Getting metadata information

Done via: `curl -X GET "http://localhost:8000/metadata/ce6c64c7-cc81-4855-807c-9a3711528f3c"`. Note the long string field should be a given `file_id` from the upload.

## Getting a topoplot from a time region

`curl -X GET "http://localhost:8000/topo/ce6c64c7-cc81-4855-807c-9a3711528f3c?start_time=5.0&end_time=10.0" --output topo_test.png`

You can view the resulting file wherever you have saved run the curl command from.