import uuid
import secrets
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.modules.auth.models import Usuario, Rol
from src.core.security import hash_password
from src.common.exceptions import ConflictException, NotFoundException, ForbiddenException
from src.common.rbac import normalize_rol

# Roles que un admin puede asignar (operativos)
ROLES_OPERATIVOS = {"encargado", "cajero", "vendedor"}


async def _reload_usuario(db: AsyncSession, usuario_id: uuid.UUID) -> Usuario:
    """Recarga un usuario con sus relaciones para evitar lazy-loading en async."""
    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.rol))
        .options(selectinload(Usuario.empresa))
        .where(Usuario.id == usuario_id)
    )
    return result.scalar_one()


async def _check_ultimo_admin(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    usuario_id: uuid.UUID,
    operacion: str,
) -> None:
    """Verifica que al desactivar o cambiar rol de un admin, quede al menos 1 admin activo.

    Lanza ConflictException si se viola la regla.
    """
    # Verificar si el usuario afectado es admin activo
    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.rol))
        .where(
            Usuario.id == usuario_id,
            Usuario.empresa_id == empresa_id,
            Usuario.activo == True,
        )
    )
    usuario = result.scalar_one_or_none()
    if not usuario or normalize_rol(usuario.rol.nombre if usuario.rol else None) != "admin":
        return  # No es admin, no hay problema

    # Contar cuántos admins activos quedarían excluyendo a este usuario
    count_result = await db.execute(
        select(func.count(Usuario.id))
        .join(Rol)
        .where(
            Usuario.empresa_id == empresa_id,
            Usuario.activo == True,
            Rol.nombre.in_(["admin", "Administrador"]),
            Usuario.id != usuario_id,
        )
    )
    admins_restantes = count_result.scalar_one()

    if admins_restantes < 1:
        raise ConflictException(
            f"No se puede {operacion} al único administrador activo. "
            "Debe existir al menos un administrador activo en la empresa."
        )


async def crear_usuario(
    db: AsyncSession,
    current_user: Usuario,
    nombre: str,
    apellido: str,
    email: str,
    rol_id: uuid.UUID,
    empresa_id: Optional[uuid.UUID] = None,
) -> tuple[Usuario, str]:
    """Crea un nuevo usuario validando permisos del creador.

    Reglas:
      - superadmin puede crear admin (con o sin empresa) y cualquier rol operativo.
      - admin solo puede crear roles operativos (encargado, cajero, vendedor).
      - admin fuerza empresa_id = current_user.empresa_id.

    Devuelve (usuario, contraseña_temporal).
    """
    # Validar email único global
    existing = await db.execute(select(Usuario).where(Usuario.email == email))
    if existing.scalar_one_or_none():
        raise ConflictException("El email ya está registrado en el sistema")

    # Validar que el rol exista
    rol_result = await db.execute(select(Rol).where(Rol.id == rol_id))
    rol = rol_result.scalar_one_or_none()
    if rol is None:
        raise ConflictException("Rol inválido")

    rol_nombre = normalize_rol(rol.nombre)
    current_rol_row = await db.get(Rol, current_user.rol_id)
    current_rol = normalize_rol(current_rol_row.nombre if current_rol_row else None)

    # Validar permisos de creación según rol del creador
    if current_rol == "superadmin":
        # superadmin puede crear cualquier rol, incluso admin
        target_empresa_id = empresa_id if empresa_id is not None else None
    elif current_rol == "admin":
        # admin solo puede crear roles operativos
        if rol_nombre not in ROLES_OPERATIVOS:
            raise ForbiddenException(
                f"No tiene permiso para crear usuarios con rol '{rol.nombre}'"
            )
        target_empresa_id = current_user.empresa_id
    else:
        raise ForbiddenException("No tiene permiso para crear usuarios")

    temp_password = secrets.token_urlsafe(12)
    usuario = Usuario(
        email=email,
        contrasena_hash=hash_password(temp_password),
        nombre=nombre,
        apellido=apellido,
        rol_id=rol_id,
        activo=True,
        empresa_id=target_empresa_id,
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    usuario = await _reload_usuario(db, usuario.id)
    return usuario, temp_password


async def listar_usuarios(
    db: AsyncSession,
    empresa_id: Optional[uuid.UUID],
    skip: int = 0,
    limit: int = 20,
    activo: Optional[bool] = None,
) -> tuple[list[Usuario], int]:
    """Lista usuarios. Si empresa_id es None (superadmin), lista todos."""
    where_clause = []
    if empresa_id is not None:
        where_clause.append(Usuario.empresa_id == empresa_id)

    if activo is not None:
        where_clause.append(Usuario.activo == activo)

    count_query = select(func.count(Usuario.id))
    if where_clause:
        count_query = count_query.where(*where_clause)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    query = (
        select(Usuario)
        .options(selectinload(Usuario.rol))
        .offset(skip)
        .limit(limit)
        .order_by(Usuario.created_at.desc())
    )
    if where_clause:
        query = query.where(*where_clause)

    result = await db.execute(query)
    usuarios = result.scalars().all()
    return list(usuarios), total


async def _get_usuario_de_empresa(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    usuario_id: uuid.UUID,
) -> Usuario:
    """Obtiene un usuario asegurando que pertenece a la empresa."""
    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.rol))
        .where(
            Usuario.id == usuario_id,
            Usuario.empresa_id == empresa_id,
        )
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise NotFoundException("Usuario no encontrado")
    return usuario


async def actualizar_usuario(
    db: AsyncSession,
    current_user: Usuario,
    empresa_id: uuid.UUID,
    usuario_id: uuid.UUID,
    nombre: Optional[str] = None,
    apellido: Optional[str] = None,
    email: Optional[str] = None,
    rol_id: Optional[uuid.UUID] = None,
    activo: Optional[bool] = None,
) -> Usuario:
    """Actualiza datos de un usuario. Valida email único y protege último admin.

    Un admin NO puede elevar un rol a 'admin' ni a 'superadmin'.
    """
    usuario = await _get_usuario_de_empresa(db, empresa_id, usuario_id)
    current_rol_row = await db.get(Rol, current_user.rol_id)
    current_rol = normalize_rol(current_rol_row.nombre if current_rol_row else None)

    # Si cambia el rol, proteger último admin y validar elevación
    if rol_id is not None and rol_id != usuario.rol_id:
        rol_result = await db.execute(select(Rol).where(Rol.id == rol_id))
        nuevo_rol = rol_result.scalar_one_or_none()
        if not nuevo_rol:
            raise ConflictException("Rol inválido")

        # Admin no puede elevar a admin ni superadmin
        nuevo_rol_canonico = normalize_rol(nuevo_rol.nombre)
        if current_rol == "admin" and nuevo_rol_canonico in ("admin", "superadmin"):
            raise ForbiddenException(
                "No tiene permiso para asignar el rol '{}'".format(nuevo_rol.nombre)
            )

        await _check_ultimo_admin(db, empresa_id, usuario_id, "cambiar el rol de")
        usuario.rol_id = rol_id

    if email is not None and email != usuario.email:
        existing = await db.execute(
            select(Usuario).where(Usuario.email == email, Usuario.id != usuario_id)
        )
        if existing.scalar_one_or_none():
            raise ConflictException("El email ya está registrado en el sistema")
        usuario.email = email

    if nombre is not None:
        usuario.nombre = nombre
    if apellido is not None:
        usuario.apellido = apellido
    if activo is not None and activo != usuario.activo:
        if not activo:
            await _check_ultimo_admin(db, empresa_id, usuario_id, "desactivar")
        usuario.activo = activo

    await db.commit()
    usuario = await _reload_usuario(db, usuario.id)
    return usuario


async def desactivar_usuario(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    usuario_id: uuid.UUID,
) -> Usuario:
    """Soft-delete de usuario con protección del último admin."""
    await _check_ultimo_admin(db, empresa_id, usuario_id, "desactivar")
    usuario = await _get_usuario_de_empresa(db, empresa_id, usuario_id)
    usuario.activo = False
    await db.commit()
    usuario = await _reload_usuario(db, usuario.id)
    return usuario


async def reactivar_usuario(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    usuario_id: uuid.UUID,
) -> Usuario:
    """Reactiva un usuario desactivado."""
    usuario = await _get_usuario_de_empresa(db, empresa_id, usuario_id)
    usuario.activo = True
    await db.commit()
    usuario = await _reload_usuario(db, usuario.id)
    return usuario


async def obtener_perfil_propio(
    db: AsyncSession,
    usuario_id: uuid.UUID,
) -> Usuario:
    """Obtiene el perfil del usuario autenticado."""
    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.rol))
        .options(selectinload(Usuario.empresa))
        .where(Usuario.id == usuario_id)
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise NotFoundException("Usuario no encontrado")
    return usuario


async def actualizar_perfil_propio(
    db: AsyncSession,
    usuario_id: uuid.UUID,
    nombre: Optional[str] = None,
    apellido: Optional[str] = None,
    email: Optional[str] = None,
    rol_id: Optional[uuid.UUID] = None,  # Ignorado intencionalmente
) -> Usuario:
    """Actualiza el perfil propio. Ignora rol_id si viene en el body."""
    usuario = await obtener_perfil_propio(db, usuario_id)

    if email is not None and email != usuario.email:
        existing = await db.execute(
            select(Usuario).where(Usuario.email == email, Usuario.id != usuario_id)
        )
        if existing.scalar_one_or_none():
            raise ConflictException("El email ya está en uso")
        usuario.email = email

    if nombre is not None:
        usuario.nombre = nombre
    if apellido is not None:
        usuario.apellido = apellido

    await db.commit()
    usuario = await _reload_usuario(db, usuario.id)
    return usuario
