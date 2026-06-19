import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Request, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.config.database import get_db
from src.config.settings import settings
from src.common.rbac import require_role, normalize_rol
from src.modules.empresa.models import Empresa
from src.modules.empresa.schemas import EmpresaPublic, EmpresaUpdate, LogoUploadResponse
from src.modules.empresa import service as empresa_service
from src.modules.empresa.storage import delete_existing_logo, save_logo
from src.common.exceptions import BasileException, NotFoundException

router = APIRouter()


# ---------------------------------------------------------------------------
# TASK-2.1: GET /empresas/me
# ---------------------------------------------------------------------------
@router.get("/me", response_model=EmpresaPublic, dependencies=[Depends(require_role("empresas:admin"))])
async def get_empresa_me(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> EmpresaPublic:
    empresa_id = request.state.empresa_id
    if empresa_id is None:
        raise NotFoundException("Empresa no encontrada")
    empresa = await empresa_service.obtener_empresa(db, empresa_id)
    return EmpresaPublic.model_validate(empresa.model_dump())


# ---------------------------------------------------------------------------
# TASK-2.2: PUT /empresas/me
# ---------------------------------------------------------------------------
@router.put("/me", response_model=EmpresaPublic, dependencies=[Depends(require_role("empresas:admin"))])
async def update_empresa_me(
    request: Request,
    payload: EmpresaUpdate,
    db: AsyncSession = Depends(get_db),
) -> EmpresaPublic:
    empresa_id = request.state.empresa_id
    if empresa_id is None:
        raise NotFoundException("Empresa no encontrada")
    current_user = request.state.current_user
    empresa = await empresa_service.actualizar_empresa(
        db=db,
        empresa_id=empresa_id,
        current_user=current_user,
        **payload.model_dump(exclude_unset=True),
    )
    return EmpresaPublic.model_validate(empresa.model_dump())


# ---------------------------------------------------------------------------
# TASK-2.3: PATCH /empresas/me/desactivar
# ---------------------------------------------------------------------------
@router.patch("/me/desactivar", response_model=EmpresaPublic, dependencies=[Depends(require_role("empresas:admin"))])
async def desactivar_empresa_me(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> EmpresaPublic:
    empresa_id = request.state.empresa_id
    if empresa_id is None:
        raise NotFoundException("Empresa no encontrada")
    current_user = request.state.current_user
    empresa = await empresa_service.actualizar_empresa(
        db=db,
        empresa_id=empresa_id,
        current_user=current_user,
        activa=False,
    )
    return EmpresaPublic.model_validate(empresa.model_dump())


# ---------------------------------------------------------------------------
# TASK-2.3b: PATCH /empresas/me/reactivar
# ---------------------------------------------------------------------------
@router.patch("/me/reactivar", response_model=EmpresaPublic, dependencies=[Depends(require_role("empresas:admin"))])
async def reactivar_empresa_me(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> EmpresaPublic:
    empresa_id = request.state.empresa_id
    if empresa_id is None:
        raise NotFoundException("Empresa no encontrada")
    current_user = request.state.current_user
    empresa = await empresa_service.actualizar_empresa(
        db=db,
        empresa_id=empresa_id,
        current_user=current_user,
        activa=True,
    )
    return EmpresaPublic.model_validate(empresa.model_dump())


# ---------------------------------------------------------------------------
# TASK-2.4: POST /empresas/me/logo
# ---------------------------------------------------------------------------
class _LogoUploadResponse(LogoUploadResponse):
    pass


@router.post("/me/logo", response_model=LogoUploadResponse, dependencies=[Depends(require_role("empresas:admin"))])
async def upload_logo(
    request: Request,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> LogoUploadResponse:
    empresa_id = request.state.empresa_id
    if empresa_id is None:
        raise NotFoundException("Empresa no encontrada")
    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa: Optional[Empresa] = result.scalar_one_or_none()
    if not empresa:
        raise NotFoundException("Empresa no encontrada")

    upload_path = Path(settings.upload_path)
    try:
        logo_url = await save_logo(empresa_id, file, upload_path)
    except ValueError as exc:
        if "excede el tamaño" in str(exc):
            raise BasileException(str(exc), status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        raise BasileException(str(exc), status_code=status.HTTP_400_BAD_REQUEST)

    empresa.logo_url = logo_url
    empresa.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(empresa)

    return LogoUploadResponse(
        logo_url=logo_url,
        filename=Path(logo_url).name,
        content_type=file.content_type or "application/octet-stream",
    )


# ---------------------------------------------------------------------------
# Superadmin endpoints
# ---------------------------------------------------------------------------
class EmpresaCreate(BaseModel):
    nombre_comercial: str
    razon_social: Optional[str] = None
    cuit: Optional[str] = None
    domicilio: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    admin_id: Optional[str] = None

    model_config = {"extra": "forbid"}


@router.post(
    "",
    response_model=EmpresaPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("empresas:create"))],
)
async def create_empresa(
    payload: EmpresaCreate,
    db: AsyncSession = Depends(get_db),
) -> EmpresaPublic:
    admin_uuid = uuid.UUID(payload.admin_id) if payload.admin_id else None
    empresa = await empresa_service.crear_empresa(
        db=db,
        nombre_comercial=payload.nombre_comercial,
        razon_social=payload.razon_social,
        cuit=payload.cuit,
        domicilio=payload.domicilio,
        telefono=payload.telefono,
        email=payload.email,
        admin_id=admin_uuid,
    )
    return EmpresaPublic.model_validate(empresa.model_dump())


@router.get(
    "",
    response_model=list[EmpresaPublic],
    dependencies=[Depends(require_role("empresas:read"))],
)
async def list_empresas(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> list[EmpresaPublic]:
    empresa_id = request.state.empresa_id
    empresas = await empresa_service.listar_empresas(db, empresa_id=empresa_id)
    return [EmpresaPublic.model_validate(e.model_dump()) for e in empresas]


@router.get(
    "/{empresa_id}",
    response_model=EmpresaPublic,
    dependencies=[Depends(require_role("empresas:read"))],
)
async def get_empresa(
    request: Request,
    empresa_id: str,
    db: AsyncSession = Depends(get_db),
) -> EmpresaPublic:
    current_rol = normalize_rol(request.state.current_user.rol.nombre if request.state.current_user.rol else None)
    if current_rol == "admin":
        if request.state.empresa_id != uuid.UUID(empresa_id):
            raise ForbiddenException("No puede ver otra empresa")
    empresa = await empresa_service.obtener_empresa(db, uuid.UUID(empresa_id))
    return EmpresaPublic.model_validate(empresa.model_dump())


@router.put(
    "/{empresa_id}",
    response_model=EmpresaPublic,
    dependencies=[Depends(require_role("empresas:update"))],
)
async def update_empresa(
    request: Request,
    empresa_id: str,
    payload: EmpresaUpdate,
    db: AsyncSession = Depends(get_db),
) -> EmpresaPublic:
    current_user = request.state.current_user
    empresa = await empresa_service.actualizar_empresa(
        db=db,
        empresa_id=uuid.UUID(empresa_id),
        current_user=current_user,
        **payload.model_dump(exclude_unset=True),
    )
    return EmpresaPublic.model_validate(empresa.model_dump())
