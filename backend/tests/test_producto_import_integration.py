import uuid
from decimal import Decimal
from io import BytesIO

import pytest
from httpx import AsyncClient
from openpyxl import Workbook
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.models import Usuario, Rol, Empresa
from src.modules.producto.models import Producto, CategoriaProducto
from src.core.security import hash_password, create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _crear_empresa(db_session: AsyncSession, nombre: str = "Test") -> Empresa:
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


def _build_xlsx(rows: list[dict], headers: list[str] = None) -> bytes:
    """Construye un archivo xlsx en memoria desde filas de dict."""
    if headers is None:
        headers = list(rows[0].keys()) if rows else []
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h) for h in headers])
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# TASK-6.2: Tests parser Excel QUENDRA
# ---------------------------------------------------------------------------
class TestImportParser:
    async def test_mapeo_columnas_quendra(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await _crear_categoria(db_session, empresa.id, "Carne vacuna")
        rol = await _crear_rol(db_session, empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        data = _build_xlsx([
            {
                "PLU": "001",
                "Nombre": "Asado",
                "Categoria": "Carne vacuna",
                "Precio_Publico": "1500.00",
                "Precio_Mayorista": "1200.00",
                "Costo_Kilo": "900.00",
                "Stock_Actual": "10.00",
                "Stock_Minimo": "2.00",
            }
        ], headers=["PLU", "Nombre", "Categoria", "Precio_Publico", "Precio_Mayorista", "Costo_Kilo", "Stock_Actual", "Stock_Minimo"])

        response = await client.post(
            "/producto/import",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            files={"file": ("quendra.xlsx", data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert response.status_code == 200
        preview = response.json()
        assert preview["validas_count"] == 1
        assert preview["filas_validas"][0]["nombre"] == "Asado"

    async def test_detecta_duplicados_plu_en_archivo(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await _crear_categoria(db_session, empresa.id, "Carne vacuna")
        rol = await _crear_rol(db_session, empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        data = _build_xlsx([
            {"PLU": "001", "Nombre": "Asado", "Categoria": "Carne vacuna", "Precio_Publico": "100", "Precio_Mayorista": "80", "Costo_Kilo": "50", "Stock_Actual": "1"},
            {"PLU": "001", "Nombre": "Asado2", "Categoria": "Carne vacuna", "Precio_Publico": "100", "Precio_Mayorista": "80", "Costo_Kilo": "50", "Stock_Actual": "1"},
        ])

        response = await client.post(
            "/producto/import",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            files={"file": ("dup.xlsx", data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert response.status_code == 200
        preview = response.json()
        assert preview["invalidas_count"] == 1
        assert "duplicado" in preview["filas_invalidas"][0]["errores"][0].lower()

    async def test_detecta_plu_existente_en_empresa(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cat = await _crear_categoria(db_session, empresa.id, "Carne vacuna")
        # Crear producto existente
        p = Producto(
            empresa_id=empresa.id, plu="EXISTE", nombre="Ya existe",
            categoria_id=cat.id, precio_publico=Decimal("100"), precio_mayorista=Decimal("80"),
            costo_por_kilo=Decimal("50"), stock_actual=Decimal("1"),
        )
        p.recalcular_margen()
        db_session.add(p)
        await db_session.commit()

        rol = await _crear_rol(db_session, empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        data = _build_xlsx([
            {"PLU": "EXISTE", "Nombre": "Nuevo", "Categoria": "Carne vacuna", "Precio_Publico": "200", "Precio_Mayorista": "160", "Costo_Kilo": "100", "Stock_Actual": "2"},
        ])

        response = await client.post(
            "/producto/import",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            files={"file": ("exist.xlsx", data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert response.status_code == 200
        preview = response.json()
        assert preview["invalidas_count"] == 1
        assert "ya existe" in preview["filas_invalidas"][0]["errores"][0].lower()

    async def test_rechaza_formato_no_xlsx(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.post(
            "/producto/import",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            files={"file": ("datos.csv", b"PLU,Nombre\n001,Asado", "text/csv")},
        )
        assert response.status_code == 415

    async def test_detecta_precio_no_numerico(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await _crear_categoria(db_session, empresa.id, "Carne vacuna")
        rol = await _crear_rol(db_session, empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        data = _build_xlsx([
            {"PLU": "001", "Nombre": "Asado", "Categoria": "Carne vacuna", "Precio_Publico": "foo", "Precio_Mayorista": "80", "Costo_Kilo": "50", "Stock_Actual": "1"},
        ])

        response = await client.post(
            "/producto/import",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            files={"file": ("bad.xlsx", data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert response.status_code == 200
        preview = response.json()
        assert preview["invalidas_count"] == 1
        assert "numérico" in preview["filas_invalidas"][0]["errores"][0].lower()

    async def test_detecta_nombre_vacio(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await _crear_categoria(db_session, empresa.id, "Carne vacuna")
        rol = await _crear_rol(db_session, empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        data = _build_xlsx([
            {"PLU": "001", "Nombre": "", "Categoria": "Carne vacuna", "Precio_Publico": "100", "Precio_Mayorista": "80", "Costo_Kilo": "50", "Stock_Actual": "1"},
        ])

        response = await client.post(
            "/producto/import",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            files={"file": ("empty.xlsx", data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert response.status_code == 200
        preview = response.json()
        assert preview["invalidas_count"] == 1
        assert "obligatorio" in preview["filas_invalidas"][0]["errores"][0].lower()

    async def test_rechaza_mas_de_5000_filas(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        rows = [{"PLU": f"{i:05d}", "Nombre": f"Prod {i}", "Precio_Publico": "100"} for i in range(5001)]
        data = _build_xlsx(rows)

        response = await client.post(
            "/producto/import",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            files={"file": ("big.xlsx", data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert response.status_code == 413

    async def test_categoria_inexistente(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        data = _build_xlsx([
            {"PLU": "001", "Nombre": "Asado", "Categoria": "NoExiste", "Precio_Publico": "100", "Precio_Mayorista": "80", "Costo_Kilo": "50", "Stock_Actual": "1"},
        ])

        response = await client.post(
            "/producto/import",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            files={"file": ("badcat.xlsx", data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert response.status_code == 200
        preview = response.json()
        assert preview["invalidas_count"] == 1
        assert "categoría" in preview["filas_invalidas"][0]["errores"][0].lower()


# ---------------------------------------------------------------------------
# TASK-6.5: Confirmar importación
# ---------------------------------------------------------------------------
class TestImportConfirm:
    async def test_confirmar_importacion_exitosa(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await _crear_categoria(db_session, empresa.id, "Carne vacuna")
        rol = await _crear_rol(db_session, empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        data = _build_xlsx([
            {"PLU": "001", "Nombre": "Asado", "Categoria": "Carne vacuna", "Precio_Publico": "100", "Precio_Mayorista": "80", "Costo_Kilo": "50", "Stock_Actual": "1"},
            {"PLU": "002", "Nombre": "Vacio", "Categoria": "Carne vacuna", "Precio_Publico": "200", "Precio_Mayorista": "160", "Costo_Kilo": "100", "Stock_Actual": "2"},
        ])

        response = await client.post(
            "/producto/import",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            files={"file": ("confirm.xlsx", data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert response.status_code == 200
        preview = response.json()
        session_id = preview["session_id"]
        assert preview["validas_count"] == 2

        # Confirmar
        response = await client.post(
            f"/producto/import/confirm?session_id={session_id}",
            headers=_auth_header(usuario, empresa_id=empresa.id),
        )
        assert response.status_code == 200
        result = response.json()
        assert result["creados"] == 2
        assert result["errores"] == 0

        # Verificar que existen en DB
        from sqlalchemy import select
        db_result = await db_session.execute(
            select(Producto).where(Producto.empresa_id == empresa.id)
        )
        productos = db_result.scalars().all()
        assert len(productos) == 2

    async def test_confirmar_con_sesion_expirada(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.post(
            "/producto/import/confirm?session_id=sesion-falsa",
            headers=_auth_header(usuario, empresa_id=empresa.id),
        )
        assert response.status_code == 410

    async def test_confirmar_ignora_invalidas(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await _crear_categoria(db_session, empresa.id, "Carne vacuna")
        rol = await _crear_rol(db_session, empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        data = _build_xlsx([
            {"PLU": "001", "Nombre": "Asado", "Categoria": "Carne vacuna", "Precio_Publico": "100", "Precio_Mayorista": "80", "Costo_Kilo": "50", "Stock_Actual": "1"},
            {"PLU": "", "Nombre": "Sin PLU", "Categoria": "Carne vacuna", "Precio_Publico": "100", "Precio_Mayorista": "80", "Costo_Kilo": "50", "Stock_Actual": "1"},
        ])

        response = await client.post(
            "/producto/import",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            files={"file": ("mixed.xlsx", data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        preview = response.json()
        session_id = preview["session_id"]
        assert preview["validas_count"] == 1
        assert preview["invalidas_count"] == 1

        response = await client.post(
            f"/producto/import/confirm?session_id={session_id}",
            headers=_auth_header(usuario, empresa_id=empresa.id),
        )
        assert response.status_code == 200
        result = response.json()
        assert result["creados"] == 1

    async def test_importar_sin_permiso(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        data = _build_xlsx([
            {"PLU": "001", "Nombre": "Asado", "Precio_Publico": "100"},
        ])

        response = await client.post(
            "/producto/import",
            headers=_auth_header(usuario, rol_nombre="Cajero", empresa_id=empresa.id),
            files={"file": ("noperm.xlsx", data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert response.status_code == 403
