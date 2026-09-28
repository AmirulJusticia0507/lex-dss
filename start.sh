#!/bin/bash
cd backend
pip install -r requirements.txt
alembic -c alembic.ini upgrade head || true
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
