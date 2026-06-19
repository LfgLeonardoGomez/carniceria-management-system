from typing import Optional

from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.config.database import get_db
from src.modules.auth.models import Usuario
from src.core.security import decode_token
from src.config.settings import settings
from src.common.exceptions import UnauthorizedException, ForbiddenException
from src.common.rbac import normalize_rol

oauth2_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    if not credentials:
        raise UnauthorizedException("Token de autenticación requerido")

    token = credentials.credentials
    try:
        payload = decode_token(token, secret=settings.jwt_secret, token_type="access")
    except Exception:
        raise UnauthorizedException("Token inválido o expirado")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Token malformado")

    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.rol))
        .options(selectinload(Usuario.empresa))
        .where(Usuario.id == user_id)
    )
    usuario: Optional[Usuario] = result.scalar_one_or_none()

    if not usuario:
        raise UnauthorizedException("Usuario no encontrado")
    if not usuario.activo:
        raise ForbiddenException("Usuario inactivo")

    return usuario


async def require_auth(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
) -> None:
    """Inyecta current_user en request.state y empresa_id (puede ser None para superadmin)."""
    request.state.current_user = current_user
    request.state.empresa_id = current_user.empresa_id


async def require_superadmin(
    request: Request,
    _: None = Depends(require_auth),
) -> None:
    """Dependency que exige rol superadmin."""
    current_user = request.state.current_user
    if normalize_rol(current_user.rol.nombre if current_user.rol else None) != "superadmin":
        raise ForbiddenException("Se requiere rol superadmin")
