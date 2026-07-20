import re
import uuid

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import BadRequestError

MIME_EXTENSION_MAP = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}

SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9_.-]")


def validate_upload(file: UploadFile, max_size_mb: int | None = None) -> None:
    max_size = (max_size_mb or settings.MAX_UPLOAD_SIZE_MB) * 1024 * 1024

    extension = (file.filename or "").rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else ""
    if extension not in settings.allowed_file_types_list:
        raise BadRequestError(f"File type '.{extension}' is not allowed.")

    if file.content_type not in MIME_EXTENSION_MAP:
        raise BadRequestError(f"Unsupported MIME type: {file.content_type}")

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > max_size:
        raise BadRequestError(f"File exceeds the maximum allowed size of {max_size_mb or settings.MAX_UPLOAD_SIZE_MB}MB.")
    if size == 0:
        raise BadRequestError("Uploaded file is empty.")


def safe_file_key(original_filename: str, folder: str) -> tuple[str, str]:
    """Returns (storage_key, safe_display_name)."""
    safe_name = SAFE_NAME_RE.sub("_", original_filename or "file")
    unique_key = f"{folder}/{uuid.uuid4().hex}_{safe_name}"
    return unique_key, safe_name
