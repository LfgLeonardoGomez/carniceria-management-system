from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.modules.producto import schemas


# ---------------------------------------------------------------------------
# TASK-3.1: Producto schema tests
# ---------------------------------------------------------------------------
class TestProductoSchemas:
    def test_create_valid(self):
        data = schemas.ProductoCreate(
            plu="001",
            nombre="Vacio",
            categoria_id=None,
            precio_publico=Decimal("1000.00"),
            precio_mayorista=Decimal("800.00"),
            costo_por_kilo=Decimal("600.00"),
            stock_actual=Decimal("10.00"),
        )
        assert data.plu == "001"
        assert data.precio_publico == Decimal("1000.00")

    def test_create_precio_negativo_rechazado(self):
        with pytest.raises(ValidationError):
            schemas.ProductoCreate(
                plu="001",
                nombre="Vacio",
                precio_publico=Decimal("-100"),
                precio_mayorista=Decimal("800"),
                costo_por_kilo=Decimal("600"),
                stock_actual=Decimal("10"),
            )

    def test_create_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            schemas.ProductoCreate(
                plu="001",
                nombre="Vacio",
                precio_publico=Decimal("100"),
                precio_mayorista=Decimal("80"),
                costo_por_kilo=Decimal("50"),
                stock_actual=Decimal("1"),
                campo_extra="no permitido",
            )

    def test_update_partial(self):
        data = schemas.ProductoUpdate(nombre="Nuevo Nombre")
        assert data.nombre == "Nuevo Nombre"
        assert data.precio_publico is None

    def test_public_serialization(self):
        import uuid
        from datetime import datetime
        data = schemas.ProductoPublic(
            id=uuid.uuid4(),
            empresa_id=uuid.uuid4(),
            plu="001",
            nombre="Vacio",
            categoria_id=None,
            precio_publico=Decimal("1000.00"),
            precio_mayorista=Decimal("800.00"),
            costo_por_kilo=Decimal("600.00"),
            margen=Decimal("0.4000"),
            stock_actual=Decimal("10.00"),
            stock_minimo=None,
            activo=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert data.margen == Decimal("0.4000")


# ---------------------------------------------------------------------------
# TASK-3.2: CategoriaProducto schema tests
# ---------------------------------------------------------------------------
class TestCategoriaProductoSchemas:
    def test_create_valid(self):
        data = schemas.CategoriaProductoCreate(nombre="Carnes")
        assert data.nombre == "Carnes"

    def test_create_nombre_vacio_rechazado(self):
        with pytest.raises(ValidationError):
            schemas.CategoriaProductoCreate(nombre="")

    def test_update_valid(self):
        data = schemas.CategoriaProductoUpdate(nombre="Nuevo")
        assert data.nombre == "Nuevo"

    def test_public_serialization(self):
        import uuid
        from datetime import datetime
        data = schemas.CategoriaProductoPublic(
            id=uuid.uuid4(),
            empresa_id=uuid.uuid4(),
            nombre="Carnes",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert data.nombre == "Carnes"


# ---------------------------------------------------------------------------
# TASK-3.3: Paginated response tests
# ---------------------------------------------------------------------------
class TestPaginatedSchemas:
    def test_paginated_producto_empty(self):
        data = schemas.PaginatedProductoResponse(items=[], total=0, skip=0, limit=20)
        assert data.total == 0
        assert len(data.items) == 0

    def test_paginated_categoria_empty(self):
        data = schemas.PaginatedCategoriaResponse(items=[], total=0, skip=0, limit=20)
        assert data.total == 0
