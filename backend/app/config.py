import secrets
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from functools import lru_cache
from typing import Literal

from cryptography.fernet import Fernet
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: Literal["development", "test", "production"] = "development"

    # Database
    database_url: str = "sqlite:///./copytrade.db"

    # JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Encryption
    encryption_key: str = ""

    # Session/Cookies
    session_cookie_name_access: str = "ct_access"
    session_cookie_name_refresh: str = "ct_refresh"
    session_cookie_name_csrf: str = "ct_csrf"
    csrf_header_name: str = "X-CSRF-Token"
    password_reveal_ttl_seconds: int = 30

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Redis (rate limit / distributed session state)
    redis_url: str = ""

    # Admin
    admin_username: str = "admin"
    admin_password: str = ""
    admin_email: str = "admin@copytrade.app"

    # V1 deprecation window
    v1_deprecation_start: str = "2026-02-06T00:00:00+00:00"
    v1_deprecation_window_days: int = 14

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator(
        "access_token_expire_minutes",
        "refresh_token_expire_days",
        "v1_deprecation_window_days",
        "password_reveal_ttl_seconds"
    )
    @classmethod
    def _validate_positive_ints(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Value must be greater than zero")
        return value

    @model_validator(mode="after")
    def _validate_security_settings(self) -> "Settings":
        if not self.jwt_secret_key:
            if self.app_env == "production":
                raise ValueError("JWT_SECRET_KEY is required in production")
            self.jwt_secret_key = secrets.token_urlsafe(48)

        if self.app_env == "production" and len(self.jwt_secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 chars in production")

        if not self.encryption_key:
            if self.app_env == "production":
                raise ValueError("ENCRYPTION_KEY is required in production")
            self.encryption_key = Fernet.generate_key().decode()

        try:
            Fernet(self.encryption_key.encode())
        except Exception as exc:  # pragma: no cover - direct validation branch
            raise ValueError("ENCRYPTION_KEY must be a valid Fernet key") from exc

        if not self.admin_password:
            if self.app_env == "production":
                raise ValueError("ADMIN_PASSWORD is required in production")
            self.admin_password = secrets.token_urlsafe(18)

        if self.app_env == "production":
            if len(self.admin_password) < 12:
                raise ValueError("ADMIN_PASSWORD must be at least 12 chars")
            if not self.redis_url:
                raise ValueError("REDIS_URL is required in production")
            if "*" in self.cors_origins_list:
                raise ValueError("CORS_ORIGINS cannot contain '*' in production")

        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def cookie_secure(self) -> bool:
        return self.app_env == "production"

    @property
    def docs_enabled(self) -> bool:
        return self.app_env != "production"

    @property
    def v1_deprecation_start_at(self) -> datetime:
        raw = self.v1_deprecation_start.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @property
    def v1_sunset_at(self) -> datetime:
        return self.v1_deprecation_start_at + timedelta(days=self.v1_deprecation_window_days)

    @property
    def v1_sunset_http(self) -> str:
        return format_datetime(self.v1_sunset_at, usegmt=True)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
