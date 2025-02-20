import os
from dotenv import load_dotenv, find_dotenv


# TODO: use pydantic_settings
env_file = find_dotenv("../.env")
load_dotenv(env_file)

DEV_MODE = os.environ.get("DEV_MODE")

if DEV_MODE != "true":

    DB_HOST = os.environ.get("DB_HOST")
    DB_PORT = os.environ.get("DB_PORT")
    DB_NAME = os.environ.get("DB_NAME")
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")

    REDIS_HOST = os.environ.get("REDIS_HOST")
    REDIS_PORT = os.environ.get("REDIS_PORT")

    S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
    S3_ENDPOINT = os.environ.get("S3_ENDPOINT")
    S3_ACCESS = os.environ.get("S3_ACCESS")
    S3_SECRET = os.environ.get("S3_SECRET")

else:

    DB_HOST = os.environ.get("DB_HOST_DEV")
    DB_PORT = os.environ.get("DB_PORT_DEV")
    DB_NAME = os.environ.get("DB_NAME_DEV")
    DB_USER = os.environ.get("DB_USER_DEV")
    DB_PASSWORD = os.environ.get("DB_PASSWORD_DEV")

    REDIS_HOST = os.environ.get("REDIS_HOST_DEV")
    REDIS_PORT = os.environ.get("REDIS_PORT_DEV")

    S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME_DEV")
    S3_ENDPOINT = os.environ.get("S3_ENDPOINT_DEV")
    S3_ACCESS = os.environ.get("S3_ACCESS_DEV")
    S3_SECRET = os.environ.get("S3_SECRET_DEV")

DB_HOST_TEST = os.environ.get("DB_HOST_TEST")
DB_PORT_TEST = os.environ.get("DB_PORT_TEST")
DB_NAME_TEST = os.environ.get("DB_NAME_TEST")
DB_USER_TEST = os.environ.get("DB_USER_TEST")
DB_PASS_TEST = os.environ.get("DB_PASS_TEST")

AUTH_SECRET = str(os.environ.get("AUTH_SECRET"))
