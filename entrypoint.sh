#!/bin/sh

if [ "$DEV" = "true" ]; then
    echo "Running in development mode"
    uvicorn verspaetungsorakel.main:app --reload
    exit 0
else
    echo "Running in production mode"
    gunicorn -k uvicorn.workers.UvicornWorker verspaetungsorakel.main:app -b :8000
fi
