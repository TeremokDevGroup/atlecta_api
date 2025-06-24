FROM python:3.13-slim-bookworm

RUN apt update && apt -y install curl

COPY --from=ghcr.io/astral-sh/uv:0.6.9 /uv /uvx /bin/

WORKDIR /app

COPY uv.lock .
COPY pyproject.toml .

RUN uv sync --frozen

COPY . .

RUN chmod +x entrypoint.sh

ENTRYPOINT [ "/app/entrypoint.sh" ]

