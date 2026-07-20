import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | request_id=%(request_id)s | %(message)s",
        defaults={"request_id": "-"},
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
