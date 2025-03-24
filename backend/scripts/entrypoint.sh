#!/bin/sh
set -e


echo "Upgrading database..."
alembic upgrade head


echo "Starting FastAPI..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port ${FASTAPI_PORT}