from typing import BinaryIO

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings
from app.core.exceptions import BadRequestError
from app.integrations.storage.base import StorageBackend


class S3StorageBackend(StorageBackend):
    def __init__(self):
        self.bucket = settings.AWS_S3_BUCKET
        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )

    def upload(self, file_obj: BinaryIO, key: str, content_type: str) -> str:
        try:
            self.client.upload_fileobj(
                file_obj, self.bucket, key, ExtraArgs={"ContentType": content_type}
            )
        except (BotoCoreError, ClientError) as exc:
            raise BadRequestError(f"Failed to upload file to S3: {exc}") from exc
        return f"https://{self.bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"

    def delete(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except (BotoCoreError, ClientError):
            pass
