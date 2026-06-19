import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.producto.models import Producto, CategoriaProducto
from src.modules.producto import service
from src.modules.empresa.models import Empresa
from src.common.exceptions import ConflictException, NotFoundException


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
    return await service.crear_categoria(db_session, empresa_id, nombre)


# ---------------------------------------------------------------------------
# TASK-2.4: ProductoService tests
# ---------------------------------------------------------------------------
class TestProductoService:
    async def test_crear_producto(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)

        producto = await service.crear_producto(
            db=db_session,
            empresa_id=empresa.id,
            plu="001",
            nombre="Vacio",
            categoria_id=cat.id,
            precio_publico=Decimal("1000.0000"),
            precio_mayorista=Decimal("800.0000"),
            costo_por_kilo=Decimal("600.0000"),
            stock_actual=Decimal("10.0000"),
        )
        assert producto.plu == "001"
        assert producto.margen == Decimal("0.4000")

    async def test_crear_producto_plu_duplicado(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)

        await service.crear_producto(
            db=db_session, empresa_id=empresa.id, plu="DUP", nombre="A",
            categoria_id=cat.id, precio_publico=Decimal("100.0000"),
            precio_mayorista=Decimal("80.0000"), costo_por_kilo=Decimal("50.0000"),
            stock_actual=Decimal("1.0000"),
        )
        with pytest.raises(ConflictException):
            await service.crear_producto(
                db=db_session, empresa_id=empresa.id, plu="DUP", nombre="B",
                categoria_id=cat.id, precio_publico=Decimal("200.0000"),
                precio_mayorista=Decimal("160.0000"), costo_por_kilo=Decimal("100.0000"),
                stock_actual=Decimal("2.0000"),
            )

    async def test_listar_productos_con_filtros(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        await service.crear_producto(
            db=db_session, empresa_id=empresa.id, plu="P1", nombre="Asado",
            categoria_id=cat.id, precio_publico=Decimal("100.0000"),
            precio_mayorista=Decimal("80.0000"), costo_por_kilo=Decimal("50.0000"),
            stock_actual=Decimal("1.0000"),
        )
        await service.crear_producto(
            db=db_session, empresa_id=empresa.id, plu="P2", nombre="Vacio",
            categoria_id=cat.id, precio_publico=Decimal("200.0000"),
            precio_mayorista=Decimal("160.0000"), costo_por_kilo=Decimal("100.0000"),
            stock_actual=Decimal("2.0000"),
        )

        productos, total = await service.listar_productos(db_session, empresa.id)
        assert total == 2
        assert len(productos) == 2

        productos, total = await service.listar_productos(
            db_session, empresa.id, search="asado"
        )
        assert total == 1
        assert productos[0].nombre == "Asado"

    async def test_listar_solo_activos_por_defecto(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        p1 = await service.crear_producto(
            db=db_session, empresa_id=empresa.id, plu="A1", nombre="Activo",
            categoria_id=cat.id, precio_publico=Decimal("100.0000"),
            precio_mayorista=Decimal("80.0000"), costo_por_kilo=Decimal("50.0000"),
            stock_actual=Decimal("1.0000"),
        )
        await service.desactivar_producto(db_session, empresa.id, p1.id)

        productos, total = await service.listar_productos(db_session, empresa.id)
        assert total == 0

        productos, total = await service.listar_productos(
            db_session, empresa.id, activo=False
        )
        assert total == 1

    async def test_actualizar_producto_recalcula_margen(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        producto = await service.crear_producto(
            db=db_session, empresa_id=empresa.id, plu="M1", nombre="Margen",
            categoria_id=cat.id, precio_publico=Decimal("1000.0000"),
            precio_mayorista=Decimal("800.0000"), costo_por_kilo=Decimal("600.0000"),
            stock_actual=Decimal("1.0000"),
        )
        assert producto.margen == Decimal("0.4000")

        actualizado = await service.actualizar_producto(
            db_session, empresa.id, producto.id,
            precio_publico=Decimal("2000.0000"),
        )
        assert actualizado.margen == Decimal("0.7000")

    async def test_actualizar_producto_sin_cambio_precio_no_recalcula(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        producto = await service.crear_producto(
            db=db_session, empresa_id=empresa.id, plu="M2", nombre="Sin Cambio",
            categoria_id=cat.id, precio_publico=Decimal("1000.0000"),
            precio_mayorista=Decimal("800.0000"), costo_por_kilo=Decimal("600.0000"),
            stock_actual=Decimal("1.0000"),
        )
        margen_original = producto.margen

        actualizado = await service.actualizar_producto(
            db_session, empresa.id, producto.id,
            nombre="Nuevo Nombre",
        )
        assert actualizado.margen == margen_original

    async def test_obtener_producto_otra_empresa(self, db_session: AsyncSession):
        empresa1 = await _crear_empresa(db_session, "Empresa 1")
        empresa2 = await _crear_empresa(db_session, "Empresa 2")
        cat = await _crear_categoria(db_session, empresa1.id)
        producto = await service.crear_producto(
            db=db_session, empresa_id=empresa1.id, plu="EXT", nombre="Externo",
            categoria_id=cat.id, precio_publico=Decimal("100.0000"),
            precio_mayorista=Decimal("80.0000"), costo_por_kilo=Decimal("50.0000"),
            stock_actual=Decimal("1.0000"),
        )

        with pytest.raises(NotFoundException):
            await service.obtener_producto(db_session, empresa2.id, producto.id)

    async def test_desactivar_y_reactivar(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        producto = await service.crear_producto(
            db=db_session, empresa_id=empresa.id, plu="S1", nombre="Soft",
            categoria_id=cat.id, precio_publico=Decimal("100.0000"),
            precio_mayorista=Decimal("80.0000"), costo_por_kilo=Decimal("50.0000"),
            stock_actual=Decimal("1.0000"),
        )

        desactivado = await service.desactivar_producto(db_session, empresa.id, producto.id)
        assert desactivado.activo is False

        reactivado = await service.reactivar_producto(db_session, empresa.id, producto.id)
        assert reactivado.activo is True


# ---------------------------------------------------------------------------
# TASK-2.6: CategoriaProductoService tests
# ---------------------------------------------------------------------------
class TestCategoriaProductoService:
    async def test_crear_categoria(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await service.crear_categoria(db_session, empresa.id, "Nueva")
        assert cat.nombre == "Nueva"
        assert cat.empresa_id == empresa.id

    async def test_crear_categoria_nombre_duplicado(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await service.crear_categoria(db_session, empresa.id, "Unica")
        with pytest.raises(ConflictException):
            await service.crear_categoria(db_session, empresa.id, "unica")  # case-insensitive

    async def test_listar_categorias(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await service.crear_categoria(db_session, empresa.id, "A")
        await service.crear_categoria(db_session, empresa.id, "B")

        cats = await service.listar_categorias(db_session, empresa.id)
        assert len(cats) == 2

    async def test_actualizar_categoria(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await service.crear_categoria(db_session, empresa.id, "Viejo")
        actualizada = await service.actualizar_categoria(
            db_session, empresa.id, cat.id, "Nuevo"
        )
        assert actualizada.nombre == "Nuevo"

    async def test_eliminar_categoria_sin_productos(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await service.crear_categoria(db_session, empresa.id, "Vacía")
        await service.eliminar_categoria(db_session, empresa.id, cat.id)

        cats = await service.listar_categorias(db_session, empresa.id)
        assert len(cats) == 0

    async def test_eliminar_categoria_con_productos_rechazada(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await service.crear_categoria(db_session, empresa.id, "Con Productos")
        await service.crear_producto(
            db=db_session, empresa_id=empresa.id, plu="CP", nombre="Producto",
            categoria_id=cat.id, precio_publico=Decimal("100.0000"),
            precio_mayorista=Decimal("80.0000"), costo_por_kilo=Decimal("50.0000"),
            stock_actual=Decimal("1.0000"),
        )

        with pytest.raises(ConflictException):
            await service.eliminar_categoria(db_session, empresa.id, cat.id)

    async def test_categoria_otra_empresa_not_found(self, db_session: AsyncSession):
        empresa1 = await _crear_empresa(db_session, "E1")
        empresa2 = await _crear_empresa(db_session, "E2")
        cat = await service.crear_categoria(db_session, empresa1.id, "Privada")

        with pytest.raises(NotFoundException):
            await service.actualizar_categoria(db_session, empresa2.id, cat.id, "Robo")
