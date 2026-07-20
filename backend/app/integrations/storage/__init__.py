from app.core.config import settings
from app.core.exceptions import ConfigurationError
from app.integrations.storage.base import StorageBackend


def get_storage_backend() -> StorageBackend:
    if not settings.AWS_S3_BUCKET:
        raise ConfigurationError("AWS_S3_BUCKET is not configured")

    from app.integrations.storage.s3 import S3StorageBackend

    return S3StorageBackend()
