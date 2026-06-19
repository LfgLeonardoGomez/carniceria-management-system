import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from src.core.email import EmailService


class TestEmailService:
    """TASK-2.2: Tests para EmailService con aiosmtplib."""

    @pytest.mark.asyncio
    async def test_send_recovery_email_success(self):
        with patch("core.email.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = None
            result = await EmailService.send_recovery_email(
                to="user@basile.app",
                token="abc123",
                frontend_url="http://localhost:5173",
            )
            assert result is True
            mock_send.assert_awaited_once()
            call_args, call_kwargs = mock_send.call_args
            # First positional arg is the MIMEMultipart message
            msg = call_args[0]
            assert "user@basile.app" in msg["To"]
            assert "Recuperá tu contraseña" in msg["Subject"]
            # Verify the HTML body contains the link (may be base64 encoded due to non-ASCII chars)
            part = msg.get_payload(0)
            payload = part.get_payload()
            if part.get("Content-Transfer-Encoding") == "base64":
                import base64
                payload = base64.b64decode(payload).decode("utf-8")
            assert "http://localhost:5173/restablecer-contrasena" in payload
            assert "abc123" in payload

    @pytest.mark.asyncio
    async def test_send_recovery_email_failure_returns_false(self):
        with patch("core.email.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("SMTP timeout")
            result = await EmailService.send_recovery_email(
                to="user@basile.app",
                token="abc123",
                frontend_url="http://localhost:5173",
            )
            assert result is False
