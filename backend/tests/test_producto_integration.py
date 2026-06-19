import uuid
from decimal import Decimal
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.auth.models import Usuario, Rol, Empresa
from src.modules.producto.models import Producto, CategoriaProducto
from src.core.security import hash_password, create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _crear_empresa(db_session: AsyncSession, nombre: str = "Carnicería Test") -> Empresa:
    empresa = Empresa(nombre_comercial=nombre, activa=True)
    db_session.add(empresa)
    await db_session.commit()
    await db_session.refresh(empresa)
    return empresa


async def _crear_rol(db_session: AsyncSession, nombre: str = "Administrador", empresa_id=None) -> Rol:
    rol = Rol(nombre=nombre, empresa_id=empresa_id)
    db_session.add(rol)
    await db_session.commit()
    await db_session.refresh(rol)
    return rol


async def _crear_usuario(
    db_session: AsyncSession,
    email: str = "test@basile.app",
    password: str = "Password123",
    activo: bool = True,
    empresa_id=None,
    rol_id=None,
) -> Usuario:
    if rol_id is None:
        rol = await _crear_rol(db_session, empresa_id=empresa_id)
        rol_id = rol.id
    usuario = Usuario(
        email=email,
        contrasena_hash=hash_password(password),
        nombre="Test",
        apellido="User",
        rol_id=rol_id,
        activo=activo,
        empresa_id=empresa_id,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    return usuario


def _auth_header(usuario: Usuario, rol_nombre: str = "Administrador", empresa_id=None):
    token = create_access_token({
        "sub": str(usuario.id),
        "empresa_id": str(empresa_id or usuario.empresa_id),
        "rol": rol_nombre,
    })
    return {"Authorization": f"Bearer {token}"}


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
        activo=activo,
    )
    producto.recalcular_margen()
    db_session.add(producto)
    await db_session.commit()
    await db_session.refresh(producto)
    return producto


# ---------------------------------------------------------------------------
# TASK-4.1: POST /producto
# ---------------------------------------------------------------------------
class TestCreateProducto:
    async def test_crear_producto_exitoso(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        rol = await _crear_rol(db_session, nombre="Encargado", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="enc@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.post("/producto", headers=_auth_header(usuario, rol_nombre="Encargado", empresa_id=empresa.id), json={
            "plu": "123",
            "nombre": "Vacio Especial",
            "categoria_id": str(cat.id),
            "precio_publico": "1500.00",
            "precio_mayorista": "1200.00",
            "costo_por_kilo": "900.00",
            "stock_actual": "25.00",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["plu"] == "123"
        assert data["nombre"] == "Vacio Especial"
        assert data["margen"] == "0.4000"
        assert data["empresa_id"] == str(empresa.id)

    async def test_crear_producto_plu_duplicado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        await _crear_producto(db_session, empresa.id, plu="DUP", categoria_id=cat.id)

        response = await client.post("/producto", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "plu": "DUP",
            "nombre": "Otro",
            "categoria_id": str(cat.id),
            "precio_publico": "100.00",
            "precio_mayorista": "80.00",
            "costo_por_kilo": "50.00",
            "stock_actual": "1.00",
        })
        assert response.status_code == 409

    async def test_crear_producto_precio_negativo(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.post("/producto", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "plu": "NEG",
            "nombre": "Negativo",
            "categoria_id": str(cat.id),
            "precio_publico": "-100.00",
            "precio_mayorista": "80.00",
            "costo_por_kilo": "50.00",
            "stock_actual": "1.00",
        })
        assert response.status_code == 422

    async def test_crear_producto_sin_permiso(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        rol = await _crear_rol(db_session, nombre="Cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.post("/producto", headers=_auth_header(usuario, rol_nombre="Cajero", empresa_id=empresa.id), json={
            "plu": "001",
            "nombre": "Vacio",
            "categoria_id": str(cat.id),
            "precio_publico": "100.00",
            "precio_mayorista": "80.00",
            "costo_por_kilo": "50.00",
            "stock_actual": "1.00",
        })
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# TASK-4.2: GET /producto
# ---------------------------------------------------------------------------
class TestListProductos:
    async def test_listar_paginado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        rol = await _crear_rol(db_session, nombre="Vendedor", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="vend@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        for i in range(25):
            await _crear_producto(db_session, empresa.id, plu=f"{i:03d}", nombre=f"Producto {i}", categoria_id=cat.id)

        response = await client.get("/producto", headers=_auth_header(usuario, rol_nombre="Vendedor", empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["items"]) == 20  # default limit

    async def test_buscar_por_nombre(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        rol = await _crear_rol(db_session, nombre="Cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        await _crear_producto(db_session, empresa.id, plu="VAC", nombre="Vacio Especial", categoria_id=cat.id)
        await _crear_producto(db_session, empresa.id, plu="NAL", nombre="Nalga Premium", categoria_id=cat.id)

        response = await client.get("/producto?search=vacio", headers=_auth_header(usuario, rol_nombre="Cajero", empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["nombre"] == "Vacio Especial"

    async def test_buscar_por_plu(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        rol = await _crear_rol(db_session, nombre="Cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        await _crear_producto(db_session, empresa.id, plu="PLU123", nombre="Test", categoria_id=cat.id)
        await _crear_producto(db_session, empresa.id, plu="PLU456", nombre="Otro", categoria_id=cat.id)

        response = await client.get("/producto?search=PLU123", headers=_auth_header(usuario, rol_nombre="Cajero", empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["plu"] == "PLU123"

    async def test_listar_filtrar_por_categoria(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat1 = await _crear_categoria(db_session, empresa.id, "Cat A")
        cat2 = await _crear_categoria(db_session, empresa.id, "Cat B")
        rol = await _crear_rol(db_session, nombre="Cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        await _crear_producto(db_session, empresa.id, plu="A1", nombre="Prod A", categoria_id=cat1.id)
        await _crear_producto(db_session, empresa.id, plu="B1", nombre="Prod B", categoria_id=cat2.id)

        response = await client.get(f"/producto?categoria_id={cat1.id}", headers=_auth_header(usuario, rol_nombre="Cajero", empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["nombre"] == "Prod A"

    async def test_listar_solo_activos_por_defecto(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        rol = await _crear_rol(db_session, nombre="Cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        await _crear_producto(db_session, empresa.id, plu="ACT", nombre="Activo", categoria_id=cat.id, activo=True)
        await _crear_producto(db_session, empresa.id, plu="INA", nombre="Inactivo", categoria_id=cat.id, activo=False)

        response = await client.get("/producto", headers=_auth_header(usuario, rol_nombre="Cajero", empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["nombre"] == "Activo"


# ---------------------------------------------------------------------------
# TASK-4.3: GET /producto/{id}
# ---------------------------------------------------------------------------
class TestGetProducto:
    async def test_obtener_producto_exitoso(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        rol = await _crear_rol(db_session, nombre="Cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, plu="GET1", categoria_id=cat.id)

        response = await client.get(f"/producto/{producto.id}", headers=_auth_header(usuario, rol_nombre="Cajero", empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["plu"] == "GET1"

    async def test_obtener_producto_otra_empresa(self, client: AsyncClient, db_session: AsyncSession):
        empresa1 = await _crear_empresa(db_session, "E1")
        empresa2 = await _crear_empresa(db_session, "E2")
        cat = await _crear_categoria(db_session, empresa1.id)
        # Crear usuario en empresa2 para intentar acceder a producto de empresa1
        rol = await _crear_rol(db_session, nombre="Cajero", empresa_id=empresa2.id)
        usuario2 = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa2.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa1.id, plu="PRIV", categoria_id=cat.id)

        response = await client.get(f"/producto/{producto.id}", headers=_auth_header(usuario2, rol_nombre="Cajero", empresa_id=empresa2.id))
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# TASK-4.4: PUT /producto/{id}
# ---------------------------------------------------------------------------
class TestUpdateProducto:
    async def test_actualizar_nombre_y_precio(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        rol = await _crear_rol(db_session, nombre="Encargado", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="enc@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, plu="UPD", categoria_id=cat.id, precio_publico=Decimal("1000.0000"), costo_por_kilo=Decimal("600.0000"))
        assert producto.margen == Decimal("0.4000")

        response = await client.put(f"/producto/{producto.id}", headers=_auth_header(usuario, rol_nombre="Encargado", empresa_id=empresa.id), json={
            "nombre": "Nuevo Nombre",
            "precio_publico": "2000.00",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Nuevo Nombre"
        assert data["margen"] == "0.7000"

    async def test_actualizar_producto_otra_empresa(self, client: AsyncClient, db_session: AsyncSession):
        empresa1 = await _crear_empresa(db_session, "E1")
        empresa2 = await _crear_empresa(db_session, "E2")
        cat = await _crear_categoria(db_session, empresa1.id)
        # Crear usuario en empresa2
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa2.id)
        usuario2 = await _crear_usuario(db_session, email="admin2@basile.app", empresa_id=empresa2.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa1.id, plu="PRIV", categoria_id=cat.id)

        response = await client.put(f"/producto/{producto.id}", headers=_auth_header(usuario2, empresa_id=empresa2.id), json={
            "nombre": "Robo",
        })
        assert response.status_code == 404

    async def test_actualizar_sin_permiso(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        rol = await _crear_rol(db_session, nombre="Cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, plu="NOUPD", categoria_id=cat.id)

        response = await client.put(f"/producto/{producto.id}", headers=_auth_header(usuario, rol_nombre="Cajero", empresa_id=empresa.id), json={
            "nombre": "Intento",
        })
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# TASK-4.5: PATCH /producto/{id}/activo
# ---------------------------------------------------------------------------
class TestToggleProductoActivo:
    async def test_desactivar_producto(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        rol = await _crear_rol(db_session, nombre="Encargado", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="enc@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, plu="DES", categoria_id=cat.id)

        response = await client.patch(f"/producto/{producto.id}/activo", headers=_auth_header(usuario, rol_nombre="Encargado", empresa_id=empresa.id), json={
            "activo": False,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["activo"] is False

    async def test_reactivar_producto(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, plu="REA", categoria_id=cat.id, activo=False)

        response = await client.patch(f"/producto/{producto.id}/activo", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "activo": True,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["activo"] is True

    async def test_toggle_sin_permiso(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id)
        rol = await _crear_rol(db_session, nombre="Vendedor", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="vend@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, plu="NOTOGGLE", categoria_id=cat.id)

        response = await client.patch(f"/producto/{producto.id}/activo", headers=_auth_header(usuario, rol_nombre="Vendedor", empresa_id=empresa.id), json={
            "activo": False,
        })
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# TASK-5.1: POST /producto/categorias
# ---------------------------------------------------------------------------
class TestCreateCategoria:
    async def test_crear_categoria_exitoso(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Encargado", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="enc@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.post("/producto/categorias", headers=_auth_header(usuario, rol_nombre="Encargado", empresa_id=empresa.id), json={
            "nombre": "Carnes Premium",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == "Carnes Premium"
        assert data["empresa_id"] == str(empresa.id)

    async def test_crear_categoria_duplicada(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        await client.post("/producto/categorias", headers=_auth_header(usuario, empresa_id=empresa.id), json={"nombre": "Unica"})
        response = await client.post("/producto/categorias", headers=_auth_header(usuario, empresa_id=empresa.id), json={"nombre": "unica"})
        assert response.status_code == 409

    async def test_crear_categoria_sin_permiso(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.post("/producto/categorias", headers=_auth_header(usuario, rol_nombre="Cajero", empresa_id=empresa.id), json={
            "nombre": "Intento",
        })
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# TASK-5.2: GET /producto/categorias
# ---------------------------------------------------------------------------
class TestListCategorias:
    async def test_listar_categorias(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await _crear_categoria(db_session, empresa.id, "A")
        await _crear_categoria(db_session, empresa.id, "B")
        rol = await _crear_rol(db_session, nombre="Cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.get("/producto/categorias", headers=_auth_header(usuario, rol_nombre="Cajero", empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    async def test_listar_categorias_otra_empresa_vacia(self, client: AsyncClient, db_session: AsyncSession):
        empresa1 = await _crear_empresa(db_session, "E1")
        empresa2 = await _crear_empresa(db_session, "E2")
        await _crear_categoria(db_session, empresa1.id, "Privada")
        # Usuario de empresa2 intenta listar categorías
        rol = await _crear_rol(db_session, nombre="Cajero", empresa_id=empresa2.id)
        usuario2 = await _crear_usuario(db_session, email="cajero2@basile.app", empresa_id=empresa2.id, rol_id=rol.id)

        response = await client.get("/producto/categorias", headers=_auth_header(usuario2, rol_nombre="Cajero", empresa_id=empresa2.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0


# ---------------------------------------------------------------------------
# TASK-5.3: PUT /producto/categorias/{id}
# ---------------------------------------------------------------------------
class TestUpdateCategoria:
    async def test_actualizar_nombre(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id, "Viejo")
        rol = await _crear_rol(db_session, nombre="Encargado", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="enc@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.put(f"/producto/categorias/{cat.id}", headers=_auth_header(usuario, rol_nombre="Encargado", empresa_id=empresa.id), json={
            "nombre": "Nuevo",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Nuevo"

    async def test_actualizar_sin_permiso(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id, "No Touch")
        rol = await _crear_rol(db_session, nombre="Cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.put(f"/producto/categorias/{cat.id}", headers=_auth_header(usuario, rol_nombre="Cajero", empresa_id=empresa.id), json={
            "nombre": "Intento",
        })
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# TASK-5.4: DELETE /producto/categorias/{id}
# ---------------------------------------------------------------------------
class TestDeleteCategoria:
    async def test_eliminar_categoria_vacia(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id, "Vacía")
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.delete(f"/producto/categorias/{cat.id}", headers=_auth_header(usuario, empresa_id=empresa.id))
        assert response.status_code == 204

    async def test_eliminar_categoria_con_productos(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id, "Con Productos")
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        await _crear_producto(db_session, empresa.id, plu="CP", categoria_id=cat.id)

        response = await client.delete(f"/producto/categorias/{cat.id}", headers=_auth_header(usuario, empresa_id=empresa.id))
        assert response.status_code == 409

    async def test_eliminar_sin_permiso_encargado(self, client: AsyncClient, db_session: AsyncSession):
        # Encargado no tiene permiso productos:delete en la matriz RBAC
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id, "No Delete")
        rol = await _crear_rol(db_session, nombre="Encargado", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="enc@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.delete(f"/producto/categorias/{cat.id}", headers=_auth_header(usuario, rol_nombre="Encargado", empresa_id=empresa.id))
        assert response.status_code == 403
