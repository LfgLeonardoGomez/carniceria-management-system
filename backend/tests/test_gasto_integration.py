"""
Integration tests for C-15 gastos — full CRUD + multi-tenant isolation + category/filter tests.

TDD order: RED (these tests are written BEFORE the production code exists).
"""
import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.models import Usuario, Rol, Empresa
from src.core.security import hash_password, create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _crear_empresa(db: AsyncSession, nombre: str = "Carnicería Test") -> Empresa:
    empresa = Empresa(nombre_comercial=nombre, activa=True)
    db.add(empresa)
    await db.commit()
    await db.refresh(empresa)
    return empresa


async def _crear_rol(db: AsyncSession, nombre: str = "Administrador") -> Rol:
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
) -> Usuario:
    u = Usuario(
        email=email,
        contrasena_hash=hash_password("Password123"),
        nombre="Test",
        apellido="User",
        rol_id=rol_id,
        activo=True,
        empresa_id=empresa_id,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


def _auth_header(usuario: Usuario, rol_nombre: str = "Administrador", empresa_id=None):
    token = create_access_token({
        "sub": str(usuario.id),
        "empresa_id": str(empresa_id or usuario.empresa_id),
        "rol": rol_nombre,
    })
    return {"Authorization": f"Bearer {token}"}


def _gasto_payload(**kwargs) -> dict:
    """Build a minimal valid gasto payload, accepting overrides."""
    defaults = {
        "fecha": "2026-01-15",
        "categoria": "alquiler",
        "descripcion": "Alquiler enero",
        "importe": "15000.00",
        "medio_pago": "transferencia",
    }
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# Tests: POST /gasto — crear gasto
# ---------------------------------------------------------------------------
class TestCrearGasto:
    async def test_crear_gasto_happy_path(self, client: AsyncClient, db_session: AsyncSession):
        """Admin can create a gasto and response contains all required fields."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        response = await client.post(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json=_gasto_payload(),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["categoria"] == "alquiler"
        assert data["importe"] == "15000.00"
        assert data["empresa_id"] == str(empresa.id)
        assert "id" in data

    async def test_crear_gasto_categoria_invalida_rechazada(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Category outside the fixed enum is rejected with 422."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        response = await client.post(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json=_gasto_payload(categoria="comida_para_perros"),
        )
        assert response.status_code == 422

    async def test_crear_gasto_todas_categorias_validas(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """All 11 valid categories are accepted."""
        valid_categories = [
            "alquiler", "empleados", "luz", "agua", "gas",
            "internet", "combustible", "impuestos", "mantenimiento",
            "insumos", "otros",
        ]
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        for cat in valid_categories:
            response = await client.post(
                "/gasto",
                headers=_auth_header(usuario, empresa_id=empresa.id),
                json=_gasto_payload(categoria=cat, descripcion=f"Gasto de {cat}"),
            )
            assert response.status_code == 201, (
                f"Category {cat} should be valid, got {response.status_code}: {response.text}"
            )

    async def test_crear_gasto_sin_descripcion_aceptado(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """descripcion is optional."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        payload = {
            "fecha": "2026-01-15",
            "categoria": "luz",
            "importe": "500.00",
            "medio_pago": "efectivo",
        }
        response = await client.post(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json=payload,
        )
        assert response.status_code == 201

    async def test_crear_gasto_importe_negativo_rechazado(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Negative importe is rejected."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        response = await client.post(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json=_gasto_payload(importe="-100.00"),
        )
        assert response.status_code == 422

    async def test_crear_gasto_campo_extra_rechazado(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Extra fields are rejected (extra='forbid')."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        response = await client.post(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json=_gasto_payload(campo_extra="no permitido"),
        )
        assert response.status_code == 422

    async def test_crear_gasto_sin_autenticacion(self, client: AsyncClient):
        """Unauthenticated request returns 401."""
        response = await client.post("/gasto", json=_gasto_payload())
        assert response.status_code == 401

    async def test_crear_gasto_rol_cajero_prohibido(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Cajero role does not have gastos:create permission."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Cajero")
        usuario = await _crear_usuario(db_session, "cajero@basile.app", rol.id, empresa.id)

        response = await client.post(
            "/gasto",
            headers=_auth_header(usuario, rol_nombre="Cajero", empresa_id=empresa.id),
            json=_gasto_payload(),
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Tests: GET /gasto — listar gastos
# ---------------------------------------------------------------------------
class TestListarGastos:
    async def test_listar_gastos_vacio(self, client: AsyncClient, db_session: AsyncSession):
        """Empty list when no gastos exist for empresa."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        response = await client.get(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_listar_gastos_con_datos(self, client: AsyncClient, db_session: AsyncSession):
        """Returns all gastos for the empresa."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        await client.post(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json=_gasto_payload(categoria="luz"),
        )
        await client.post(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json=_gasto_payload(categoria="agua"),
        )

        response = await client.get(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_filtrar_por_categoria(self, client: AsyncClient, db_session: AsyncSession):
        """Filtering by categoria returns only matching gastos."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        await client.post(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json=_gasto_payload(categoria="luz"),
        )
        await client.post(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json=_gasto_payload(categoria="agua"),
        )
        await client.post(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json=_gasto_payload(categoria="luz", descripcion="Segunda luz"),
        )

        response = await client.get(
            "/gasto?categoria=luz",
            headers=_auth_header(usuario, empresa_id=empresa.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        for item in data["items"]:
            assert item["categoria"] == "luz"

    async def test_filtrar_por_rango_fecha(self, client: AsyncClient, db_session: AsyncSession):
        """Filtering by fecha_desde / fecha_hasta narrows results."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        await client.post(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json=_gasto_payload(fecha="2026-01-10"),
        )
        await client.post(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json=_gasto_payload(fecha="2026-01-20"),
        )
        await client.post(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json=_gasto_payload(fecha="2026-02-05"),
        )

        response = await client.get(
            "/gasto?fecha_desde=2026-01-15&fecha_hasta=2026-01-31",
            headers=_auth_header(usuario, empresa_id=empresa.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["fecha"][:10] == "2026-01-20"

    async def test_aislamiento_multitenant(self, client: AsyncClient, db_session: AsyncSession):
        """Empresa A cannot see Empresa B's gastos."""
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        rol = await _crear_rol(db_session, "Administrador")
        usuario_a = await _crear_usuario(db_session, "admin_a@basile.app", rol.id, empresa_a.id)
        usuario_b = await _crear_usuario(db_session, "admin_b@basile.app", rol.id, empresa_b.id)

        # Create gasto for empresa B
        await client.post(
            "/gasto",
            headers=_auth_header(usuario_b, empresa_id=empresa_b.id),
            json=_gasto_payload(descripcion="Gasto de Empresa B"),
        )

        # empresa_a sees nothing
        response = await client.get(
            "/gasto",
            headers=_auth_header(usuario_a, empresa_id=empresa_a.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0


# ---------------------------------------------------------------------------
# Tests: GET /gasto/{id} — obtener gasto por id
# ---------------------------------------------------------------------------
class TestObtenerGasto:
    async def test_obtener_gasto_existente(self, client: AsyncClient, db_session: AsyncSession):
        """Can retrieve a gasto by its id."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        create_resp = await client.post(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json=_gasto_payload(),
        )
        gasto_id = create_resp.json()["id"]

        response = await client.get(
            f"/gasto/{gasto_id}",
            headers=_auth_header(usuario, empresa_id=empresa.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == gasto_id

    async def test_obtener_gasto_otra_empresa_404(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Cannot read a gasto belonging to another empresa."""
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        rol = await _crear_rol(db_session, "Administrador")
        usuario_a = await _crear_usuario(db_session, "admin_a@basile.app", rol.id, empresa_a.id)
        usuario_b = await _crear_usuario(db_session, "admin_b@basile.app", rol.id, empresa_b.id)

        create_resp = await client.post(
            "/gasto",
            headers=_auth_header(usuario_b, empresa_id=empresa_b.id),
            json=_gasto_payload(),
        )
        gasto_b_id = create_resp.json()["id"]

        response = await client.get(
            f"/gasto/{gasto_b_id}",
            headers=_auth_header(usuario_a, empresa_id=empresa_a.id),
        )
        assert response.status_code == 404

    async def test_obtener_gasto_inexistente_404(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Non-existent id returns 404."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        response = await client.get(
            f"/gasto/{uuid.uuid4()}",
            headers=_auth_header(usuario, empresa_id=empresa.id),
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests: PUT /gasto/{id} — actualizar gasto
# ---------------------------------------------------------------------------
class TestActualizarGasto:
    async def test_actualizar_gasto(self, client: AsyncClient, db_session: AsyncSession):
        """Can update an existing gasto."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        create_resp = await client.post(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json=_gasto_payload(),
        )
        gasto_id = create_resp.json()["id"]

        response = await client.put(
            f"/gasto/{gasto_id}",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"importe": "20000.00", "descripcion": "Alquiler enero actualizado"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["importe"] == "20000.00"
        assert data["descripcion"] == "Alquiler enero actualizado"

    async def test_actualizar_gasto_categoria_invalida(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Update with invalid category is rejected."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        create_resp = await client.post(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json=_gasto_payload(),
        )
        gasto_id = create_resp.json()["id"]

        response = await client.put(
            f"/gasto/{gasto_id}",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"categoria": "categoria_inexistente"},
        )
        assert response.status_code == 422

    async def test_actualizar_gasto_otra_empresa_404(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Cannot update a gasto from another empresa."""
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        rol = await _crear_rol(db_session, "Administrador")
        usuario_a = await _crear_usuario(db_session, "admin_a@basile.app", rol.id, empresa_a.id)
        usuario_b = await _crear_usuario(db_session, "admin_b@basile.app", rol.id, empresa_b.id)

        create_resp = await client.post(
            "/gasto",
            headers=_auth_header(usuario_b, empresa_id=empresa_b.id),
            json=_gasto_payload(),
        )
        gasto_b_id = create_resp.json()["id"]

        response = await client.put(
            f"/gasto/{gasto_b_id}",
            headers=_auth_header(usuario_a, empresa_id=empresa_a.id),
            json={"descripcion": "hack"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests: DELETE /gasto/{id} — eliminar gasto
# ---------------------------------------------------------------------------
class TestEliminarGasto:
    async def test_eliminar_gasto(self, client: AsyncClient, db_session: AsyncSession):
        """Admin can delete a gasto (hard delete)."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        create_resp = await client.post(
            "/gasto",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json=_gasto_payload(),
        )
        gasto_id = create_resp.json()["id"]

        response = await client.delete(
            f"/gasto/{gasto_id}",
            headers=_auth_header(usuario, empresa_id=empresa.id),
        )
        assert response.status_code == 204

        # Verify it's no longer retrievable
        get_response = await client.get(
            f"/gasto/{gasto_id}",
            headers=_auth_header(usuario, empresa_id=empresa.id),
        )
        assert get_response.status_code == 404

    async def test_eliminar_gasto_otra_empresa_404(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Cannot delete a gasto from another empresa."""
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        rol = await _crear_rol(db_session, "Administrador")
        usuario_a = await _crear_usuario(db_session, "admin_a@basile.app", rol.id, empresa_a.id)
        usuario_b = await _crear_usuario(db_session, "admin_b@basile.app", rol.id, empresa_b.id)

        create_resp = await client.post(
            "/gasto",
            headers=_auth_header(usuario_b, empresa_id=empresa_b.id),
            json=_gasto_payload(),
        )
        gasto_b_id = create_resp.json()["id"]

        response = await client.delete(
            f"/gasto/{gasto_b_id}",
            headers=_auth_header(usuario_a, empresa_id=empresa_a.id),
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests: schema validation (unit-level, no DB needed)
# ---------------------------------------------------------------------------
class TestGastoSchemas:
    def test_gasto_create_categoria_invalida(self):
        """GastoCreate rejects invalid category."""
        from src.modules.gasto.schemas import GastoCreate
        from decimal import Decimal as D
        import pytest as _pytest

        with _pytest.raises(Exception):
            GastoCreate(
                fecha=date(2026, 1, 15),
                categoria="no_existe",
                importe=D("100.00"),
                medio_pago="efectivo",
            )

    def test_gasto_create_categoria_valida(self):
        """GastoCreate accepts valid category."""
        from src.modules.gasto.schemas import GastoCreate
        from decimal import Decimal as D

        g = GastoCreate(
            fecha=date(2026, 1, 15),
            categoria="alquiler",
            importe=D("1500.00"),
            medio_pago="transferencia",
        )
        assert g.categoria == "alquiler"
        assert g.importe == D("1500.00")

    def test_gasto_create_importe_negativo_rechazado(self):
        """GastoCreate rejects negative importe."""
        from src.modules.gasto.schemas import GastoCreate
        from decimal import Decimal as D
        import pytest as _pytest

        with _pytest.raises(Exception):
            GastoCreate(
                fecha=date(2026, 1, 15),
                categoria="luz",
                importe=D("-50.00"),
                medio_pago="efectivo",
            )

    def test_gasto_create_extra_fields_forbidden(self):
        """GastoCreate with extra fields raises ValidationError."""
        from src.modules.gasto.schemas import GastoCreate
        from decimal import Decimal as D
        import pytest as _pytest

        with _pytest.raises(Exception):
            GastoCreate(
                fecha=date(2026, 1, 15),
                categoria="gas",
                importe=D("200.00"),
                medio_pago="efectivo",
                campo_extra="no permitido",
            )
