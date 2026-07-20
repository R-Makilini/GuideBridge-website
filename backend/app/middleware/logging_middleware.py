import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logging import get_logger

logger = get_logger("http")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        request_id = getattr(request.state, "request_id", "-")
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.time() - start) * 1000, 2)
            logger.error(
                "%s %s failed after %sms",
                request.method,
                request.url.path,
                duration_ms,
                extra={"request_id": request_id},
            )
            raise
        duration_ms = round((time.time() - start) * 1000, 2)
        logger.info(
            "%s %s -> %s in %sms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={"request_id": request_id},
        )
        return response
