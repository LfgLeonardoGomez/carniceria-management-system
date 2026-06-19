import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from src.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token


class TestPasswordHashing:
    """TASK-1.1: Tests para bcrypt hashing."""

    def test_hash_password_returns_string(self):
        hashed = hash_password("secret123")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        hashed = hash_password("my_password")
        assert verify_password("my_password", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("my_password")
        assert verify_password("wrong_password", hashed) is False

    def test_hash_password_produces_different_hashes(self):
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2, "bcrypt debe producir salts diferentes"

    def test_verify_password_with_invalid_hash(self):
        assert verify_password("password", "not_a_valid_hash") is False


class TestJWTCreateAndDecode:
    """TASK-1.1: Tests para JWT HS256 create/decode."""

    def test_create_access_token_returns_string(self):
        token = create_access_token({"sub": "user-1"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_returns_string(self):
        token = create_refresh_token({"sub": "user-1"})
        assert isinstance(token, str)

    def test_decode_access_token_success(self):
        token = create_access_token({"sub": "user-1", "empresa_id": "emp-1"})
        payload = decode_token(token, secret="super-secret-jwt-key-for-testing-only-do-not-use-in-production-1234567890", token_type="access")
        assert payload["sub"] == "user-1"
        assert payload["empresa_id"] == "emp-1"
        assert payload["type"] == "access"

    def test_decode_refresh_token_success(self):
        token = create_refresh_token({"sub": "user-1"})
        payload = decode_token(token, secret="super-secret-refresh-key-for-testing-only-do-not-use-in-production-1234567890", token_type="refresh")
        assert payload["sub"] == "user-1"
        assert payload["type"] == "refresh"

    def test_decode_expired_token(self):
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        token = create_access_token({"sub": "user-1"}, expires_delta=timedelta(minutes=-10))
        with pytest.raises(Exception):
            decode_token(token, secret="super-secret-jwt-key-for-testing-only-do-not-use-in-production-1234567890", token_type="access")

    def test_decode_wrong_secret(self):
        token = create_access_token({"sub": "user-1"})
        with pytest.raises(Exception):
            decode_token(token, secret="wrong-secret", token_type="access")

    def test_decode_wrong_token_type(self):
        token = create_refresh_token({"sub": "user-1"})
        with pytest.raises(Exception):
            decode_token(token, secret="super-secret-refresh-key-for-testing-only-do-not-use-in-production-1234567890", token_type="access")

    def test_access_token_expires_in_15_minutes_default(self):
        now = datetime.now(timezone.utc)
        token = create_access_token({"sub": "user-1"})
        payload = decode_token(token, secret="super-secret-jwt-key-for-testing-only-do-not-use-in-production-1234567890", token_type="access")
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        assert (exp - now).total_seconds() <= 15 * 60

    def test_refresh_token_expires_in_7_days_default(self):
        now = datetime.now(timezone.utc)
        token = create_refresh_token({"sub": "user-1"})
        payload = decode_token(token, secret="super-secret-refresh-key-for-testing-only-do-not-use-in-production-1234567890", token_type="refresh")
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        assert (exp - now).total_seconds() <= 7 * 24 * 60 * 60
