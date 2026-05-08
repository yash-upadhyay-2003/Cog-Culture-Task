#!/bin/bash
# FastAPI launch wrapper
exec /home/runner/workspace/.pythonlibs/bin/uvicorn api.app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload
