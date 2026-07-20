from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "GuideBridge"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/guidebridge"
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DATABASE: str = "guidebridge"

    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000"

    STORAGE_BACKEND: str = "s3"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-south-1"
    AWS_S3_BUCKET: str = ""

    PAYHERE_MERCHANT_ID: str = ""
    PAYHERE_MERCHANT_SECRET: str = ""
    PAYHERE_SANDBOX: bool = True
    PAYHERE_NOTIFY_URL: str = "http://localhost:8000/api/v1/payments/payhere/callback"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@guidebridge.lk"
    SENDGRID_API_KEY: str = ""

    JITSI_DOMAIN: str = "meet.jit.si"

    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: str = "jpg,jpeg,png,pdf,doc,docx"

    DEFAULT_PLATFORM_COMMISSION_PERCENT: int = 15
    DEFAULT_FREE_CHAT_LIMIT: int = 10

    SUPER_ADMIN_EMAIL: str = "admin@guidebridge.lk"
    SUPER_ADMIN_PASSWORD: str = "ChangeMe123!"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_file_types_list(self) -> List[str]:
        return [t.strip().lower() for t in self.ALLOWED_FILE_TYPES.split(",") if t.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
