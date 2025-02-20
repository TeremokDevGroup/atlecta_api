from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from typing import Union

from .config import S3_BUCKET_NAME, S3_ENDPOINT, S3_ACCESS, S3_SECRET

import asyncio
import aioboto3
from botocore.client import Config


class S3BucketService:
    def __init__(self, bucket_name: str, endpoint: str, access_key: str, secret_key: str) -> None:
        self.bucket_name = bucket_name
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key

    @asynccontextmanager
    async def get_s3_client(self):
        session = aioboto3.Session()

        yield session.client(
            service_name="s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version="s3v4")
        )

    async def upload_file_object(self, prefix: str, source_file_name: str, content: Union[str, bytes], content_type: str = "application/octet-stream") -> None:
        session = aioboto3.Session()

        async with session.client(
            service_name="s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version="s3v4")
        ) as client:

            destination_path = str(Path(prefix, source_file_name))
            # Use BytesIO for file-like object handling
            if isinstance(content, str):
                buffer = BytesIO(content.encode("utf-8"))
            elif isinstance(content, bytes):
                buffer = BytesIO(content)
            else:
                raise ValueError("Content must be str or bytes.")

            # Reset buffer position before upload
            buffer.seek(0)

            # Upload file with optional ContentType
            await client.upload_fileobj(
                buffer,
                self.bucket_name,
                destination_path,
                ExtraArgs={"ContentType": content_type}
            )

    async def delete_file_object(self, prefix: str, source_file_name: str) -> None:
        session = aioboto3.Session()

        async with session.client(
            service_name="s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version="s3v4")
        ) as client:
            path_to_file = str(Path(prefix, source_file_name))

            await client.delete_object(Bucket=self.bucket_name, Key=path_to_file)

    # def list_objects(self, prefix: str) -> list[str]:
    #     client = self.create_s3_client()
    #
    #     response = client.list_objects_v2(
    #         Bucket=self.bucket_name, Prefix=prefix)
    #     storage_content: list[str] = []
    #
    #     try:
    #         contents = response["Contents"]
    #     except KeyError:
    #         return storage_content
    #
    #     for item in contents:
    #         storage_content.append(item["Key"])
    #
    #     return storage_content
    #
    #
    # def download_file_object(self, prefix: str, source_file_name: str, download_file_name: str) -> None:
    #     client = self.create_s3_client()
    #     path_to_file = str(Path(prefix, source_file_name))
    #     client.download_file(Bucket=self.bucket_name,
    #                          Key=path_to_file, Filename=download_file_name)


def s3_bucket_service_factory() -> S3BucketService:
    return S3BucketService(
        S3_BUCKET_NAME,
        S3_ENDPOINT,
        S3_ACCESS,
        S3_SECRET
    )
