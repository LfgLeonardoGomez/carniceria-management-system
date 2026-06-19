import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.producto.models import Producto, CategoriaProducto
from src.modules.empresa.models import Empresa


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _crear_empresa(db_session: AsyncSession, nombre: str = "Test") -> Empresa:
    empresa = Empresa(nombre_comercial=nombre, activa=True)
    db_session.add(empresa)
    await db_session.commit()
    await db_session.refresh(empresa)
    return empresa


async def _crear_categoria(db_session: AsyncSession, empresa_id: uuid.UUID, nombre: str = "Carnes") -> CategoriaProducto:
    cat = CategoriaProducto(nombre=nombre, empresa_id=empresa_id)
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)
    return cat


async def _crear_producto(
    db_session: AsyncSession,
    empresa_id: uuid.UUID,
    plu: str = "001",
    nombre: str = "Producto Test",
    categoria_id: uuid.UUID = None,
    precio_publico: Decimal = Decimal("1000.0000"),
    precio_mayorista: Decimal = Decimal("800.0000"),
    costo_por_kilo: Decimal = Decimal("600.0000"),
    stock_actual: Decimal = Decimal("10.0000"),
    stock_minimo: Decimal = Decimal("2.0000"),
    activo: bool = True,
) -> Producto:
    producto = Producto(
        empresa_id=empresa_id,
        plu=plu,
        nombre=nombre,
        categoria_id=categoria_id,
        precio_publico=precio_publico,
        precio_mayorista=precio_mayorista,
        costo_por_kilo=costo_por_kilo,
        stock_actual=stock_actual,
        stock_minimo=stock_minimo,
        activo=activo,
    )
    producto.recalcular_margen()
    db_session.add(producto)
    await db_session.commit()
    await db_session.refresh(producto)
    return producto


# ---------------------------------------------------------------------------
# TASK-2.3: Tests para cálculo automático de margen
# ---------------------------------------------------------------------------
class TestCalcularMargen:
    def test_margen_normal(self):
        p = Producto(
            precio_publico=Decimal("1000.0000"),
            costo_por_kilo=Decimal("600.0000"),
        )
        margen = p.calcular_margen()
        assert margen == Decimal("0.4000")

    def test_margen_precio_cero(self):
        p = Producto(
            precio_publico=Decimal("0.0000"),
            costo_por_kilo=Decimal("0.0000"),
        )
        margen = p.calcular_margen()
        assert margen == Decimal("0.0000")

    def test_margen_precio_menor_que_costo(self):
        p = Producto(
            precio_publico=Decimal("500.0000"),
            costo_por_kilo=Decimal("600.0000"),
        )
        margen = p.calcular_margen()
        assert margen == Decimal("-0.2000")

    def test_recalcular_margen_asigna(self):
        p = Producto(
            precio_publico=Decimal("1000.0000"),
            costo_por_kilo=Decimal("600.0000"),
        )
        p.recalcular_margen()
        assert p.margen == Decimal("0.4000")

    def test_margen_precision_4_decimales(self):
        p = Producto(
            precio_publico=Decimal("1000.0000"),
            costo_por_kilo=Decimal("333.3333"),
        )
        margen = p.calcular_margen()
        # (1000 - 333.3333) / 1000 = 0.6666667 -> rounded to 4 decimals
        assert margen == Decimal("0.6667")


# ---------------------------------------------------------------------------
# TASK-2.1: Tests para ProductoRepository (DB level)
# ---------------------------------------------------------------------------
class TestProductoRepository:
    async def test_crear_producto(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        producto = await _crear_producto(db_session, empresa.id, categoria_id=cat.id)

        assert producto.id is not None
        assert producto.empresa_id == empresa.id
        assert producto.plu == "001"
        assert producto.margen == Decimal("0.4000")

    async def test_buscar_por_plu(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        await _crear_producto(db_session, empresa.id, plu="123", categoria_id=cat.id)

        from sqlalchemy import select
        result = await db_session.execute(
            select(Producto).where(Producto.plu == "123", Producto.empresa_id == empresa.id)
        )
        found = result.scalar_one_or_none()
        assert found is not None
        assert found.plu == "123"

    async def test_busqueda_por_nombre(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        await _crear_producto(db_session, empresa.id, plu="VAC", nombre="Vacio Especial", categoria_id=cat.id)
        await _crear_producto(db_session, empresa.id, plu="NAL", nombre="Nalga Premium", categoria_id=cat.id)

        from sqlalchemy import select, func
        result = await db_session.execute(
            select(Producto).where(
                Producto.empresa_id == empresa.id,
                func.lower(Producto.nombre).contains("vacio")
            )
        )
        found = result.scalars().all()
        assert len(found) == 1
        assert found[0].nombre == "Vacio Especial"

    async def test_paginacion(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        for i in range(25):
            await _crear_producto(db_session, empresa.id, plu=f"{i:03d}", nombre=f"Producto {i}", categoria_id=cat.id)

        from sqlalchemy import select, func
        count_result = await db_session.execute(
            select(func.count(Producto.id)).where(Producto.empresa_id == empresa.id, Producto.activo == True)
        )
        total = count_result.scalar_one()
        assert total == 25

        result = await db_session.execute(
            select(Producto)
            .where(Producto.empresa_id == empresa.id, Producto.activo == True)
            .order_by(Producto.nombre)
            .offset(0)
            .limit(20)
        )
        items = result.scalars().all()
        assert len(items) == 20

    async def test_unicidad_plu_por_empresa(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        await _crear_producto(db_session, empresa.id, plu="DUPLICADO", categoria_id=cat.id)

        from sqlalchemy.exc import IntegrityError
        duplicado = Producto(
            empresa_id=empresa.id,
            plu="DUPLICADO",
            nombre="Otro",
            categoria_id=cat.id,
            precio_publico=Decimal("100.0000"),
            precio_mayorista=Decimal("80.0000"),
            costo_por_kilo=Decimal("50.0000"),
            stock_actual=Decimal("1.0000"),
        )
        duplicado.recalcular_margen()
        db_session.add(duplicado)
        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_plu_misma_empresa_diferente_empresa_ok(self, db_session: AsyncSession):
        empresa1 = await _crear_empresa(db_session, "Empresa 1")
        empresa2 = await _crear_empresa(db_session, "Empresa 2")
        cat1 = await _crear_categoria(db_session, empresa1.id)
        cat2 = await _crear_categoria(db_session, empresa2.id)

        await _crear_producto(db_session, empresa1.id, plu="SAME", categoria_id=cat1.id)
        await _crear_producto(db_session, empresa2.id, plu="SAME", categoria_id=cat2.id)

        from sqlalchemy import select
        result1 = await db_session.execute(
            select(Producto).where(Producto.empresa_id == empresa1.id, Producto.plu == "SAME")
        )
        result2 = await db_session.execute(
            select(Producto).where(Producto.empresa_id == empresa2.id, Producto.plu == "SAME")
        )
        assert result1.scalar_one_or_none() is not None
        assert result2.scalar_one_or_none() is not None

    async def test_soft_delete(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        producto = await _crear_producto(db_session, empresa.id, categoria_id=cat.id)

        producto.activo = False
        await db_session.commit()

        from sqlalchemy import select
        result = await db_session.execute(
            select(Producto).where(Producto.id == producto.id)
        )
        found = result.scalar_one()
        assert found.activo is False

    async def test_decimal_no_float(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        producto = await _crear_producto(
            db_session, empresa.id,
            precio_publico=Decimal("999.999"),
            costo_por_kilo=Decimal("333.333"),
            categoria_id=cat.id,
        )
        # Ensure it's Decimal, not float
        assert isinstance(producto.precio_publico, Decimal)
        assert isinstance(producto.margen, Decimal)


# ---------------------------------------------------------------------------
# TASK-2.5: Tests para CategoriaProductoRepository (DB level)
# ---------------------------------------------------------------------------
class TestCategoriaProductoRepository:
    async def test_crear_categoria(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = CategoriaProducto(nombre="Nueva Categoria", empresa_id=empresa.id)
        db_session.add(cat)
        await db_session.commit()
        await db_session.refresh(cat)
        assert cat.id is not None
        assert cat.empresa_id == empresa.id

    async def test_unicidad_nombre_por_empresa(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat1 = CategoriaProducto(nombre="Unica", empresa_id=empresa.id)
        db_session.add(cat1)
        await db_session.commit()

        from sqlalchemy.exc import IntegrityError
        cat2 = CategoriaProducto(nombre="Unica", empresa_id=empresa.id)
        db_session.add(cat2)
        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_nombre_mismo_diferente_empresa_ok(self, db_session: AsyncSession):
        empresa1 = await _crear_empresa(db_session)
        empresa2 = await _crear_empresa(db_session)
        cat1 = CategoriaProducto(nombre="Compartida", empresa_id=empresa1.id)
        cat2 = CategoriaProducto(nombre="Compartida", empresa_id=empresa2.id)
        db_session.add(cat1)
        db_session.add(cat2)
        await db_session.commit()

        from sqlalchemy import select
        count = await db_session.execute(
            select(CategoriaProducto).where(CategoriaProducto.nombre == "Compartida")
        )
        assert len(count.scalars().all()) == 2

    async def test_eliminar_categoria_sin_productos(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = CategoriaProducto(nombre="Vacía", empresa_id=empresa.id)
        db_session.add(cat)
        await db_session.commit()
        await db_session.refresh(cat)

        await db_session.delete(cat)
        await db_session.commit()

        from sqlalchemy import select
        result = await db_session.execute(
            select(CategoriaProducto).where(CategoriaProducto.id == cat.id)
        )
        assert result.scalar_one_or_none() is None

    async def test_no_eliminar_categoria_con_productos(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id, "Con Productos")
        await _crear_producto(db_session, empresa.id, categoria_id=cat.id)

        # Verify that deleting a category with products is blocked at DB level
        from sqlalchemy import text
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            await db_session.execute(
                text("DELETE FROM categoria_producto WHERE id = :id"),
                {"id": str(cat.id)}
            )
            await db_session.commit()
