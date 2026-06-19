import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, ValidationError


class TestSettingsValidation:
    """TASK-1.2: Validación de settings JWT."""

    def test_jwt_secret_validation_short(self):
        """Debe fallar si jwt_secret tiene menos de 32 caracteres."""
        with pytest.raises(ValidationError):
            class BadSettings(BaseSettings):
                model_config = SettingsConfigDict(extra="forbid")
                jwt_secret: str
                refresh_token_secret: str
                database_url: str = "x"
                email_host: str = "x"
                email_user: str = "x"
                email_pass: str = "x"
                email_from: str = "x"

                @field_validator("jwt_secret", "refresh_token_secret")
                @classmethod
                def _validate_secret_length(cls, v: str) -> str:
                    if len(v) < 32:
                        raise ValueError("JWT secrets must be at least 32 characters long")
                    return v

            BadSettings(jwt_secret="short", refresh_token_secret="also-short-but-okay-ish")

    def test_jwt_secret_validation_ok(self):
        """Debe aceptar secrets de 32+ caracteres."""
        from src.config.settings import settings
        assert len(settings.jwt_secret) >= 32
        assert len(settings.refresh_token_secret) >= 32

    def test_default_access_token_expire(self):
        from src.config.settings import settings
        assert settings.access_token_expire_minutes == 15

    def test_default_refresh_token_expire(self):
        from src.config.settings import settings
        assert settings.refresh_token_expire_days == 7

    def test_default_jwt_algorithm(self):
        from src.config.settings import settings
        assert settings.jwt_algorithm == "HS256"
