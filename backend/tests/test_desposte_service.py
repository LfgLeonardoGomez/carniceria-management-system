import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.desposte.models import Desposte, CorteDesposte
from src.modules.desposte import service as desposte_service
from src.modules.compra.models import Compra
from src.modules.compra import service as compra_service
from src.modules.proveedor.models import Proveedor
from src.modules.producto.models import Producto
from src.modules.stock.models import MovimientoStock
from src.modules.auth.models import Usuario, Rol
from src.modules.empresa.models import Empresa
from src.common.exceptions import NotFoundException, ConflictException, BasileException


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
async def empresa(db_session: AsyncSession) -> Empresa:
    empresa = Empresa(
        nombre_comercial="Test Carnicería",
        razon_social="Test SA",
        cuit="30701234567",
    )
    db_session.add(empresa)
    await db_session.commit()
    await db_session.refresh(empresa)
    return empresa


@pytest.fixture
async def proveedor(db_session: AsyncSession, empresa: Empresa) -> Proveedor:
    proveedor = Proveedor(
        empresa_id=empresa.id,
        nombre="Proveedor Test",
        cuit="30701234568",
    )
    db_session.add(proveedor)
    await db_session.commit()
    await db_session.refresh(proveedor)
    return proveedor


@pytest.fixture
async def rol(db_session: AsyncSession) -> Rol:
    rol = Rol(nombre="Encargado")
    db_session.add(rol)
    await db_session.commit()
    await db_session.refresh(rol)
    return rol


@pytest.fixture
async def usuario(db_session: AsyncSession, empresa: Empresa, rol: Rol) -> Usuario:
    usuario = Usuario(
        empresa_id=empresa.id,
        email="test@basile.com",
        contrasena_hash="hashed_password",
        nombre="Test",
        apellido="User",
        rol_id=rol.id,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    return usuario


@pytest.fixture
async def compra(db_session: AsyncSession, empresa: Empresa, proveedor: Proveedor, usuario: Usuario) -> Compra:
    compra = await compra_service.create_compra(
        db=db_session,
        empresa_id=empresa.id,
        proveedor_id=proveedor.id,
        fecha=date.today(),
        cantidad_medias_reses=2,
        peso_total=Decimal("100.000"),
        costo_total=Decimal("500.00"),
        operador_id=usuario.id,
    )
    return compra


@pytest.fixture
async def producto_asado(db_session: AsyncSession, empresa: Empresa) -> Producto:
    producto = Producto(
        empresa_id=empresa.id,
        plu="ASADO001",
        nombre="Asado",
        precio_publico=Decimal("800.0000"),
        precio_mayorista=Decimal("750.0000"),
        costo_por_kilo=Decimal("500.0000"),
        margen=Decimal("0.3750"),
        stock_actual=Decimal("50.0000"),
    )
    db_session.add(producto)
    await db_session.commit()
    await db_session.refresh(producto)
    return producto


# ---------------------------------------------------------------------------
# Tests: Crear Desposte
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_crear_desposte_exitoso(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
    usuario: Usuario,
):
    desposte = await desposte_service.crear_desposte(
        db=db_session,
        empresa_id=empresa.id,
        compra_id=compra.id,
        fecha=date.today(),
        operador_id=usuario.id,
    )
    assert desposte.estado == "en_proceso"
    assert desposte.compra_id == compra.id
    assert desposte.operador_id == usuario.id
    assert desposte.rendimiento_total == Decimal("0.000")
    assert desposte.merma == Decimal("0.000")


@pytest.mark.asyncio
async def test_crear_desposte_compra_no_existe(
    db_session: AsyncSession,
    empresa: Empresa,
    usuario: Usuario,
):
    with pytest.raises(NotFoundException) as exc_info:
        await desposte_service.crear_desposte(
            db=db_session,
            empresa_id=empresa.id,
            compra_id=uuid.uuid4(),
            fecha=date.today(),
            operador_id=usuario.id,
        )
    assert "Compra no encontrada" in str(exc_info.value)


@pytest.mark.asyncio
async def test_crear_desposte_operador_no_existe(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
):
    with pytest.raises(NotFoundException) as exc_info:
        await desposte_service.crear_desposte(
            db=db_session,
            empresa_id=empresa.id,
            compra_id=compra.id,
            fecha=date.today(),
            operador_id=uuid.uuid4(),
        )
    assert "Operador no encontrado" in str(exc_info.value)


@pytest.mark.asyncio
async def test_crear_desposte_aislamiento_multi_tenant(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
    usuario: Usuario,
):
    otra_empresa = Empresa(
        nombre_comercial="Otra",
        razon_social="Otra SA",
        cuit="30701234569",
    )
    db_session.add(otra_empresa)
    await db_session.commit()

    with pytest.raises(NotFoundException):
        await desposte_service.crear_desposte(
            db=db_session,
            empresa_id=otra_empresa.id,
            compra_id=compra.id,
            fecha=date.today(),
            operador_id=usuario.id,
        )


# ---------------------------------------------------------------------------
# Tests: Agregar Corte
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_agregar_corte_exitoso(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
    usuario: Usuario,
    producto_asado: Producto,
):
    desposte = await desposte_service.crear_desposte(
        db=db_session,
        empresa_id=empresa.id,
        compra_id=compra.id,
        fecha=date.today(),
        operador_id=usuario.id,
    )

    corte = await desposte_service.agregar_corte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        tipo_corte="asado",
        kilos_obtenidos=Decimal("20.000"),
        producto_id=producto_asado.id,
    )

    assert corte.tipo_corte == "asado"
    assert corte.kilos_obtenidos == Decimal("20.000")
    assert corte.porcentaje_rendimiento == Decimal("20.000")
    assert corte.costo_asignado == Decimal("100.00")
    assert corte.costo_final_por_kilo == Decimal("5.00")
    assert corte.producto_id == producto_asado.id


@pytest.mark.asyncio
async def test_agregar_corte_tipo_invalido(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
    usuario: Usuario,
):
    desposte = await desposte_service.crear_desposte(
        db=db_session,
        empresa_id=empresa.id,
        compra_id=compra.id,
        fecha=date.today(),
        operador_id=usuario.id,
    )

    with pytest.raises(BasileException) as exc_info:
        await desposte_service.agregar_corte(
            db=db_session,
            desposte_id=desposte.id,
            empresa_id=empresa.id,
            tipo_corte="corte_invalido",
            kilos_obtenidos=Decimal("10.000"),
        )
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_agregar_corte_kilos_negativos(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
    usuario: Usuario,
):
    desposte = await desposte_service.crear_desposte(
        db=db_session,
        empresa_id=empresa.id,
        compra_id=compra.id,
        fecha=date.today(),
        operador_id=usuario.id,
    )

    with pytest.raises(BasileException) as exc_info:
        await desposte_service.agregar_corte(
            db=db_session,
            desposte_id=desposte.id,
            empresa_id=empresa.id,
            tipo_corte="asado",
            kilos_obtenidos=Decimal("0.000"),
        )
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_agregar_corte_desposte_finalizado(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
    usuario: Usuario,
    producto_asado: Producto,
):
    desposte = await desposte_service.crear_desposte(
        db=db_session,
        empresa_id=empresa.id,
        compra_id=compra.id,
        fecha=date.today(),
        operador_id=usuario.id,
    )

    await desposte_service.agregar_corte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        tipo_corte="asado",
        kilos_obtenidos=Decimal("20.000"),
        producto_id=producto_asado.id,
    )

    await desposte_service.finalizar_desposte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        operador_id=usuario.id,
    )

    with pytest.raises(ConflictException):
        await desposte_service.agregar_corte(
            db=db_session,
            desposte_id=desposte.id,
            empresa_id=empresa.id,
            tipo_corte="vacio",
            kilos_obtenidos=Decimal("10.000"),
        )


# ---------------------------------------------------------------------------
# Tests: Calcular Costos
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_calculos_corte(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
    usuario: Usuario,
    producto_asado: Producto,
):
    desposte = await desposte_service.crear_desposte(
        db=db_session,
        empresa_id=empresa.id,
        compra_id=compra.id,
        fecha=date.today(),
        operador_id=usuario.id,
    )

    # Compra: 100kg, $500 -> costo por kg = $5
    corte = await desposte_service.agregar_corte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        tipo_corte="asado",
        kilos_obtenidos=Decimal("25.000"),
        producto_id=producto_asado.id,
    )

    assert corte.costo_asignado == Decimal("125.00")
    assert corte.costo_final_por_kilo == Decimal("5.00")
    assert corte.porcentaje_rendimiento == Decimal("25.000")


@pytest.mark.asyncio
async def test_calculos_multiples_cortes(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
    usuario: Usuario,
    producto_asado: Producto,
):
    desposte = await desposte_service.crear_desposte(
        db=db_session,
        empresa_id=empresa.id,
        compra_id=compra.id,
        fecha=date.today(),
        operador_id=usuario.id,
    )

    # Compra: 100kg, $500
    corte1 = await desposte_service.agregar_corte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        tipo_corte="asado",
        kilos_obtenidos=Decimal("20.000"),
        producto_id=producto_asado.id,
    )
    corte2 = await desposte_service.agregar_corte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        tipo_corte="vacio",
        kilos_obtenidos=Decimal("30.000"),
    )

    assert corte1.costo_asignado == Decimal("100.00")
    assert corte2.costo_asignado == Decimal("150.00")

    # Verificar rendimiento_total del desposte
    result = await db_session.execute(
        select(Desposte).where(Desposte.id == desposte.id)
    )
    desposte_actualizado = result.scalar_one()
    assert desposte_actualizado.rendimiento_total == Decimal("50.000")


# ---------------------------------------------------------------------------
# Tests: Finalizar Desposte
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_finalizar_desposte_exitoso(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
    usuario: Usuario,
    producto_asado: Producto,
):
    desposte = await desposte_service.crear_desposte(
        db=db_session,
        empresa_id=empresa.id,
        compra_id=compra.id,
        fecha=date.today(),
        operador_id=usuario.id,
    )

    await desposte_service.agregar_corte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        tipo_corte="asado",
        kilos_obtenidos=Decimal("80.000"),
        producto_id=producto_asado.id,
    )

    desposte_finalizado = await desposte_service.finalizar_desposte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        operador_id=usuario.id,
    )

    assert desposte_finalizado.estado == "finalizado"
    assert desposte_finalizado.rendimiento_total == Decimal("80.000")
    assert desposte_finalizado.merma == Decimal("20.000")


@pytest.mark.asyncio
async def test_finalizar_desposte_rendimiento_mayor_peso(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
    usuario: Usuario,
    producto_asado: Producto,
):
    desposte = await desposte_service.crear_desposte(
        db=db_session,
        empresa_id=empresa.id,
        compra_id=compra.id,
        fecha=date.today(),
        operador_id=usuario.id,
    )

    await desposte_service.agregar_corte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        tipo_corte="asado",
        kilos_obtenidos=Decimal("100.000"),
        producto_id=producto_asado.id,
    )
    await desposte_service.agregar_corte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        tipo_corte="vacio",
        kilos_obtenidos=Decimal("10.000"),
    )

    with pytest.raises(BasileException) as exc_info:
        await desposte_service.finalizar_desposte(
            db=db_session,
            desposte_id=desposte.id,
            empresa_id=empresa.id,
            operador_id=usuario.id,
        )
    assert exc_info.value.status_code == 422
    assert "rendimiento total" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_finalizar_desposte_sin_cortes(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
    usuario: Usuario,
):
    desposte = await desposte_service.crear_desposte(
        db=db_session,
        empresa_id=empresa.id,
        compra_id=compra.id,
        fecha=date.today(),
        operador_id=usuario.id,
    )

    with pytest.raises(BasileException) as exc_info:
        await desposte_service.finalizar_desposte(
            db=db_session,
            desposte_id=desposte.id,
            empresa_id=empresa.id,
            operador_id=usuario.id,
        )
    assert exc_info.value.status_code == 422
    assert "al menos un corte" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_finalizar_desposte_ya_finalizado(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
    usuario: Usuario,
    producto_asado: Producto,
):
    desposte = await desposte_service.crear_desposte(
        db=db_session,
        empresa_id=empresa.id,
        compra_id=compra.id,
        fecha=date.today(),
        operador_id=usuario.id,
    )

    await desposte_service.agregar_corte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        tipo_corte="asado",
        kilos_obtenidos=Decimal("80.000"),
        producto_id=producto_asado.id,
    )

    await desposte_service.finalizar_desposte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        operador_id=usuario.id,
    )

    with pytest.raises(ConflictException) as exc_info:
        await desposte_service.finalizar_desposte(
            db=db_session,
            desposte_id=desposte.id,
            empresa_id=empresa.id,
            operador_id=usuario.id,
        )
    assert "ya está finalizado" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Tests: Generación de Stock
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_generacion_stock_al_finalizar(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
    usuario: Usuario,
    producto_asado: Producto,
):
    stock_inicial = producto_asado.stock_actual

    desposte = await desposte_service.crear_desposte(
        db=db_session,
        empresa_id=empresa.id,
        compra_id=compra.id,
        fecha=date.today(),
        operador_id=usuario.id,
    )

    await desposte_service.agregar_corte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        tipo_corte="asado",
        kilos_obtenidos=Decimal("25.000"),
        producto_id=producto_asado.id,
    )

    await desposte_service.finalizar_desposte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        operador_id=usuario.id,
    )

    # Verificar movimiento de stock
    result = await db_session.execute(
        select(MovimientoStock).where(
            MovimientoStock.referencia_id == str(desposte.id),
            MovimientoStock.tipo == "entrada_desposte",
        )
    )
    movimiento = result.scalar_one()
    assert movimiento.cantidad_kilos == Decimal("25.000")
    assert movimiento.stock_resultante == stock_inicial + Decimal("25.000")
    assert movimiento.producto_id == producto_asado.id

    # Verificar stock actual del producto
    result = await db_session.execute(
        select(Producto).where(Producto.id == producto_asado.id)
    )
    producto_actualizado = result.scalar_one()
    assert producto_actualizado.stock_actual == stock_inicial + Decimal("25.000")


@pytest.mark.asyncio
async def test_corte_sin_producto_no_genera_stock(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
    usuario: Usuario,
):
    desposte = await desposte_service.crear_desposte(
        db=db_session,
        empresa_id=empresa.id,
        compra_id=compra.id,
        fecha=date.today(),
        operador_id=usuario.id,
    )

    await desposte_service.agregar_corte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        tipo_corte="asado",
        kilos_obtenidos=Decimal("25.000"),
        producto_id=None,
    )

    await desposte_service.finalizar_desposte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        operador_id=usuario.id,
    )

    # Verificar que no se creó movimiento de stock
    result = await db_session.execute(
        select(MovimientoStock).where(
            MovimientoStock.referencia_id == str(desposte.id),
        )
    )
    assert result.scalar_one_or_none() is None


# ---------------------------------------------------------------------------
# Tests: Listar y Obtener
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_listar_despostes_filtra_por_empresa(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
    usuario: Usuario,
):
    desposte = await desposte_service.crear_desposte(
        db=db_session,
        empresa_id=empresa.id,
        compra_id=compra.id,
        fecha=date.today(),
        operador_id=usuario.id,
    )

    despostes, total = await desposte_service.listar_despostes(
        db=db_session,
        empresa_id=empresa.id,
    )
    assert total == 1
    assert len(despostes) == 1
    assert despostes[0].id == desposte.id

    # Verificar aislamiento
    otra_empresa = Empresa(
        nombre_comercial="Otra",
        razon_social="Otra SA",
        cuit="30701234569",
    )
    db_session.add(otra_empresa)
    await db_session.commit()

    despostes, total = await desposte_service.listar_despostes(
        db=db_session,
        empresa_id=otra_empresa.id,
    )
    assert total == 0


@pytest.mark.asyncio
async def test_obtener_desposte_con_cortes(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
    usuario: Usuario,
    producto_asado: Producto,
):
    desposte = await desposte_service.crear_desposte(
        db=db_session,
        empresa_id=empresa.id,
        compra_id=compra.id,
        fecha=date.today(),
        operador_id=usuario.id,
    )

    await desposte_service.agregar_corte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        tipo_corte="asado",
        kilos_obtenidos=Decimal("20.000"),
        producto_id=producto_asado.id,
    )

    desposte_obtenido = await desposte_service.obtener_desposte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
    )

    assert len(desposte_obtenido.cortes) == 1
    assert desposte_obtenido.cortes[0].tipo_corte == "asado"
    assert desposte_obtenido.compra is not None
    assert desposte_obtenido.operador is not None


@pytest.mark.asyncio
async def test_obtener_desposte_no_existe(
    db_session: AsyncSession,
    empresa: Empresa,
):
    with pytest.raises(NotFoundException):
        await desposte_service.obtener_desposte(
            db=db_session,
            desposte_id=uuid.uuid4(),
            empresa_id=empresa.id,
        )


# ---------------------------------------------------------------------------
# Tests: Auditoría
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_auditoria_al_finalizar(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
    usuario: Usuario,
    producto_asado: Producto,
    caplog,
):
    desposte = await desposte_service.crear_desposte(
        db=db_session,
        empresa_id=empresa.id,
        compra_id=compra.id,
        fecha=date.today(),
        operador_id=usuario.id,
    )

    await desposte_service.agregar_corte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        tipo_corte="asado",
        kilos_obtenidos=Decimal("80.000"),
        producto_id=producto_asado.id,
    )

    import logging
    with caplog.at_level(logging.INFO, logger="basile.auditoria"):
        await desposte_service.finalizar_desposte(
            db=db_session,
            desposte_id=desposte.id,
            empresa_id=empresa.id,
            operador_id=usuario.id,
        )

    assert "FINALIZAR_DESPOSTE" in caplog.text


# ---------------------------------------------------------------------------
# Tests: Upsert de Corte
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_agregar_corte_actualiza_existente(
    db_session: AsyncSession,
    empresa: Empresa,
    compra: Compra,
    usuario: Usuario,
    producto_asado: Producto,
):
    desposte = await desposte_service.crear_desposte(
        db=db_session,
        empresa_id=empresa.id,
        compra_id=compra.id,
        fecha=date.today(),
        operador_id=usuario.id,
    )

    corte1 = await desposte_service.agregar_corte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        tipo_corte="asado",
        kilos_obtenidos=Decimal("20.000"),
        producto_id=producto_asado.id,
    )

    corte2 = await desposte_service.agregar_corte(
        db=db_session,
        desposte_id=desposte.id,
        empresa_id=empresa.id,
        tipo_corte="asado",
        kilos_obtenidos=Decimal("25.000"),
        producto_id=producto_asado.id,
    )

    assert corte1.id == corte2.id
    assert corte2.kilos_obtenidos == Decimal("25.000")
    assert corte2.costo_asignado == Decimal("125.00")

    result = await db_session.execute(
        select(CorteDesposte).where(CorteDesposte.desposte_id == desposte.id)
    )
    cortes = result.scalars().all()
    assert len(cortes) == 1
    assert cortes[0].kilos_obtenidos == Decimal("25.000")
