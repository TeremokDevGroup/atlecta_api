#!/bin/sh

uv run alembic upgrade head

uv run uvicorn src.main:app --host 0.0.0.0 --port 8080
