from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.modules.auth.dependencies import get_current_user, require_auth
from src.modules.auth.models import Usuario
from src.modules.usuario import schemas
from src.modules.usuario import service
from src.common.rbac import require_role
from src.common.rate_limit import check_user_create_rate_limit

router = APIRouter()


# ---------------------------------------------------------------------------
# Profile endpoints (any authenticated user)
# IMPORTANT: /me debe ir ANTES de /{usuario_id} para evitar que FastAPI
# interprete "me" como un UUID de usuario.
# ---------------------------------------------------------------------------
@router.get("/me", response_model=schemas.PerfilPublic)
async def get_me(
    current_user: Usuario = Depends(get_current_user),
) -> schemas.PerfilPublic:
    return schemas.PerfilPublic(
        id=current_user.id,
        nombre=current_user.nombre,
        apellido=current_user.apellido,
        email=current_user.email,
        rol=current_user.rol.nombre if current_user.rol else None,
        empresa=current_user.empresa.nombre_comercial if current_user.empresa else None,
        ultimo_acceso=current_user.ultimo_acceso,
    )


@router.put("/me", response_model=schemas.PerfilPublic)
async def update_me(
    payload: schemas.PerfilUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> schemas.PerfilPublic:
    usuario = await service.actualizar_perfil_propio(
        db=db,
        usuario_id=current_user.id,
        nombre=payload.nombre,
        apellido=payload.apellido,
        email=payload.email,
        rol_id=payload.rol_id,  # Será ignorado por el servicio
    )
    return schemas.PerfilPublic(
        id=usuario.id,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        rol=usuario.rol.nombre if usuario.rol else None,
        empresa=usuario.empresa.nombre_comercial if usuario.empresa else None,
        ultimo_acceso=usuario.ultimo_acceso,
    )


# ---------------------------------------------------------------------------
# Admin / superadmin endpoints
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=schemas.ContrasenaTemporalResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("usuarios:create"))],
)
async def create_usuario(
    request: Request,
    payload: schemas.UsuarioCreate,
    db: AsyncSession = Depends(get_db),
) -> schemas.ContrasenaTemporalResponse:
    check_user_create_rate_limit(request)
    current_user: Usuario = request.state.current_user
    usuario, temp_pass = await service.crear_usuario(
        db=db,
        current_user=current_user,
        nombre=payload.nombre,
        apellido=payload.apellido,
        email=payload.email,
        rol_id=payload.rol_id,
        empresa_id=payload.empresa_id,
    )
    return schemas.ContrasenaTemporalResponse(
        usuario=_to_public(usuario),
        contrasena_temporal=temp_pass,
    )


@router.get(
    "",
    response_model=schemas.UsuarioListResponse,
    dependencies=[Depends(require_role("usuarios:read"))],
)
async def list_usuarios(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    activo: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
) -> schemas.UsuarioListResponse:
    # superadmin (empresa_id = None) ve todos; admin ve solo los de su empresa
    empresa_id = request.state.empresa_id
    usuarios, total = await service.listar_usuarios(
        db=db,
        empresa_id=empresa_id,
        skip=skip,
        limit=limit,
        activo=activo,
    )
    return schemas.UsuarioListResponse(
        items=[_to_public(u) for u in usuarios],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.put(
    "/{usuario_id}",
    response_model=schemas.UsuarioPublic,
    dependencies=[Depends(require_role("usuarios:update"))],
)
async def update_usuario(
    request: Request,
    usuario_id: str,
    payload: schemas.UsuarioUpdate,
    db: AsyncSession = Depends(get_db),
) -> schemas.UsuarioPublic:
    empresa_id = request.state.empresa_id
    current_user: Usuario = request.state.current_user
    usuario = await service.actualizar_usuario(
        db=db,
        current_user=current_user,
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        nombre=payload.nombre,
        apellido=payload.apellido,
        email=payload.email,
        rol_id=payload.rol_id,
        activo=payload.activo,
    )
    return _to_public(usuario)


@router.patch(
    "/{usuario_id}/desactivar",
    response_model=schemas.UsuarioPublic,
    dependencies=[Depends(require_role("usuarios:delete"))],
)
async def deactivate_usuario(
    request: Request,
    usuario_id: str,
    db: AsyncSession = Depends(get_db),
) -> schemas.UsuarioPublic:
    empresa_id = request.state.empresa_id
    usuario = await service.desactivar_usuario(db, empresa_id, usuario_id)
    return _to_public(usuario)


@router.patch(
    "/{usuario_id}/reactivar",
    response_model=schemas.UsuarioPublic,
    dependencies=[Depends(require_role("usuarios:update"))],
)
async def reactivate_usuario(
    request: Request,
    usuario_id: str,
    db: AsyncSession = Depends(get_db),
) -> schemas.UsuarioPublic:
    empresa_id = request.state.empresa_id
    usuario = await service.reactivar_usuario(db, empresa_id, usuario_id)
    return _to_public(usuario)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _to_public(usuario: Usuario) -> schemas.UsuarioPublic:
    return schemas.UsuarioPublic(
        id=usuario.id,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        rol=usuario.rol.nombre if usuario.rol else None,
        activo=usuario.activo,
        empresa_id=usuario.empresa_id,
        ultimo_acceso=usuario.ultimo_acceso,
        created_at=usuario.created_at,
        updated_at=usuario.updated_at,
    )
