import os
from dotenv import load_dotenv, find_dotenv


# TODO: use pydantic_settings
env_file = find_dotenv("../.env")
load_dotenv(env_file)

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

AUTH_SECRET = str(os.environ.get("AUTH_SECRET"))
