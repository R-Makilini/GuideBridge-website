from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api_router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import configure_logging, get_logger
from app.database import model_registry  # noqa: F401
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.modules.chat.router import ws_router as chat_ws_router


configure_logging()
logger = get_logger("main")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],
)

app = FastAPI(
    title=settings.APP_NAME,
    description="Bridging School Students with Verified University Mentors",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)


@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request,
    exc: AppException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            **exc.detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    cleaned_errors = []

    for error in exc.errors():
        cleaned_error = {
            "type": error.get("type"),
            "location": list(error.get("loc", [])),
            "message": error.get("msg"),
        }

        error_input = error.get("input")

        if isinstance(
            error_input,
            (
                str,
                int,
                float,
                bool,
                list,
                dict,
                type(None),
            ),
        ):
            cleaned_error["input"] = error_input
        else:
            cleaned_error["input"] = str(error_input)

        if error.get("ctx"):
            cleaned_error["context"] = {
                key: str(value)
                for key, value in error["ctx"].items()
            }

        cleaned_errors.append(cleaned_error)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation failed.",
            "error_code": "VALIDATION_ERROR",
            "errors": cleaned_errors,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.error(
        "Unhandled exception on %s: %s",
        request.url.path,
        exc,
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected error occurred.",
            "error_code": "INTERNAL_SERVER_ERROR",
        },
    )


@app.get("/", tags=["System"])
def root():
    return {
        "success": True,
        "message": "GuideBridge API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "ready": "/ready",
    }


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
    }


@app.get("/ready", tags=["System"])
def readiness_check():
    from sqlalchemy import text

    from app.database.session import engine

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "database": "connected",
        }

    except Exception as exc:  
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "database": "disconnected",
                "detail": str(exc),
            },
        )


app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)

app.include_router(
    chat_ws_router,
    prefix=settings.API_V1_PREFIX,
)