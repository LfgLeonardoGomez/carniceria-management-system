from fastapi import Request
from limits import parse
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter

from src.common.exceptions import BasileException

# In-memory storage for rate limiting (dev); Redis in production future
_storage = MemoryStorage()
_limiter = MovingWindowRateLimiter(_storage)

# 5 requests per 60 seconds
AUTH_LIMIT = parse("5/60second")

# 10 requests per 60 seconds for user creation
USER_CREATE_LIMIT = parse("10/60second")


def check_auth_rate_limit(request: Request, email: str) -> None:
    """Check rate limit for auth endpoints keyed by IP + email."""
    client_ip = request.client.host if request.client else "unknown"
    key = f"auth:{client_ip}:{email.lower()}"
    if not _limiter.hit(AUTH_LIMIT, key):
        raise BasileException("Demasiados intentos. Probá de nuevo en unos minutos.", status_code=429)


def check_user_create_rate_limit(request: Request) -> None:
    """Check rate limit for user creation endpoints keyed by IP."""
    client_ip = request.client.host if request.client else "unknown"
    key = f"user_create:{client_ip}"
    if not _limiter.hit(USER_CREATE_LIMIT, key):
        raise BasileException("Demasiadas solicitudes. Probá de nuevo en unos minutos.", status_code=429)
