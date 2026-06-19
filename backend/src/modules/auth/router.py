import logging
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.config.database import get_db
from src.modules.auth.models import Usuario, RefreshToken, TokenRecuperacion
from src.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RecoverRequest,
    ResetRequest,
    GenericMessageResponse,
    UsuarioPublic,
)
from src.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.core.email import EmailService
from src.config.settings import settings
from src.modules.auth.dependencies import get_current_user, require_auth
from src.common.exceptions import UnauthorizedException, ForbiddenException
from src.common.rate_limit import check_auth_rate_limit

logger = logging.getLogger("basile.auth")
router = APIRouter()

# ---------------------------------------------------------------------------
# Cookie helpers
# ---------------------------------------------------------------------------
REFRESH_COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,
        samesite="lax",
        secure=False if settings.node_env == "development" else True,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=False if settings.node_env == "development" else True,
    )


def _build_usuario_public(usuario: Usuario) -> UsuarioPublic:
    """Construye UsuarioPublic incluyendo original_role si está en el token."""
    # Nota: original_role no se almacena en DB, viene del JWT en contexto de impersonación.
    # El endpoint /auth/me no lo puede saber sin el token, pero login/refresh sí.
    return UsuarioPublic(
        id=str(usuario.id),
        email=usuario.email,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        rol=usuario.rol.nombre if usuario.rol else None,
        empresa_id=str(usuario.empresa_id) if usuario.empresa_id else None,
    )


# ---------------------------------------------------------------------------
# TASK-2.1: POST /auth/login
# ---------------------------------------------------------------------------
@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Response:
    check_auth_rate_limit(request, payload.email)

    # Find user by email
    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.rol))
        .options(selectinload(Usuario.empresa))
        .where(Usuario.email == payload.email)
    )
    usuario: Optional[Usuario] = result.scalar_one_or_none()

    if not usuario or not verify_password(payload.contrasena, usuario.contrasena_hash):
        raise UnauthorizedException("Credenciales inválidas")

    if not usuario.activo:
        raise ForbiddenException("Usuario inactivo")

    # Solo validar empresa activa si el usuario tiene empresa asignada
    if usuario.empresa and not usuario.empresa.activa:
        raise ForbiddenException("Empresa desactivada. Contacte a soporte.")

    # Update ultimo_acceso
    usuario.ultimo_acceso = datetime.now(timezone.utc)
    await db.commit()

    # Generate tokens
    token_data = {
        "sub": str(usuario.id),
        "empresa_id": str(usuario.empresa_id) if usuario.empresa_id else None,
        "rol": usuario.rol.nombre if usuario.rol else None,
    }
    access_token = create_access_token(token_data)
    refresh_token_obj = create_refresh_token(token_data)

    # Persist refresh token in DB
    decoded_refresh = decode_token(
        refresh_token_obj,
        secret=settings.refresh_token_secret,
        token_type="refresh",
    )
    db_refresh = RefreshToken(
        usuario_id=usuario.id,
        jti=decoded_refresh["jti"],
        exp=datetime.fromtimestamp(decoded_refresh["exp"], tz=timezone.utc),
        revoked=False,
    )
    db.add(db_refresh)
    await db.commit()

    # Build response with cookie
    response = JSONResponse(
        content=LoginResponse(
            access_token=access_token,
            token_type="bearer",
            usuario=_build_usuario_public(usuario),
        ).model_dump(),
    )
    _set_refresh_cookie(response, refresh_token_obj)
    return response


# ---------------------------------------------------------------------------
# TASK-2.3: POST /auth/recover
# ---------------------------------------------------------------------------
@router.post("/recover", response_model=GenericMessageResponse)
async def recover(
    request: Request,
    payload: RecoverRequest,
    db: AsyncSession = Depends(get_db),
) -> GenericMessageResponse:
    check_auth_rate_limit(request, payload.email)

    result = await db.execute(select(Usuario).where(Usuario.email == payload.email))
    usuario: Optional[Usuario] = result.scalar_one_or_none()

    if usuario:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        tr = TokenRecuperacion(
            usuario_id=usuario.id,
            token_hash=token_hash,
            expiracion=datetime.now(timezone.utc) + timedelta(hours=1),
            usado=False,
        )
        db.add(tr)
        await db.commit()

        sent = await EmailService.send_recovery_email(
            to=usuario.email,
            token=raw_token,
            frontend_url=settings.frontend_url,
        )
        if not sent:
            logger.critical("Recovery email failed to send", extra={"email": usuario.email})

    # Always return generic message
    return GenericMessageResponse(message="Si el email existe, recibirás instrucciones de recuperación.")


# ---------------------------------------------------------------------------
# TASK-2.4: POST /auth/reset
# ---------------------------------------------------------------------------
@router.post("/reset", response_model=GenericMessageResponse)
async def reset(
    payload: ResetRequest,
    db: AsyncSession = Depends(get_db),
) -> GenericMessageResponse:
    if payload.nueva_contrasena != payload.confirmacion:
        from src.common.exceptions import BasileException
        raise BasileException("Las contraseñas no coinciden", status_code=400)

    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
    result = await db.execute(
        select(TokenRecuperacion)
        .where(
            TokenRecuperacion.token_hash == token_hash,
            TokenRecuperacion.usado == False,
        )
    )
    tr: Optional[TokenRecuperacion] = result.scalar_one_or_none()

    # DB stores naive datetimes (utcnow), use utcnow for comparison
    if not tr or tr.expiracion < datetime.utcnow():
        from src.common.exceptions import BasileException
        raise BasileException("Token inválido o expirado", status_code=400)

    # Update password
    user_result = await db.execute(select(Usuario).where(Usuario.id == tr.usuario_id))
    usuario: Usuario = user_result.scalar_one()
    usuario.contrasena_hash = hash_password(payload.nueva_contrasena)
    tr.usado = True
    await db.commit()

    return GenericMessageResponse(message="Contraseña actualizada correctamente.")


# ---------------------------------------------------------------------------
# TASK-2.5: POST /auth/refresh
# ---------------------------------------------------------------------------
class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(extra="forbid")


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    refresh_cookie = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_cookie:
        raise UnauthorizedException("Refresh token requerido")

    try:
        payload = decode_token(
            refresh_cookie,
            secret=settings.refresh_token_secret,
            token_type="refresh",
        )
    except Exception:
        raise UnauthorizedException("Refresh token inválido")

    jti = payload.get("jti")
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.jti == jti)
    )
    db_token: Optional[RefreshToken] = result.scalar_one_or_none()

    if not db_token or db_token.revoked or db_token.exp < datetime.utcnow():
        raise UnauthorizedException("Refresh token revocado o expirado")

    # Load user for claims
    user_result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.rol))
        .where(Usuario.id == payload["sub"])
    )
    usuario: Optional[Usuario] = user_result.scalar_one_or_none()
    if not usuario or not usuario.activo:
        raise UnauthorizedException("Usuario inválido o inactivo")

    # Revoke old refresh token
    db_token.revoked = True

    # Generate new tokens
    token_data = {
        "sub": str(usuario.id),
        "empresa_id": str(usuario.empresa_id) if usuario.empresa_id else None,
        "rol": usuario.rol.nombre if usuario.rol else None,
    }
    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)

    # Persist new refresh token
    decoded_new = decode_token(
        new_refresh,
        secret=settings.refresh_token_secret,
        token_type="refresh",
    )
    new_db_token = RefreshToken(
        usuario_id=usuario.id,
        jti=decoded_new["jti"],
        exp=datetime.fromtimestamp(decoded_new["exp"], tz=timezone.utc),
        revoked=False,
    )
    db.add(new_db_token)
    await db.commit()

    response = JSONResponse(
        content=RefreshResponse(access_token=new_access).model_dump(),
    )
    _set_refresh_cookie(response, new_refresh)
    return response


# ---------------------------------------------------------------------------
# TASK-2.6: POST /auth/logout
# ---------------------------------------------------------------------------
@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    refresh_cookie = request.cookies.get(REFRESH_COOKIE_NAME)
    if refresh_cookie:
        try:
            payload = decode_token(
                refresh_cookie,
                secret=settings.refresh_token_secret,
                token_type="refresh",
            )
            jti = payload.get("jti")
            result = await db.execute(
                select(RefreshToken).where(RefreshToken.jti == jti)
            )
            db_token: Optional[RefreshToken] = result.scalar_one_or_none()
            if db_token:
                db_token.revoked = True
                await db.commit()
        except Exception:
            pass  # If token is invalid, still clear cookie

    response = Response(status_code=204)
    _clear_refresh_cookie(response)
    return response


# ---------------------------------------------------------------------------
# TASK-3.x: Current user endpoint (useful for frontend + testing)
# ---------------------------------------------------------------------------
@router.get("/me", response_model=UsuarioPublic)
async def me(
    current_user: Usuario = Depends(get_current_user),
) -> UsuarioPublic:
    return _build_usuario_public(current_user)
