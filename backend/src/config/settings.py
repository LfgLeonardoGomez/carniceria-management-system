from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    database_url: str
    jwt_secret: str
    refresh_token_secret: str
    email_host: str
    email_port: int = 587
    email_user: str
    email_pass: str
    email_from: str
    frontend_url: str = "http://localhost:5173"
    port: int = 8000
    cors_origin: str = "http://localhost:5173"
    upload_path: str = "./uploads"
    node_env: str = "development"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    jwt_algorithm: str = "HS256"

    @field_validator("jwt_secret", "refresh_token_secret")
    @classmethod
    def _validate_secret_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT secrets must be at least 32 characters long")
        return v


settings = Settings()
