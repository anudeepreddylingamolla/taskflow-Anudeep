#!/bin/sh

echo "Running database migrations..."
alembic upgrade head

echo "Seeding database..."
python -m scripts.seed || echo "Seeding skipped or failed (non-fatal)"

echo "Starting TaskFlow API on port 5001..."
exec uvicorn app.main:app --host 0.0.0.0 --port 5001
