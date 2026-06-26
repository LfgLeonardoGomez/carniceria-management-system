import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.auth.models import Usuario, Rol, Empresa
from src.core.security import hash_password, create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _crear_empresa(db: AsyncSession, nombre: str = "Carnicería Test", activa: bool = True) -> Empresa:
    empresa = Empresa(nombre_comercial=nombre, activa=activa)
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


def _auth_header(usuario: Usuario, rol_nombre: str = "admin", empresa_id=None):
    token = create_access_token({
        "sub": str(usuario.id),
        "empresa_id": str(empresa_id or usuario.empresa_id) if (empresa_id or usuario.empresa_id) else None,
        "rol": rol_nombre,
    })
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# TASK-6.1: Login de usuario desactivado -> 403
# ---------------------------------------------------------------------------
class TestLoginUsuarioInactivo:
    async def test_login_usuario_desactivado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session)
        await _crear_usuario(db_session, "inactive@basile.app", rol.id, empresa.id, activo=False)

        response = await client.post("/auth/login", json={
            "email": "inactive@basile.app",
            "contrasena": "Password123",
        })
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# TASK-6.2: CRUD con admin -> 200/201; otros roles -> 403
# ---------------------------------------------------------------------------
class TestCRUDUsuariosAdmin:
    async def test_crear_usuario_como_admin(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        rol_cajero = await _crear_rol(db_session, "cajero")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol_admin.id, empresa.id)

        response = await client.post("/usuarios", headers=_auth_header(admin, rol_nombre="admin", empresa_id=empresa.id), json={
            "nombre": "Nuevo",
            "apellido": "Cajero",
            "email": "nuevo@basile.app",
            "rol_id": str(rol_cajero.id),
        })
        assert response.status_code == 201
        data = response.json()
        assert data["usuario"]["email"] == "nuevo@basile.app"
        assert "contrasena_temporal" in data
        assert len(data["contrasena_temporal"]) >= 8

    async def test_listar_usuarios_como_admin(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "admin")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        await _crear_usuario(db_session, "u1@basile.app", rol.id, empresa.id)
        await _crear_usuario(db_session, "u2@basile.app", rol.id, empresa.id)

        response = await client.get("/usuarios", headers=_auth_header(admin, rol_nombre="admin", empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    async def test_actualizar_usuario_como_admin(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "admin")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        u = await _crear_usuario(db_session, "target@basile.app", rol.id, empresa.id, nombre="Viejo")

        response = await client.put(f"/usuarios/{u.id}", headers=_auth_header(admin, rol_nombre="admin", empresa_id=empresa.id), json={
            "nombre": "Nuevo",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Nuevo"

    async def test_desactivar_usuario_como_admin(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        rol_cajero = await _crear_rol(db_session, "cajero")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol_admin.id, empresa.id)
        u = await _crear_usuario(db_session, "cajero@basile.app", rol_cajero.id, empresa.id)

        response = await client.patch(f"/usuarios/{u.id}/desactivar", headers=_auth_header(admin, rol_nombre="admin", empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["activo"] is False

    async def test_reactivar_usuario_como_admin(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        rol_cajero = await _crear_rol(db_session, "cajero")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol_admin.id, empresa.id)
        u = await _crear_usuario(db_session, "cajero@basile.app", rol_cajero.id, empresa.id, activo=False)

        response = await client.patch(f"/usuarios/{u.id}/reactivar", headers=_auth_header(admin, rol_nombre="admin", empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["activo"] is True


class TestCRUDUsuariosNoAdmin:
    async def test_cajero_no_puede_crear_usuario(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_cajero = await _crear_rol(db_session, "cajero")
        cajero = await _crear_usuario(db_session, "cajero@basile.app", rol_cajero.id, empresa.id)

        response = await client.post("/usuarios", headers=_auth_header(cajero, rol_nombre="cajero", empresa_id=empresa.id), json={
            "nombre": "Hack",
            "apellido": "User",
            "email": "hack@basile.app",
            "rol_id": str(rol_cajero.id),
        })
        assert response.status_code == 403

    async def test_encargado_no_puede_listar_usuarios(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_encargado = await _crear_rol(db_session, "encargado")
        encargado = await _crear_usuario(db_session, "encargado@basile.app", rol_encargado.id, empresa.id)

        response = await client.get("/usuarios", headers=_auth_header(encargado, rol_nombre="encargado", empresa_id=empresa.id))
        assert response.status_code == 403

    async def test_vendedor_no_puede_actualizar_usuario(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_vendedor = await _crear_rol(db_session, "vendedor")
        rol_admin = await _crear_rol(db_session, "admin")
        vendedor = await _crear_usuario(db_session, "vendedor@basile.app", rol_vendedor.id, empresa.id)
        admin = await _crear_usuario(db_session, "admin@basile.app", rol_admin.id, empresa.id)

        response = await client.put(f"/usuarios/{admin.id}", headers=_auth_header(vendedor, rol_nombre="vendedor", empresa_id=empresa.id), json={
            "nombre": "Hack",
        })
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# TASK-6.3: Protección del último admin -> 409
# ---------------------------------------------------------------------------
class TestProteccionUltimoAdmin:
    async def test_desactivar_ultimo_admin_409(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        admin = await _crear_usuario(db_session, "unico@basile.app", rol_admin.id, empresa.id)

        response = await client.patch(f"/usuarios/{admin.id}/desactivar", headers=_auth_header(admin, rol_nombre="admin", empresa_id=empresa.id))
        assert response.status_code == 409
        assert "administrador" in response.json()["detail"].lower()

    async def test_cambiar_rol_ultimo_admin_409(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        rol_cajero = await _crear_rol(db_session, "cajero")
        admin = await _crear_usuario(db_session, "unico@basile.app", rol_admin.id, empresa.id)

        response = await client.put(f"/usuarios/{admin.id}", headers=_auth_header(admin, rol_nombre="admin", empresa_id=empresa.id), json={
            "rol_id": str(rol_cajero.id),
        })
        assert response.status_code == 409
        assert "administrador" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# TASK-6.4: Aislamiento multi-tenant
# ---------------------------------------------------------------------------
class TestAislamientoMultiTenant:
    async def test_admin_a_no_ve_usuarios_de_b(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        rol = await _crear_rol(db_session, "admin")
        admin_a = await _crear_usuario(db_session, "admin_a@basile.app", rol.id, empresa_a.id)
        await _crear_usuario(db_session, "user_b@basile.app", rol.id, empresa_b.id)

        response = await client.get("/usuarios", headers=_auth_header(admin_a, rol_nombre="admin", empresa_id=empresa_a.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["email"] == "admin_a@basile.app"

    async def test_admin_a_no_puede_modificar_user_b(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        rol = await _crear_rol(db_session, "admin")
        admin_a = await _crear_usuario(db_session, "admin_a@basile.app", rol.id, empresa_a.id)
        user_b = await _crear_usuario(db_session, "user_b@basile.app", rol.id, empresa_b.id)

        response = await client.put(f"/usuarios/{user_b.id}", headers=_auth_header(admin_a, rol_nombre="admin", empresa_id=empresa_a.id), json={
            "nombre": "Hack",
        })
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# TASK-6.5: Email duplicado global -> 409
# ---------------------------------------------------------------------------
class TestEmailDuplicado:
    async def test_crear_usuario_email_duplicado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "admin")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        await _crear_usuario(db_session, "dup@basile.app", rol.id, empresa.id)

        response = await client.post("/usuarios", headers=_auth_header(admin, rol_nombre="admin", empresa_id=empresa.id), json={
            "nombre": "Otro",
            "apellido": "User",
            "email": "dup@basile.app",
            "rol_id": str(rol.id),
        })
        assert response.status_code == 409
        assert "email" in response.json()["detail"].lower()

    async def test_actualizar_email_duplicado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "admin")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        await _crear_usuario(db_session, "dup@basile.app", rol.id, empresa.id)
        u = await _crear_usuario(db_session, "target@basile.app", rol.id, empresa.id)

        response = await client.put(f"/usuarios/{u.id}", headers=_auth_header(admin, rol_nombre="admin", empresa_id=empresa.id), json={
            "email": "dup@basile.app",
        })
        assert response.status_code == 409


# ---------------------------------------------------------------------------
# TASK-6.6: /usuarios/me accesible por todos; /usuarios solo admin
# ---------------------------------------------------------------------------
class TestPerfilYUsuarios:
    async def test_perfil_propio_cualquier_rol(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_vendedor = await _crear_rol(db_session, "vendedor")
        vendedor = await _crear_usuario(db_session, "yo@basile.app", rol_vendedor.id, empresa.id, nombre="Yo", apellido="Mismo")

        response = await client.get("/usuarios/me", headers=_auth_header(vendedor, rol_nombre="vendedor", empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "yo@basile.app"
        assert data["nombre"] == "Yo"

    async def test_actualizar_perfil_propio_cualquier_rol(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_cajero = await _crear_rol(db_session, "cajero")
        cajero = await _crear_usuario(db_session, "cajero@basile.app", rol_cajero.id, empresa.id)

        response = await client.put("/usuarios/me", headers=_auth_header(cajero, rol_nombre="cajero", empresa_id=empresa.id), json={
            "nombre": "Nuevo Nombre",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Nuevo Nombre"

    async def test_usuarios_solo_admin(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_vendedor = await _crear_rol(db_session, "vendedor")
        vendedor = await _crear_usuario(db_session, "vend@basile.app", rol_vendedor.id, empresa.id)

        response = await client.get("/usuarios", headers=_auth_header(vendedor, rol_nombre="vendedor", empresa_id=empresa.id))
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# TASK-5.3: Rate limiting en creación de usuario
# ---------------------------------------------------------------------------
class TestRateLimitingCreacion:
    async def test_rate_limit_creacion_usuario(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        rol_cajero = await _crear_rol(db_session, "cajero")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol_admin.id, empresa.id)

        # Crear usuarios rápidamente hasta que alguno sea rate limited.
        # El límite es 10 req/min por IP; otros tests en el mismo proceso
        # pueden haber consumido parte de la ventana, por eso no hacemos
        # assertions rígidos sobre el número exacto.
        rate_limited = False
        for i in range(25):
            response = await client.post("/usuarios", headers=_auth_header(admin, rol_nombre="admin", empresa_id=empresa.id), json={
                "nombre": f"User{i}",
                "apellido": "Test",
                "email": f"rl{i}@basile.app",
                "rol_id": str(rol_cajero.id),
            })
            if response.status_code == 429:
                rate_limited = True
                break
            assert response.status_code == 201

        assert rate_limited, "Se esperaba que el rate limit bloqueara una solicitud"


# ---------------------------------------------------------------------------
# Extra: schemas con extra='forbid'
# ---------------------------------------------------------------------------
class TestSchemaExtraForbid:
    async def test_crear_usuario_con_campo_extra_rechazado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "admin")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        response = await client.post("/usuarios", headers=_auth_header(admin, rol_nombre="admin", empresa_id=empresa.id), json={
            "nombre": "Test",
            "apellido": "User",
            "email": "test@basile.app",
            "rol_id": str(rol.id),
            "extra_field": "should_fail",
        })
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Superadmin tests
# ---------------------------------------------------------------------------
class TestSuperadminCRUD:
    async def test_superadmin_crea_empresa(self, client: AsyncClient, db_session: AsyncSession):
        superadmin = await _crear_superadmin(db_session)

        response = await client.post("/empresas", headers=_auth_header(superadmin, rol_nombre="superadmin"), json={
            "nombre_comercial": "Nueva Empresa",
            "cuit": "30-12345678-9",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["nombre_comercial"] == "Nueva Empresa"

    async def test_superadmin_lista_todas_las_empresas(self, client: AsyncClient, db_session: AsyncSession):
        await _crear_empresa(db_session, "Empresa A")
        await _crear_empresa(db_session, "Empresa B")
        superadmin = await _crear_superadmin(db_session)

        response = await client.get("/empresas", headers=_auth_header(superadmin, rol_nombre="superadmin"))
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_admin_no_puede_crear_empresa(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol_admin.id, empresa.id)

        response = await client.post("/empresas", headers=_auth_header(admin, rol_nombre="admin", empresa_id=empresa.id), json={
            "nombre_comercial": "Hack",
        })
        assert response.status_code == 403

    async def test_superadmin_crea_admin(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        superadmin = await _crear_superadmin(db_session)
        rol_admin = await _crear_rol(db_session, "admin")

        response = await client.post("/usuarios", headers=_auth_header(superadmin, rol_nombre="superadmin"), json={
            "nombre": "Nuevo",
            "apellido": "Admin",
            "email": "nuevo_admin@basile.app",
            "rol_id": str(rol_admin.id),
            "empresa_id": str(empresa.id),
        })
        assert response.status_code == 201
        data = response.json()
        assert data["usuario"]["rol"] == "admin"

    async def test_superadmin_asigna_admin_a_empresa(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        superadmin = await _crear_superadmin(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol_admin.id, empresa.id)

        response = await client.put(f"/empresas/{empresa.id}", headers=_auth_header(superadmin, rol_nombre="superadmin"), json={
            "admin_id": str(admin.id),
        })
        assert response.status_code == 200
        data = response.json()
        assert data["admin_id"] == str(admin.id)

    async def test_superadmin_impersona(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        superadmin = await _crear_superadmin(db_session)

        response = await client.post("/soporte/impersonate", headers=_auth_header(superadmin, rol_nombre="superadmin"), json={
            "empresa_id": str(empresa.id),
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

        # Verificar claims del token
        from src.core.security import decode_token
        from src.config.settings import settings
        token = data["access_token"]
        payload = decode_token(token, secret=settings.jwt_secret, token_type="access")
        assert payload["rol"] == "admin"
        assert payload["original_role"] == "superadmin"
        assert payload["empresa_id"] == str(empresa.id)

    async def test_auditoria_impersonate(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        superadmin = await _crear_superadmin(db_session)

        response = await client.post("/soporte/impersonate", headers=_auth_header(superadmin, rol_nombre="superadmin"), json={
            "empresa_id": str(empresa.id),
        })
        assert response.status_code == 200

        # Verificar registro en auditoría
        from src.modules.auditoria.models import Auditoria
        result = await db_session.execute(
            select(Auditoria).where(Auditoria.accion == "IMPERSONATE_ADMIN")
        )
        auditoria = result.scalar_one_or_none()
        assert auditoria is not None
        assert auditoria.usuario_id == superadmin.id
        assert auditoria.empresa_id == empresa.id
