# Atlecta API

The API for Atlecta - an app for finding a training partner. 

## Technology stack

- [FastAPI](https://fastapi.tiangolo.com) as the backend API.
- [Pydantic](https://docs.pydantic.dev/latest/) for data validation.
- [PostgreSQL](https://www.postgresql.org/) as the relational database.
- [SQLAlchemy](https://www.sqlalchemy.org/) as the ORM.
- [Alembic](https://alembic.sqlalchemy.org/en/latest/) for managing migrations.

## Pre-requests

- Python 3.12.2 or newer 
- Working PostgreSQL instance
- Poetry packaging and dependency manager (optional, but preferred)
## Installation

Using `pip`:
```bash
pip install requirements.txt
```

Using `poetry`: 
```bash
poetry install
```
## Config

Create `.env` file in your project root directory:

```bash
DB_HOST=YOUR_DB_HOST
DB_PORT=YOUR_DB_PORT
DB_NAME=YOUR_DB_NAME
DB_USER=YOUR_DB_USER
DB_PASSWORD=YOUR_DB_PASSOWORD

AUTH_SECRET=YOUR_AUTH_SECRET # A string which is needed to encode JWT. Just use something like a strong password.
```

## Usage

Run `uvicorn` server with:
```bash 
uvicorn src.main:app --reload
```

View API schema at [127.0.0.1:8000/docs](127.0.0.1:8000/docs)
