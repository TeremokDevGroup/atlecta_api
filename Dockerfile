FROM python:3.12-slim-bookworm

RUN apt update && \
  apt -y install curl && \
  pip install poetry

WORKDIR /app

COPY poetry.lock .
COPY pyproject.toml .

RUN poetry install

COPY . .

RUN chmod +x entrypoint.sh

ENTRYPOINT [ "/app/entrypoint.sh" ]

