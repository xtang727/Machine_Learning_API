#!/bin/bash

RUN_PORT=${PORT:-8000}

/opt/env/bin/gunicorn --worker-tmp-dir /dev/shm -k uvicorn.workders.UvicornWorker --bind '0.0.0.0:${RUN_PORT}' app.main:app