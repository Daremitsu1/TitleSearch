#!/bin/sh

# Go to the API folder
cd api || exit

# Start the FastAPI apps
uvicorn job-api:app --host 0.0.0.0 --port 8002 &
uvicorn user-authentication-api:app --host 0.0.0.0 --port 8001 &
wait