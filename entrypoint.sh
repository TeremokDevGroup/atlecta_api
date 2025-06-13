#!/bin/sh

uv run alembic upgrade head

# uv run gunicorn -k uvicorn.workers.UvicornWorker -w 2 --bind 0.0.0.0:8080 src.main:app

uv run gunicorn -k uvicorn.workers.UvicornWorker -w 2 --bind 0.0.0.0:8080 src.main:app --access-logfile "-" --log-level info
