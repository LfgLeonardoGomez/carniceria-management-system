import uuid
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.auth.models import Usuario, Rol, Empresa
from src.modules.usuario.service import (
    crear_usuario,
    listar_usuarios,
    actualizar_usuario,
    desactivar_usuario,
    reactivar_usuario,
    obtener_perfil_propio,
    actualizar_perfil_propio,
    _check_ultimo_admin,
)
from src.core.security import verify_password
from src.common.exceptions import ConflictException, NotFoundException, ForbiddenException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _crear_empresa(db: AsyncSession, nombre: str = "Carnicería Test") -> Empresa:
    empresa = Empresa(nombre_comercial=nombre, activa=True)
    db.add(empresa)
    await db.commit()
    await db.refresh(empresa)
    return empresa


async def _crear_rol(db: AsyncSession, nombre: str = "admin") -> Rol:
    rol = Rol(nombre=nombre)
    db.add(rol)
    await db.commit()
    await db.refresh(rol)
    return rol


async def _crear_usuario(
    db: AsyncSession,
    email: str,
    rol_id: uuid.UUID,
    empresa_id: uuid.UUID,
    activo: bool = True,
    nombre: str = "Test",
    apellido: str = "User",
) -> Usuario:
    from src.core.security import hash_password
    u = Usuario(
        email=email,
        contrasena_hash=hash_password("Password123"),
        nombre=nombre,
        apellido=apellido,
        rol_id=rol_id,
        activo=activo,
        empresa_id=empresa_id,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


async def _crear_superadmin(db: AsyncSession, email: str = "superadmin@basile.app") -> Usuario:
    from src.core.security import hash_password
    rol = Rol(nombre="superadmin")
    db.add(rol)
    await db.commit()
    await db.refresh(rol)
    u = Usuario(
        email=email,
        contrasena_hash=hash_password("Password123"),
        nombre="Super",
        apellido="Admin",
        rol_id=rol.id,
        activo=True,
        empresa_id=None,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


# ---------------------------------------------------------------------------
# Tests: crear_usuario
# ---------------------------------------------------------------------------
class TestCrearUsuario:
    async def test_crear_usuario_exitoso(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol_admin.id, empresa.id)

        rol_cajero = await _crear_rol(db_session, "cajero")
        nuevo, temp_pass = await crear_usuario(
            db=db_session,
            current_user=admin,
            nombre="Nuevo",
            apellido="Usuario",
            email="nuevo@basile.app",
            rol_id=rol_cajero.id,
        )

        assert nuevo.email == "nuevo@basile.app"
        assert nuevo.empresa_id == empresa.id
        assert nuevo.rol_id == rol_cajero.id
        assert nuevo.activo is True
        assert verify_password(temp_pass, nuevo.contrasena_hash) is True
        assert len(temp_pass) >= 8

    async def test_email_duplicado_global(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "admin")
        await _crear_usuario(db_session, "dup@basile.app", rol.id, empresa.id)

        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        with pytest.raises(ConflictException) as exc:
            await crear_usuario(
                db=db_session,
                current_user=admin,
                nombre="Otro",
                apellido="User",
                email="dup@basile.app",
                rol_id=rol.id,
            )
        assert "email" in str(exc.value.message).lower()

    async def test_rol_invalido(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "admin")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        fake_rol_id = uuid.uuid4()
        with pytest.raises(ConflictException):
            await crear_usuario(
                db=db_session,
                current_user=admin,
                nombre="Otro",
                apellido="User",
                email="otro@basile.app",
                rol_id=fake_rol_id,
            )

    async def test_admin_no_puede_crear_admin(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol_admin.id, empresa.id)

        with pytest.raises(ForbiddenException):
            await crear_usuario(
                db=db_session,
                current_user=admin,
                nombre="Otro",
                apellido="Admin",
                email="otro_admin@basile.app",
                rol_id=rol_admin.id,
            )

    async def test_superadmin_puede_crear_admin(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        superadmin = await _crear_superadmin(db_session)
        rol_admin = await _crear_rol(db_session, "admin")

        nuevo, temp_pass = await crear_usuario(
            db=db_session,
            current_user=superadmin,
            nombre="Nuevo",
            apellido="Admin",
            email="nuevo_admin@basile.app",
            rol_id=rol_admin.id,
            empresa_id=empresa.id,
        )
        assert nuevo.rol_id == rol_admin.id
        assert nuevo.empresa_id == empresa.id

    async def test_superadmin_puede_crear_admin_sin_empresa(self, db_session: AsyncSession):
        superadmin = await _crear_superadmin(db_session)
        rol_admin = await _crear_rol(db_session, "admin")

        nuevo, temp_pass = await crear_usuario(
            db=db_session,
            current_user=superadmin,
            nombre="Nuevo",
            apellido="Admin",
            email="nuevo_admin@basile.app",
            rol_id=rol_admin.id,
        )
        assert nuevo.rol_id == rol_admin.id
        assert nuevo.empresa_id is None


# ---------------------------------------------------------------------------
# Tests: listar_usuarios
# ---------------------------------------------------------------------------
class TestListarUsuarios:
    async def test_listar_filtra_por_empresa(self, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        rol = await _crear_rol(db_session, "admin")

        await _crear_usuario(db_session, "a1@basile.app", rol.id, empresa_a.id)
        await _crear_usuario(db_session, "a2@basile.app", rol.id, empresa_a.id)
        await _crear_usuario(db_session, "b1@basile.app", rol.id, empresa_b.id)

        resultados, total = await listar_usuarios(db_session, empresa_a.id, skip=0, limit=20)
        assert total == 2
        assert all(u.empresa_id == empresa_a.id for u in resultados)

    async def test_superadmin_ve_todos(self, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        rol = await _crear_rol(db_session, "admin")

        await _crear_usuario(db_session, "a1@basile.app", rol.id, empresa_a.id)
        await _crear_usuario(db_session, "b1@basile.app", rol.id, empresa_b.id)

        resultados, total = await listar_usuarios(db_session, None, skip=0, limit=20)
        assert total == 2

    async def test_listar_filtro_activo(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "admin")
        await _crear_usuario(db_session, "activo@basile.app", rol.id, empresa.id, activo=True)
        await _crear_usuario(db_session, "inactivo@basile.app", rol.id, empresa.id, activo=False)

        resultados, total = await listar_usuarios(db_session, empresa.id, skip=0, limit=20, activo=True)
        assert total == 1
        assert resultados[0].email == "activo@basile.app"

    async def test_listar_paginacion(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "admin")
        for i in range(5):
            await _crear_usuario(db_session, f"u{i}@basile.app", rol.id, empresa.id)

        resultados, total = await listar_usuarios(db_session, empresa.id, skip=0, limit=3)
        assert total == 5
        assert len(resultados) == 3

        resultados, total = await listar_usuarios(db_session, empresa.id, skip=3, limit=3)
        assert len(resultados) == 2


# ---------------------------------------------------------------------------
# Tests: actualizar_usuario
# ---------------------------------------------------------------------------
class TestActualizarUsuario:
    async def test_actualizar_nombre_y_email(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "admin")
        u = await _crear_usuario(db_session, "viejo@basile.app", rol.id, empresa.id)

        actualizado = await actualizar_usuario(
            db=db_session,
            current_user=u,
            empresa_id=empresa.id,
            usuario_id=u.id,
            nombre="Nuevo Nombre",
            email="nuevo@basile.app",
        )
        assert actualizado.nombre == "Nuevo Nombre"
        assert actualizado.email == "nuevo@basile.app"

    async def test_actualizar_email_duplicado(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "admin")
        await _crear_usuario(db_session, "existente@basile.app", rol.id, empresa.id)
        u = await _crear_usuario(db_session, "cambio@basile.app", rol.id, empresa.id)

        with pytest.raises(ConflictException):
            await actualizar_usuario(
                db=db_session,
                current_user=u,
                empresa_id=empresa.id,
                usuario_id=u.id,
                email="existente@basile.app",
            )

    async def test_actualizar_cambio_rol(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        rol_cajero = await _crear_rol(db_session, "cajero")
        # Dos admins para evitar protección
        await _crear_usuario(db_session, "otro_admin@basile.app", rol_admin.id, empresa.id)
        u = await _crear_usuario(db_session, "user@basile.app", rol_admin.id, empresa.id)

        actualizado = await actualizar_usuario(
            db=db_session,
            current_user=u,
            empresa_id=empresa.id,
            usuario_id=u.id,
            rol_id=rol_cajero.id,
        )
        assert actualizado.rol_id == rol_cajero.id

    async def test_admin_no_puede_elevar_a_admin(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        rol_cajero = await _crear_rol(db_session, "cajero")
        await _crear_usuario(db_session, "otro_admin@basile.app", rol_admin.id, empresa.id)
        admin = await _crear_usuario(db_session, "admin@basile.app", rol_admin.id, empresa.id)
        cajero = await _crear_usuario(db_session, "cajero@basile.app", rol_cajero.id, empresa.id)

        with pytest.raises(ForbiddenException):
            await actualizar_usuario(
                db=db_session,
                current_user=admin,
                empresa_id=empresa.id,
                usuario_id=cajero.id,
                rol_id=rol_admin.id,
            )


# ---------------------------------------------------------------------------
# Tests: protección del último admin
# ---------------------------------------------------------------------------
class TestProteccionUltimoAdmin:
    async def test_check_ultimo_admin_dos_admins_ok(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        await _crear_usuario(db_session, "admin1@basile.app", rol_admin.id, empresa.id)
        u2 = await _crear_usuario(db_session, "admin2@basile.app", rol_admin.id, empresa.id)

        # Debería pasar sin excepción
        await _check_ultimo_admin(db_session, empresa.id, u2.id, "desactivar")

    async def test_check_ultimo_admin_unico_falla(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        u = await _crear_usuario(db_session, "unico@basile.app", rol_admin.id, empresa.id)

        with pytest.raises(ConflictException) as exc:
            await _check_ultimo_admin(db_session, empresa.id, u.id, "desactivar")
        assert "al menos un administrador" in str(exc.value.message).lower()

    async def test_desactivar_ultimo_admin_devuelve_409(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        u = await _crear_usuario(db_session, "unico@basile.app", rol_admin.id, empresa.id)

        with pytest.raises(ConflictException):
            await desactivar_usuario(db_session, empresa.id, u.id)

    async def test_cambiar_rol_ultimo_admin_devuelve_409(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        rol_cajero = await _crear_rol(db_session, "cajero")
        u = await _crear_usuario(db_session, "unico@basile.app", rol_admin.id, empresa.id)

        with pytest.raises(ConflictException):
            await actualizar_usuario(
                db=db_session,
                current_user=u,
                empresa_id=empresa.id,
                usuario_id=u.id,
                rol_id=rol_cajero.id,
            )

    async def test_desactivar_no_admin_sin_proteccion(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_cajero = await _crear_rol(db_session, "cajero")
        u = await _crear_usuario(db_session, "cajero@basile.app", rol_cajero.id, empresa.id)

        # No debería fallar porque no es admin
        result = await desactivar_usuario(db_session, empresa.id, u.id)
        assert result.activo is False


# ---------------------------------------------------------------------------
# Tests: reactivar_usuario
# ---------------------------------------------------------------------------
class TestReactivarUsuario:
    async def test_reactivar_usuario_inactivo(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "admin")
        u = await _crear_usuario(db_session, "inactivo@basile.app", rol.id, empresa.id, activo=False)

        result = await reactivar_usuario(db_session, empresa.id, u.id)
        assert result.activo is True

    async def test_reactivar_idempotente(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "admin")
        u = await _crear_usuario(db_session, "activo@basile.app", rol.id, empresa.id, activo=True)

        result = await reactivar_usuario(db_session, empresa.id, u.id)
        assert result.activo is True


# ---------------------------------------------------------------------------
# Tests: perfil propio
# ---------------------------------------------------------------------------
class TestPerfilPropio:
    async def test_obtener_perfil(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "admin")
        u = await _crear_usuario(db_session, "yo@basile.app", rol.id, empresa.id, nombre="Yo", apellido="Mismo")

        perfil = await obtener_perfil_propio(db_session, u.id)
        assert perfil.email == "yo@basile.app"
        assert perfil.nombre == "Yo"

    async def test_actualizar_perfil_ignora_rol(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "admin")
        u = await _crear_usuario(db_session, "yo@basile.app", rol.id, empresa.id)
        otro_rol = await _crear_rol(db_session, "cajero")

        actualizado = await actualizar_perfil_propio(
            db=db_session,
            usuario_id=u.id,
            nombre="Nuevo",
            rol_id=otro_rol.id,  # Debería ser ignorado
        )
        assert actualizado.nombre == "Nuevo"
        assert actualizado.rol_id == rol.id  # No cambió

    async def test_actualizar_perfil_email_unico(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "admin")
        await _crear_usuario(db_session, "otro@basile.app", rol.id, empresa.id)
        u = await _crear_usuario(db_session, "yo@basile.app", rol.id, empresa.id)

        with pytest.raises(ConflictException):
            await actualizar_perfil_propio(
                db=db_session,
                usuario_id=u.id,
                email="otro@basile.app",
            )


# ---------------------------------------------------------------------------
# Tests: seguridad cross-tenant
# ---------------------------------------------------------------------------
class TestAislamientoMultiTenant:
    async def test_no_puede_actualizar_usuario_de_otra_empresa(self, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "A")
        empresa_b = await _crear_empresa(db_session, "B")
        rol = await _crear_rol(db_session, "admin")
        u_b = await _crear_usuario(db_session, "b@basile.app", rol.id, empresa_b.id)

        with pytest.raises(NotFoundException):
            await actualizar_usuario(
                db=db_session,
                current_user=u_b,
                empresa_id=empresa_a.id,
                usuario_id=u_b.id,
                nombre="Hack",
            )

    async def test_no_puede_desactivar_usuario_de_otra_empresa(self, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "A")
        empresa_b = await _crear_empresa(db_session, "B")
        rol = await _crear_rol(db_session, "admin")
        u_b = await _crear_usuario(db_session, "b@basile.app", rol.id, empresa_b.id)

        with pytest.raises(NotFoundException):
            await desactivar_usuario(db_session, empresa_a.id, u_b.id)
