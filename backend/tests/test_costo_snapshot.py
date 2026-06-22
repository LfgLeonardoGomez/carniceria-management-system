"""Tests for costo_unitario snapshot and ganancia calculation.

TDD cycle: RED → GREEN → TRIANGULATE → REFACTOR
These tests are written BEFORE the production code they exercise.
"""
import uuid
from decimal import Decimal
from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.auth.models import Usuario, Rol, Empresa
from src.modules.venta.models import Venta, DetalleVenta
from src.modules.stock.models import MovimientoStock
from src.modules.caja.models import Caja
from src.core.security import hash_password, create_access_token

# ---------------------------------------------------------------------------
# We import the ganancia helper under test.
# At RED phase this import WILL FAIL — that is the expected behaviour.
# ---------------------------------------------------------------------------
from src.modules.venta.service import calcular_ganancia


# ---------------------------------------------------------------------------
# Shared test helpers (mirror those from test_venta_integration.py)
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
    email: str = "test@basile.app",
    empresa_id=None,
    rol_id=None,
) -> Usuario:
    if rol_id is None:
        rol = await _crear_rol(db, empresa_id=empresa_id)
        rol_id = rol.id
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


async def _crear_producto(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    plu: str = "CS01",
    nombre: str = "Producto Snapshot",
    stock_actual: Decimal = Decimal("20.000"),
    costo_por_kilo: Decimal = Decimal("500.0000"),
    precio_publico: Decimal = Decimal("1200.0000"),
) -> "Producto":
    from src.modules.producto.models import Producto
    producto = Producto(
        empresa_id=empresa_id,
        plu=plu,
        nombre=nombre,
        precio_publico=precio_publico,
        precio_mayorista=Decimal("900.0000"),
        costo_por_kilo=costo_por_kilo,
        stock_actual=stock_actual,
    )
    producto.recalcular_margen()
    db.add(producto)
    await db.commit()
    await db.refresh(producto)

    if stock_actual > Decimal("0.000"):
        mov = MovimientoStock(
            empresa_id=empresa_id,
            producto_id=producto.id,
            tipo="entrada_compra",
            cantidad_kilos=stock_actual,
            stock_resultante=stock_actual,
            fecha=datetime.utcnow(),
        )
        db.add(mov)
        await db.commit()

    return producto


async def _crear_caja_abierta(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    operador_id: uuid.UUID,
) -> Caja:
    caja = Caja(
        empresa_id=empresa_id,
        operador_id=operador_id,
        efectivo_inicial=Decimal("100.00"),
        estado="abierta",
    )
    db.add(caja)
    await db.commit()
    await db.refresh(caja)
    return caja


# ===========================================================================
# UNIT TESTS — calcular_ganancia (pure function)
# These run WITHOUT the DB; they exercise the logic in isolation.
# ===========================================================================
class TestCalcularGanancia:
    """Unit tests for the calcular_ganancia() pure function.

    Formula: ganancia = Σ(importe) − Σ(cantidad_kilos × costo_unitario)
    Rule: if ANY line has costo_unitario IS NULL → return None.
    """

    # -----------------------------------------------------------------------
    # Case (a): all lines snapshotted → computes correct Decimal
    # -----------------------------------------------------------------------
    def test_ganancia_todas_lineas_con_costo(self):
        """All lines have costo_unitario — should return the exact profit."""
        lineas = [
            DetalleVenta(
                id=uuid.uuid4(),
                venta_id=uuid.uuid4(),
                producto_id=uuid.uuid4(),
                cantidad_kilos=Decimal("2.000"),
                precio_unitario=Decimal("1200.00"),
                importe=Decimal("2400.00"),
                costo_unitario=Decimal("500.00"),
            )
        ]
        # ganancia = 2400 - (2.000 × 500) = 2400 - 1000 = 1400
        resultado = calcular_ganancia(lineas)
        assert resultado == Decimal("1400.00")

    # -----------------------------------------------------------------------
    # Triangulation case 1: multi-line sum
    # -----------------------------------------------------------------------
    def test_ganancia_multiples_lineas(self):
        """Multiple lines — sum must be applied across all lines."""
        venta_id = uuid.uuid4()
        lineas = [
            DetalleVenta(
                id=uuid.uuid4(),
                venta_id=venta_id,
                producto_id=uuid.uuid4(),
                cantidad_kilos=Decimal("1.000"),
                precio_unitario=Decimal("1000.00"),
                importe=Decimal("1000.00"),
                costo_unitario=Decimal("400.00"),
            ),
            DetalleVenta(
                id=uuid.uuid4(),
                venta_id=venta_id,
                producto_id=uuid.uuid4(),
                cantidad_kilos=Decimal("0.500"),
                precio_unitario=Decimal("2000.00"),
                importe=Decimal("1000.00"),
                costo_unitario=Decimal("800.00"),
            ),
        ]
        # ganancia = (1000 + 1000) - (1×400 + 0.5×800)
        #          = 2000 - (400 + 400) = 2000 - 800 = 1200
        resultado = calcular_ganancia(lineas)
        assert resultado == Decimal("1200.00")

    # -----------------------------------------------------------------------
    # Case (b): one NULL line → return None (not available)
    # -----------------------------------------------------------------------
    def test_ganancia_una_linea_sin_costo_retorna_none(self):
        """If any line has costo_unitario=None, the whole venta is not available."""
        venta_id = uuid.uuid4()
        lineas = [
            DetalleVenta(
                id=uuid.uuid4(),
                venta_id=venta_id,
                producto_id=uuid.uuid4(),
                cantidad_kilos=Decimal("1.000"),
                precio_unitario=Decimal("1000.00"),
                importe=Decimal("1000.00"),
                costo_unitario=Decimal("400.00"),  # has snapshot
            ),
            DetalleVenta(
                id=uuid.uuid4(),
                venta_id=venta_id,
                producto_id=uuid.uuid4(),
                cantidad_kilos=Decimal("1.000"),
                precio_unitario=Decimal("1000.00"),
                importe=Decimal("1000.00"),
                costo_unitario=None,  # no snapshot — historical line
            ),
        ]
        resultado = calcular_ganancia(lineas)
        assert resultado is None

    # -----------------------------------------------------------------------
    # Triangulation case 2: all lines NULL → still None (not zero)
    # -----------------------------------------------------------------------
    def test_ganancia_todas_lineas_sin_costo_retorna_none(self):
        """All lines have no snapshot — should NOT produce a zero ganancia."""
        lineas = [
            DetalleVenta(
                id=uuid.uuid4(),
                venta_id=uuid.uuid4(),
                producto_id=uuid.uuid4(),
                cantidad_kilos=Decimal("3.000"),
                precio_unitario=Decimal("500.00"),
                importe=Decimal("1500.00"),
                costo_unitario=None,
            ),
        ]
        resultado = calcular_ganancia(lineas)
        assert resultado is None

    # -----------------------------------------------------------------------
    # Edge case: empty lines list
    # -----------------------------------------------------------------------
    def test_ganancia_sin_lineas_es_cero(self):
        """An empty sale has zero profit (trivially all costs known: none)."""
        resultado = calcular_ganancia([])
        assert resultado == Decimal("0.00")


# ===========================================================================
# INTEGRATION TESTS — costo_unitario snapshot
# These hit the real DB via testcontainers.
# ===========================================================================
class TestCostoSnapshot:
    """Integration: DetalleVenta.costo_unitario is snapshotted at sale creation time."""

    async def test_crear_venta_snapshot_costo_en_detalle(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """When a venta is created, each DetalleVenta line stores costo_por_kilo snapshot."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="snap1@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        # Product with costo_por_kilo = 500.0000
        producto = await _crear_producto(
            db_session,
            empresa.id,
            plu="CS01",
            costo_por_kilo=Decimal("500.0000"),
        )

        response = await client.post(
            "/venta",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"items": [{"producto_id": str(producto.id), "cantidad_kilos": "2.000"}]},
        )
        assert response.status_code == 201
        venta_id = response.json()["id"]

        # Fetch the DetalleVenta from DB and verify the snapshot
        result = await db_session.execute(
            select(DetalleVenta).where(DetalleVenta.venta_id == uuid.UUID(venta_id))
        )
        detalle = result.scalar_one()
        assert detalle.costo_unitario is not None
        assert Decimal(str(detalle.costo_unitario)) == Decimal("500.00")

    async def test_snapshot_inmutable_ante_cambio_de_costo(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """After the sale is created, updating the product cost must NOT change the snapshot."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="snap2@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        # Product with initial cost 500
        producto = await _crear_producto(
            db_session,
            empresa.id,
            plu="CS02",
            costo_por_kilo=Decimal("500.0000"),
        )

        # Create the sale — snapshot should be 500
        response = await client.post(
            "/venta",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}]},
        )
        assert response.status_code == 201
        venta_id = response.json()["id"]

        # Simulate cost update AFTER the sale (e.g. new delivery at higher price)
        from src.modules.producto.models import Producto
        result = await db_session.execute(
            select(Producto).where(Producto.id == producto.id)
        )
        prod_db = result.scalar_one()
        prod_db.costo_por_kilo = Decimal("999.0000")
        await db_session.commit()

        # The snapshot on the DetalleVenta MUST still be the original 500
        result = await db_session.execute(
            select(DetalleVenta).where(DetalleVenta.venta_id == uuid.UUID(venta_id))
        )
        detalle = result.scalar_one()
        assert Decimal(str(detalle.costo_unitario)) == Decimal("500.00"), (
            "costo_unitario must be the snapshot at sale time, not the current product cost"
        )

    async def test_snapshot_multilinea_cada_producto_su_costo(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Multi-line sale: each line snapshots its own product cost independently."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="snap3@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        producto_a = await _crear_producto(
            db_session, empresa.id, plu="CSA", costo_por_kilo=Decimal("300.0000"),
            precio_publico=Decimal("800.0000"),
        )
        producto_b = await _crear_producto(
            db_session, empresa.id, plu="CSB", costo_por_kilo=Decimal("700.0000"),
            precio_publico=Decimal("1500.0000"),
        )

        response = await client.post(
            "/venta",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={
                "items": [
                    {"producto_id": str(producto_a.id), "cantidad_kilos": "1.000"},
                    {"producto_id": str(producto_b.id), "cantidad_kilos": "2.000"},
                ]
            },
        )
        assert response.status_code == 201
        venta_id = response.json()["id"]

        result = await db_session.execute(
            select(DetalleVenta)
            .where(DetalleVenta.venta_id == uuid.UUID(venta_id))
            .order_by(DetalleVenta.producto_id)
        )
        detalles = result.scalars().all()
        assert len(detalles) == 2

        costos = {str(d.producto_id): Decimal(str(d.costo_unitario)) for d in detalles}
        assert costos[str(producto_a.id)] == Decimal("300.00")
        assert costos[str(producto_b.id)] == Decimal("700.00")
