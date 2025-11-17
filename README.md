# EEGNet Montage API

TODO: add description and link to spec sheet

## Building

Build with: `docker build -t eegnet-api .`

## Running

Note mounting of the test path: `docker run --rm -p 8000:8000 -v ./test-data:/data eegnet-api:latest`

## Docs

Should be available where the host is and adding `/docs#` to the hosted location.

## TODOs

* Error handling
* Security review
* Image scaling on the plots