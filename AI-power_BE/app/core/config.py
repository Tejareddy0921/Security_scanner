from functools import lru_cache
from pathlib import Path
import secrets
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = Field(
        default="scam_detection",
        min_length=1,
        validation_alias=AliasChoices("DATABASE_NAME", "MONGODB_DATABASE"),
    )
    # A random process-local key lets a fresh development checkout start safely.
    # Deployments should provide SECRET_KEY so tokens remain valid across restarts.
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(48), min_length=32)
    algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0, le=1440)
    groq_api_key: SecretStr | None = None
    groq_model: str = Field(default="openai/gpt-oss-20b", min_length=1)
    groq_timeout_seconds: float = Field(default=45.0, gt=0, le=300)
    max_content_length: int = Field(default=20_000, gt=0)
    max_request_size_bytes: int = Field(default=1_048_576, gt=0)
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        validation_alias=AliasChoices("CORS_ORIGINS", "CLIENT_URL"),
    )

    @field_validator("groq_api_key", mode="before")
    @classmethod
    def empty_groq_key_is_missing(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def require_deployment_secret(self) -> "Settings":
        if self.environment == "production" and "secret_key" not in self.model_fields_set:
            raise ValueError("SECRET_KEY must be explicitly configured in production")
        return self

    @property
    def allowed_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        if self.environment == "development":
            origins.extend(
                [
                    "http://localhost:4173",
                    "http://127.0.0.1:4173",
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                ]
            )
        return list(dict.fromkeys(origins))


@lru_cache
def get_settings() -> Settings:
    return Settings()
