import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib
from jinja2 import Template

from src.config.settings import settings

logger = logging.getLogger("basile.email")

RECOVERY_TEMPLATE = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Recuperá tu contraseña — BASILE</title>
</head>
<body>
    <h2>Recuperá tu contraseña — BASILE</h2>
    <p>Recibimos una solicitud para restablecer tu contraseña.</p>
    <p>Hacé clic en el siguiente enlace para continuar:</p>
    <p><a href="{{ frontend_url }}/restablecer-contrasena?token={{ token }}">
        Restablecer contraseña
    </a></p>
    <p>Si no solicitaste esto, ignorá este email.</p>
    <p>El enlace expira en 1 hora.</p>
</body>
</html>
""")


class EmailService:
    """Async email service using SMTP generic (aiosmtplib)."""

    @staticmethod
    async def send_recovery_email(to: str, token: str, frontend_url: str) -> bool:
        """Send password recovery email. Returns True if sent, False on failure."""
        html = RECOVERY_TEMPLATE.render(token=token, frontend_url=frontend_url)
        message = MIMEMultipart("alternative")
        message["Subject"] = "Recuperá tu contraseña — BASILE"
        message["From"] = settings.email_from
        message["To"] = to
        message.attach(MIMEText(html, "html", "utf-8"))

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.email_host,
                port=settings.email_port,
                username=settings.email_user,
                password=settings.email_pass,
                start_tls=True,
            )
            return True
        except Exception as exc:
            logger.critical(
                "Email delivery failed",
                extra={
                    "recipient": to,
                    "error": str(exc),
                    "template": "recovery",
                },
            )
            return False
