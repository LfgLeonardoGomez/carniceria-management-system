import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.modules.empresa.models import Empresa
from src.modules.auth.models import Usuario, Rol
from src.common.exceptions import NotFoundException, ForbiddenException, ConflictException
from src.common.rbac import normalize_rol


async def crear_empresa(
    db: AsyncSession,
    nombre_comercial: str,
    razon_social: Optional[str] = None,
    cuit: Optional[str] = None,
    domicilio: Optional[str] = None,
    telefono: Optional[str] = None,
    email: Optional[str] = None,
    admin_id: Optional[uuid.UUID] = None,
) -> Empresa:
    """Crea una nueva empresa. Solo superadmin puede ejecutar esta operación."""
    empresa = Empresa(
        nombre_comercial=nombre_comercial,
        razon_social=razon_social,
        cuit=cuit,
        domicilio=domicilio,
        telefono=telefono,
        email=email,
        admin_id=admin_id,
        activa=True,
    )
    db.add(empresa)
    await db.commit()
    await db.refresh(empresa)
    return empresa


async def listar_empresas(
    db: AsyncSession,
    empresa_id: Optional[uuid.UUID] = None,
) -> list[Empresa]:
    """Lista empresas. Si empresa_id es None (superadmin), lista todas.
    Si empresa_id está presente, devuelve solo esa empresa.
    """
    query = select(Empresa).order_by(Empresa.created_at.desc())
    if empresa_id is not None:
        query = query.where(Empresa.id == empresa_id)

    result = await db.execute(query)
    return list(result.scalars().all())


async def obtener_empresa(
    db: AsyncSession,
    empresa_id: uuid.UUID,
) -> Empresa:
    """Obtiene una empresa por ID."""
    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise NotFoundException("Empresa no encontrada")
    return empresa


async def actualizar_empresa(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    current_user: Usuario,
    nombre_comercial: Optional[str] = None,
    razon_social: Optional[str] = None,
    cuit: Optional[str] = None,
    domicilio: Optional[str] = None,
    telefono: Optional[str] = None,
    email: Optional[str] = None,
    datos_fiscales: Optional[dict] = None,
    configuracion_general: Optional[dict] = None,
    parametros_operativos: Optional[dict] = None,
    admin_id: Optional[uuid.UUID] = None,
    activa: Optional[bool] = None,
) -> Empresa:
    """Actualiza una empresa.

    - superadmin puede modificar cualquier empresa y asignar admin_id.
    - admin solo puede modificar la suya y NO puede cambiar admin_id.
    """
    empresa = await obtener_empresa(db, empresa_id)
    current_rol = normalize_rol(current_user.rol.nombre if current_user.rol else None)

    # Validar que admin solo modifique su propia empresa
    if current_rol == "admin":
        if current_user.empresa_id != empresa_id:
            raise ForbiddenException("No puede modificar otra empresa")
        # Admin no puede asignar admin_id
        if admin_id is not None:
            raise ForbiddenException("No tiene permiso para asignar administrador")

    # Validar que admin_id corresponda a un usuario con rol admin
    if admin_id is not None:
        result = await db.execute(
            select(Usuario)
            .options(selectinload(Usuario.rol))
            .where(Usuario.id == admin_id)
        )
        admin_user = result.scalar_one_or_none()
        if not admin_user:
            raise ConflictException("El usuario administrador no existe")
        if normalize_rol(admin_user.rol.nombre if admin_user.rol else None) != "admin":
            raise ConflictException("El usuario asignado debe tener rol 'admin'")
        empresa.admin_id = admin_id

    if nombre_comercial is not None:
        empresa.nombre_comercial = nombre_comercial
    if razon_social is not None:
        empresa.razon_social = razon_social
    if cuit is not None:
        empresa.cuit = cuit
    if domicilio is not None:
        empresa.domicilio = domicilio
    if telefono is not None:
        empresa.telefono = telefono
    if email is not None:
        empresa.email = email
    if activa is not None:
        empresa.activa = activa

    if datos_fiscales is not None:
        existing = empresa.datos_fiscales or {}
        existing.update(datos_fiscales)
        empresa.datos_fiscales = existing
    if configuracion_general is not None:
        existing = empresa.configuracion_general or {}
        existing.update(configuracion_general)
        empresa.configuracion_general = existing
    if parametros_operativos is not None:
        existing = empresa.parametros_operativos or {}
        existing.update(parametros_operativos)
        empresa.parametros_operativos = existing

    empresa.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(empresa)
    return empresa
