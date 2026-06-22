import uuid
from decimal import Decimal
from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.auth.models import Usuario, Rol, Empresa
from src.modules.producto.models import Producto
from src.modules.stock.models import MovimientoStock
from src.modules.caja.models import Caja, MovimientoCaja
from src.modules.cliente.models import Cliente
from src.modules.cuenta_corriente.models import CuentaCorriente  # noqa: F401 (register table in metadata)
from src.common.exceptions import ConflictException
from src.core.security import hash_password, create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _crear_empresa(db: AsyncSession, nombre: str = "Carniceria Test") -> Empresa:
    empresa = Empresa(nombre_comercial=nombre, activa=True)
    db.add(empresa)
    await db.commit()
    await db.refresh(empresa)
    return empresa


async def _crear_rol(db: AsyncSession, nombre: str = "cajero", empresa_id=None) -> Rol:
    rol = Rol(nombre=nombre, empresa_id=empresa_id)
    db.add(rol)
    await db.commit()
    await db.refresh(rol)
    return rol


async def _crear_usuario(
    db: AsyncSession,
    email: str = "cajero@basile.app",
    empresa_id=None,
    rol_id=None,
) -> Usuario:
    usuario = Usuario(
        email=email,
        contrasena_hash=hash_password("Password123"),
        nombre="Test",
        apellido="User",
        rol_id=rol_id,
        activo=True,
        empresa_id=empresa_id,
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario


def _auth_header(usuario: Usuario, rol_nombre: str = "cajero", empresa_id=None):
    token = create_access_token({
        "sub": str(usuario.id),
        "empresa_id": str(empresa_id or usuario.empresa_id),
        "rol": rol_nombre,
    })
    return {"Authorization": f"Bearer {token}"}


async def _crear_producto(db: AsyncSession, empresa_id: uuid.UUID, plu: str = "001") -> Producto:
    producto = Producto(
        empresa_id=empresa_id,
        plu=plu,
        nombre="Asado",
        precio_publico=Decimal("1000.0000"),
        precio_mayorista=Decimal("800.0000"),
        costo_por_kilo=Decimal("600.0000"),
        stock_actual=Decimal("100.0000"),
    )
    producto.recalcular_margen()
    db.add(producto)
    await db.commit()
    await db.refresh(producto)
    mov = MovimientoStock(
        empresa_id=empresa_id,
        producto_id=producto.id,
        tipo="entrada_compra",
        cantidad_kilos=Decimal("100.0000"),
        stock_resultante=Decimal("100.0000"),
        fecha=datetime.utcnow(),
    )
    db.add(mov)
    await db.commit()
    return producto


async def _setup_cajero(db: AsyncSession, nombre_empresa="Carniceria Test", email="cajero@basile.app"):
    empresa = await _crear_empresa(db, nombre_empresa)
    rol = await _crear_rol(db, "cajero", empresa_id=empresa.id)
    usuario = await _crear_usuario(db, email=email, empresa_id=empresa.id, rol_id=rol.id)
    return empresa, usuario


# ---------------------------------------------------------------------------
# Apertura
# ---------------------------------------------------------------------------
class TestApertura:
    async def test_apertura_exitosa(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        response = await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_inicial": "100.00"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["estado"] == "abierta"
        assert Decimal(data["efectivo_inicial"]) == Decimal("100.00")
        assert data["usuario_apertura_id"] == str(usuario.id)

    async def test_segunda_apertura_rechazada(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_inicial": "100.00"},
        )
        response = await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_inicial": "50.00"},
        )
        assert response.status_code == 409
        assert "abierta" in response.json()["detail"].lower()

    async def test_apertura_aislada_por_empresa(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a, usuario_a = await _setup_cajero(db_session, "Empresa A", "a@basile.app")
        empresa_b, usuario_b = await _setup_cajero(db_session, "Empresa B", "b@basile.app")
        await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario_a, empresa_id=empresa_a.id),
            json={"efectivo_inicial": "100.00"},
        )
        # Empresa B can still open its own caja
        response = await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario_b, empresa_id=empresa_b.id),
            json={"efectivo_inicial": "200.00"},
        )
        assert response.status_code == 201


# ---------------------------------------------------------------------------
# Movimientos
# ---------------------------------------------------------------------------
class TestMovimientos:
    async def test_registrar_retiro(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        await client.post("/caja/apertura", headers=_auth_header(usuario, empresa_id=empresa.id), json={"efectivo_inicial": "100.00"})
        response = await client.post(
            "/caja/movimientos",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"tipo": "retiro", "importe": "30.00", "descripcion": "Pago proveedor"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["tipo"] == "retiro"
        assert Decimal(data["importe"]) == Decimal("30.00")
        assert data["descripcion"] == "Pago proveedor"

    async def test_registrar_ingreso_manual(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        await client.post("/caja/apertura", headers=_auth_header(usuario, empresa_id=empresa.id), json={"efectivo_inicial": "100.00"})
        response = await client.post(
            "/caja/movimientos",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"tipo": "ingreso_manual", "importe": "20.00", "descripcion": "Reposición fondo"},
        )
        assert response.status_code == 201
        assert response.json()["tipo"] == "ingreso_manual"

    async def test_movimiento_sin_caja_abierta(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        response = await client.post(
            "/caja/movimientos",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"tipo": "retiro", "importe": "10.00"},
        )
        assert response.status_code == 409


# ---------------------------------------------------------------------------
# Cierre con diferencias (esperado vs real)
# ---------------------------------------------------------------------------
class TestCierre:
    async def test_cierre_sin_diferencia(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        producto = await _crear_producto(db_session, empresa.id)
        await client.post("/caja/apertura", headers=_auth_header(usuario, empresa_id=empresa.id), json={"efectivo_inicial": "100.00"})

        # Una venta cobrada en efectivo => MovimientoCaja entrada_venta efectivo
        resp = await client.post("/venta", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}],
        })
        venta_id = resp.json()["id"]
        await client.post(f"/venta/{venta_id}/cobrar", headers=_auth_header(usuario, empresa_id=empresa.id), json={"medio_pago": "efectivo"})

        # esperado efectivo = 100 + 1000 = 1100
        response = await client.post(
            "/caja/cierre",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_real": "1100.00", "transferencias_real": "0.00", "tarjetas_real": "0.00"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["caja"]["estado"] == "cerrada"
        assert Decimal(data["esperado"]["efectivo"]) == Decimal("1100.00")
        assert Decimal(data["diferencias"]["diferencia_total"]) == Decimal("0.00")
        assert data["diferencias"]["tiene_diferencia"] is False
        assert data["diferencias"]["diferencia_significativa"] is False

    async def test_cierre_con_faltante_significativo(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        await client.post("/caja/apertura", headers=_auth_header(usuario, empresa_id=empresa.id), json={"efectivo_inicial": "140.00"})
        response = await client.post(
            "/caja/cierre",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_real": "130.00", "transferencias_real": "0.00", "tarjetas_real": "0.00"},
        )
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["diferencias"]["diferencia_efectivo"]) == Decimal("-10.00")
        assert Decimal(data["diferencias"]["diferencia_total"]) == Decimal("-10.00")
        assert data["diferencias"]["tiene_diferencia"] is True
        assert data["diferencias"]["diferencia_significativa"] is True

    async def test_cierre_tarjetas_y_transferencias(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        producto = await _crear_producto(db_session, empresa.id)
        await client.post("/caja/apertura", headers=_auth_header(usuario, empresa_id=empresa.id), json={"efectivo_inicial": "0.00"})

        # venta débito 1000
        resp = await client.post("/venta", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}],
        })
        vid = resp.json()["id"]
        await client.post(f"/venta/{vid}/cobrar", headers=_auth_header(usuario, empresa_id=empresa.id), json={"medio_pago": "debito"})
        # venta transferencia 1000
        resp = await client.post("/venta", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}],
        })
        vid2 = resp.json()["id"]
        await client.post(f"/venta/{vid2}/cobrar", headers=_auth_header(usuario, empresa_id=empresa.id), json={"medio_pago": "transferencia"})

        response = await client.post(
            "/caja/cierre",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_real": "0.00", "transferencias_real": "1000.00", "tarjetas_real": "1000.00"},
        )
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["esperado"]["tarjetas"]) == Decimal("1000.00")
        assert Decimal(data["esperado"]["transferencias"]) == Decimal("1000.00")
        assert Decimal(data["diferencias"]["diferencia_total"]) == Decimal("0.00")

    async def test_cierre_sin_caja_abierta(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        response = await client.post(
            "/caja/cierre",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_real": "0.00"},
        )
        assert response.status_code == 409


# ---------------------------------------------------------------------------
# GET /caja/actual
# ---------------------------------------------------------------------------
class TestCajaActual:
    async def test_actual_con_esperado_vivo(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        await client.post("/caja/apertura", headers=_auth_header(usuario, empresa_id=empresa.id), json={"efectivo_inicial": "100.00"})
        await client.post("/caja/movimientos", headers=_auth_header(usuario, empresa_id=empresa.id), json={"tipo": "ingreso_manual", "importe": "50.00"})
        await client.post("/caja/movimientos", headers=_auth_header(usuario, empresa_id=empresa.id), json={"tipo": "retiro", "importe": "20.00"})

        response = await client.get("/caja/actual", headers=_auth_header(usuario, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        # 100 + 50 - 20 = 130
        assert Decimal(data["esperado"]["efectivo"]) == Decimal("130.00")


# ---------------------------------------------------------------------------
# Multi-tenant + RBAC
# ---------------------------------------------------------------------------
class TestSeguridad:
    async def test_apertura_no_cruza_empresas(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a, usuario_a = await _setup_cajero(db_session, "Empresa A", "a@basile.app")
        empresa_b, usuario_b = await _setup_cajero(db_session, "Empresa B", "b@basile.app")
        # A abre caja
        await client.post("/caja/apertura", headers=_auth_header(usuario_a, empresa_id=empresa_a.id), json={"efectivo_inicial": "100.00"})
        # B no ve caja de A: su /caja/actual da 404
        response = await client.get("/caja/actual", headers=_auth_header(usuario_b, empresa_id=empresa_b.id))
        assert response.status_code == 404

    async def test_vendedor_sin_permiso_caja(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "vendedor", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="vend@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        response = await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario, rol_nombre="vendedor", empresa_id=empresa.id),
            json={"efectivo_inicial": "100.00"},
        )
        assert response.status_code == 403

    async def test_encargado_puede_operar_caja(self, client: AsyncClient, db_session: AsyncSession):
        """RN-CAJA-04: Cajero, Encargado o Administrador operan caja."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "encargado", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="enc@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        response = await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario, rol_nombre="encargado", empresa_id=empresa.id),
            json={"efectivo_inicial": "100.00"},
        )
        assert response.status_code == 201
        assert response.json()["estado"] == "abierta"


# ---------------------------------------------------------------------------
# Polish-1: Unified efectivo_inicial field + cierre uses apertura value correctly
# ---------------------------------------------------------------------------
class TestEfectivoInicialUnificado:
    async def test_apertura_expone_efectivo_inicial(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """CajaRead must expose efectivo_inicial (not monto_inicial)."""
        empresa, usuario = await _setup_cajero(db_session)
        response = await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_inicial": "250.00"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "efectivo_inicial" in data, "CajaRead must expose efectivo_inicial"
        assert "monto_inicial" not in data, "CajaRead must NOT expose monto_inicial"
        assert Decimal(data["efectivo_inicial"]) == Decimal("250.00")

    async def test_cierre_esperado_usa_efectivo_inicial_de_apertura(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """cierre.esperado.efectivo must equal efectivo_inicial set at apertura.

        This test catches the latent bug where apertura writes monto_inicial but
        cierre reads efectivo_inicial — after unification both must be the same field.
        """
        empresa, usuario = await _setup_cajero(db_session)
        apertura_amount = "350.00"
        await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_inicial": apertura_amount},
        )
        # Close with no movements — esperado.efectivo must equal apertura amount.
        response = await client.post(
            "/caja/cierre",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={
                "efectivo_real": apertura_amount,
                "transferencias_real": "0.00",
                "tarjetas_real": "0.00",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["esperado"]["efectivo"]) == Decimal(apertura_amount), (
            f"cierre.esperado.efectivo must equal apertura efectivo_inicial={apertura_amount}"
        )
        assert Decimal(data["diferencias"]["diferencia_total"]) == Decimal("0.00")
        # The response caja should expose efectivo_inicial
        assert "efectivo_inicial" in data["caja"]
        assert "monto_inicial" not in data["caja"]

    async def test_cierre_esperado_con_retiro_usa_efectivo_inicial_base(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Triangulate: cierre esperado with a retiro uses efectivo_inicial as base.

        efectivo_inicial=200, retiro=50 => esperado.efectivo=150.
        """
        empresa, usuario = await _setup_cajero(db_session)
        await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_inicial": "200.00"},
        )
        await client.post(
            "/caja/movimientos",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"tipo": "retiro", "importe": "50.00"},
        )
        response = await client.post(
            "/caja/cierre",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={
                "efectivo_real": "150.00",
                "transferencias_real": "0.00",
                "tarjetas_real": "0.00",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # 200 - 50 = 150
        assert Decimal(data["esperado"]["efectivo"]) == Decimal("150.00")
        assert Decimal(data["diferencias"]["diferencia_total"]) == Decimal("0.00")


# ---------------------------------------------------------------------------
# FIX 1 — Apertura TOCTOU race: DB-level partial unique index
# ---------------------------------------------------------------------------
class TestAperturaConcurrencia:
    async def test_segunda_caja_abierta_rechazada_en_db(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A second apertura while one is open is rejected at the DB layer,
        independent of the in-app `_obtener_caja_abierta` guard.

        We bypass the in-app check by calling the service after a caja is already
        open via the in-app path, then forcing a second open insert through the
        service while the partial unique index is what must reject it. Concretely:
        open one caja, then patch out the in-app guard so the service relies solely
        on the DB constraint, and assert it still raises ConflictException.
        """
        from unittest.mock import patch
        from src.modules.caja import service as caja_service

        empresa, usuario = await _setup_cajero(db_session)
        await caja_service.abrir_caja(
            db=db_session,
            empresa_id=empresa.id,
            usuario_id=usuario.id,
            efectivo_inicial=Decimal("100.00"),
        )

        # Force the in-app guard to "see no open caja", so only the DB index protects us.
        with patch.object(caja_service, "_obtener_caja_abierta", return_value=None):
            with pytest.raises(ConflictException) as exc_info:
                await caja_service.abrir_caja(
                    db=db_session,
                    empresa_id=empresa.id,
                    usuario_id=usuario.id,
                    efectivo_inicial=Decimal("50.00"),
                )
        assert "abierta" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# FIX 2 — Cierre row-lock / double-cierre guard
# ---------------------------------------------------------------------------
class TestCierreConcurrencia:
    async def test_doble_cierre_rechazado(self, client: AsyncClient, db_session: AsyncSession):
        """A second cierre on the same caja must be rejected (no open caja left)."""
        empresa, usuario = await _setup_cajero(db_session)
        await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_inicial": "100.00"},
        )
        first = await client.post(
            "/caja/cierre",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_real": "100.00", "transferencias_real": "0.00", "tarjetas_real": "0.00"},
        )
        assert first.status_code == 200
        second = await client.post(
            "/caja/cierre",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_real": "100.00", "transferencias_real": "0.00", "tarjetas_real": "0.00"},
        )
        assert second.status_code == 409

    async def test_movimiento_no_se_adjunta_a_caja_cerrada(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Once cerrada, no new movimiento attaches (open-caja lookup filters estado)."""
        empresa, usuario = await _setup_cajero(db_session)
        await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_inicial": "100.00"},
        )
        await client.post(
            "/caja/cierre",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_real": "100.00", "transferencias_real": "0.00", "tarjetas_real": "0.00"},
        )
        resp = await client.post(
            "/caja/movimientos",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"tipo": "ingreso_manual", "importe": "10.00"},
        )
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# FIX 3 — Over-retiro guard
# ---------------------------------------------------------------------------
class TestOverRetiro:
    async def test_retiro_mayor_a_disponible_rechazado(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        empresa, usuario = await _setup_cajero(db_session)
        await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_inicial": "100.00"},
        )
        # Try to withdraw more than the 100.00 available -> rejected.
        resp = await client.post(
            "/caja/movimientos",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"tipo": "retiro", "importe": "150.00"},
        )
        assert resp.status_code == 409

    async def test_retiro_valido_sigue_funcionando(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        empresa, usuario = await _setup_cajero(db_session)
        await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_inicial": "100.00"},
        )
        resp = await client.post(
            "/caja/movimientos",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"tipo": "retiro", "importe": "100.00"},
        )
        assert resp.status_code == 201

    async def test_retiro_exacto_disponible_permitido(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Boundary: importe == efectivo_disponible is allowed (only > is rejected)."""
        empresa, usuario = await _setup_cajero(db_session)
        await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_inicial": "50.00"},
        )
        await client.post(
            "/caja/movimientos",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"tipo": "ingreso_manual", "importe": "10.00"},
        )
        # disponible = 60.00 -> retiro of exactly 60.00 is allowed
        resp = await client.post(
            "/caja/movimientos",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"tipo": "retiro", "importe": "60.00"},
        )
        assert resp.status_code == 201


# ---------------------------------------------------------------------------
# FIX 4 — Money-invariant tests (CC exclusion + same-day anulación netting)
# ---------------------------------------------------------------------------
class TestInvariantesDinero:
    async def test_cuenta_corriente_excluida_de_caja(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """CC sale does NOT touch caja: esperado.efectivo stays at efectivo_inicial,
        transferencias/tarjetas unchanged, and no MovimientoCaja row created for it."""
        empresa, usuario = await _setup_cajero(db_session)
        producto = await _crear_producto(db_session, empresa.id)
        # cliente para CC
        cliente = Cliente(
            empresa_id=empresa.id,
            nombre="Cliente CC",
            tipo_cliente="mayorista",
            saldo_actual=Decimal("0.00"),
        )
        db_session.add(cliente)
        await db_session.commit()
        await db_session.refresh(cliente)

        await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_inicial": "100.00"},
        )
        resp = await client.post(
            "/venta",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={
                "cliente_id": str(cliente.id),
                "items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}],
            },
        )
        venta_id = resp.json()["id"]
        cobro = await client.post(
            f"/venta/{venta_id}/cobrar",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"medio_pago": "cuenta_corriente"},
        )
        assert cobro.status_code == 200

        actual = await client.get(
            "/caja/actual", headers=_auth_header(usuario, empresa_id=empresa.id)
        )
        data = actual.json()
        assert Decimal(data["esperado"]["efectivo"]) == Decimal("100.00")
        assert Decimal(data["esperado"]["transferencias"]) == Decimal("0.00")
        assert Decimal(data["esperado"]["tarjetas"]) == Decimal("0.00")

        # No MovimientoCaja row was created for the CC sale.
        result = await db_session.execute(
            select(MovimientoCaja).where(MovimientoCaja.venta_id == uuid.UUID(venta_id))
        )
        assert result.scalar_one_or_none() is None

    async def test_anulacion_mismo_dia_neutraliza_efectivo(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Same-day: open -> cobra efectivo -> anula -> cierre returns to
        efectivo_inicial with diferencia_total == 0.

        Uses an Encargado: only Admin/Encargado may anular ventas, and (after FIX 5)
        an Encargado may also operate caja, so one actor drives the whole flow.
        """
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "encargado", empresa_id=empresa.id)
        usuario = await _crear_usuario(
            db_session, email="enc-anula@basile.app", empresa_id=empresa.id, rol_id=rol.id
        )
        headers = _auth_header(usuario, rol_nombre="encargado", empresa_id=empresa.id)
        producto = await _crear_producto(db_session, empresa.id)
        await client.post(
            "/caja/apertura",
            headers=headers,
            json={"efectivo_inicial": "100.00"},
        )
        resp = await client.post(
            "/venta",
            headers=headers,
            json={"items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}]},
        )
        venta_id = resp.json()["id"]
        await client.post(
            f"/venta/{venta_id}/cobrar",
            headers=headers,
            json={"medio_pago": "efectivo"},
        )
        anula = await client.post(
            f"/venta/{venta_id}/anular",
            headers=headers,
        )
        assert anula.status_code == 200

        cierre = await client.post(
            "/caja/cierre",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_real": "100.00", "transferencias_real": "0.00", "tarjetas_real": "0.00"},
        )
        assert cierre.status_code == 200
        data = cierre.json()
        assert Decimal(data["esperado"]["efectivo"]) == Decimal("100.00")
        assert Decimal(data["diferencias"]["diferencia_total"]) == Decimal("0.00")


# ---------------------------------------------------------------------------
# FIX 6 — Caja scope is per CAJERO (operador), not per empresa.
# Several cajeros in the same empresa may each hold one open caja at the same
# time, and every caja operation (apertura, movimiento, cobro, cierre, actual)
# resolves THE caja of the acting cajero. Resolves KB IN-06 for multi-cajero.
# ---------------------------------------------------------------------------
class TestMultiCajero:
    async def test_dos_cajeros_misma_empresa_abren_simultaneo(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Two distinct cajeros in the SAME empresa can each open their own caja
        concurrently. The per-empresa model rejected the second with 409; the
        per-cajero model lets both through."""
        empresa, cajero_a = await _setup_cajero(db_session, "Carniceria MC", "mc-a@basile.app")
        cajero_b = await _crear_usuario(
            db_session, email="mc-b@basile.app", empresa_id=empresa.id, rol_id=cajero_a.rol_id
        )

        r_a = await client.post(
            "/caja/apertura",
            headers=_auth_header(cajero_a, empresa_id=empresa.id),
            json={"efectivo_inicial": "100.00"},
        )
        r_b = await client.post(
            "/caja/apertura",
            headers=_auth_header(cajero_b, empresa_id=empresa.id),
            json={"efectivo_inicial": "200.00"},
        )
        assert r_a.status_code == 201
        assert r_b.status_code == 201
        assert r_a.json()["id"] != r_b.json()["id"]

    async def test_mismo_cajero_no_reabre(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A single cajero still cannot hold two open cajas at once."""
        empresa, cajero = await _setup_cajero(db_session, "Carniceria MC2", "mc2@basile.app")
        await client.post(
            "/caja/apertura",
            headers=_auth_header(cajero, empresa_id=empresa.id),
            json={"efectivo_inicial": "100.00"},
        )
        second = await client.post(
            "/caja/apertura",
            headers=_auth_header(cajero, empresa_id=empresa.id),
            json={"efectivo_inicial": "50.00"},
        )
        assert second.status_code == 409

    async def test_cobro_va_a_la_caja_del_cajero(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """With two open cajas in the empresa, a sale cobrada by cajero B must
        record its entrada_venta against B's caja, not A's."""
        empresa, cajero_a = await _setup_cajero(db_session, "Carniceria MC3", "mc3-a@basile.app")
        cajero_b = await _crear_usuario(
            db_session, email="mc3-b@basile.app", empresa_id=empresa.id, rol_id=cajero_a.rol_id
        )
        producto = await _crear_producto(db_session, empresa.id)

        await client.post(
            "/caja/apertura",
            headers=_auth_header(cajero_a, empresa_id=empresa.id),
            json={"efectivo_inicial": "100.00"},
        )
        r_b = await client.post(
            "/caja/apertura",
            headers=_auth_header(cajero_b, empresa_id=empresa.id),
            json={"efectivo_inicial": "0.00"},
        )
        caja_b_id = r_b.json()["id"]

        venta = await client.post(
            "/venta",
            headers=_auth_header(cajero_b, empresa_id=empresa.id),
            json={"items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}]},
        )
        venta_id = venta.json()["id"]
        cobro = await client.post(
            f"/venta/{venta_id}/cobrar",
            headers=_auth_header(cajero_b, empresa_id=empresa.id),
            json={"medio_pago": "efectivo"},
        )
        assert cobro.status_code == 200

        result = await db_session.execute(
            select(MovimientoCaja).where(MovimientoCaja.venta_id == uuid.UUID(venta_id))
        )
        mov = result.scalar_one()
        assert str(mov.caja_id) == caja_b_id

    async def test_actual_y_movimientos_scoped_por_cajero(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Each cajero's /caja/actual and movimientos hit only their own caja."""
        empresa, cajero_a = await _setup_cajero(db_session, "Carniceria MC4", "mc4-a@basile.app")
        cajero_b = await _crear_usuario(
            db_session, email="mc4-b@basile.app", empresa_id=empresa.id, rol_id=cajero_a.rol_id
        )
        await client.post(
            "/caja/apertura",
            headers=_auth_header(cajero_a, empresa_id=empresa.id),
            json={"efectivo_inicial": "100.00"},
        )
        await client.post(
            "/caja/apertura",
            headers=_auth_header(cajero_b, empresa_id=empresa.id),
            json={"efectivo_inicial": "500.00"},
        )

        # A withdraws 30 from A's caja only.
        await client.post(
            "/caja/movimientos",
            headers=_auth_header(cajero_a, empresa_id=empresa.id),
            json={"tipo": "retiro", "importe": "30.00"},
        )

        actual_a = await client.get(
            "/caja/actual", headers=_auth_header(cajero_a, empresa_id=empresa.id)
        )
        actual_b = await client.get(
            "/caja/actual", headers=_auth_header(cajero_b, empresa_id=empresa.id)
        )
        assert Decimal(actual_a.json()["esperado"]["efectivo"]) == Decimal("70.00")
        # B's caja is untouched by A's retiro.
        assert Decimal(actual_b.json()["esperado"]["efectivo"]) == Decimal("500.00")
