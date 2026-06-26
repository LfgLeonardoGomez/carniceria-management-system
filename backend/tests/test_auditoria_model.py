import uuid
from datetime import datetime, timezone, date, time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.auditoria.models import Auditoria
from src.modules.empresa.models import Empresa
from src.modules.auth.models import Usuario, Rol


class TestAuditoriaModel:
    """TASK-1.4: Tests para modelo Auditoria."""

    def test_auditoria_columns_exist(self):
        cols = {c.name for c in Auditoria.__table__.columns}
        required = {
            "id", "empresa_id", "usuario_id", "accion", "entidad_tipo",
            "entidad_id", "payload", "fecha", "hora", "created_at",
        }
        assert required.issubset(cols), f"Auditoria falta columnas: {required - cols}"

    def test_auditoria_empresa_id_not_nullable(self):
        col = Auditoria.__table__.columns["empresa_id"]
        assert not col.nullable, "empresa_id debe ser NOT NULL"

    def test_auditoria_accion_not_nullable(self):
        col = Auditoria.__table__.columns["accion"]
        assert not col.nullable, "accion debe ser NOT NULL"

    def test_auditoria_instance_creation(self):
        registro = Auditoria(
            empresa_id=uuid.uuid4(),
            usuario_id=uuid.uuid4(),
            accion="CREAR",
            entidad_tipo="venta",
            entidad_id=uuid.uuid4(),
            payload={"total": 150.00, "items": 2},
            fecha=datetime.now(timezone.utc).date(),
            hora=datetime.now(timezone.utc).time(),
        )
        assert registro.accion == "CREAR"
        assert registro.entidad_tipo == "venta"
        assert registro.payload == {"total": 150.00, "items": 2}
        assert registro.fecha is not None
        assert registro.hora is not None

    @pytest.mark.asyncio
    async def test_auditoria_insert_and_query(self, db_session: AsyncSession):
        empresa = Empresa(nombre_comercial="Test Empresa Auditoria")
        db_session.add(empresa)
        await db_session.commit()
        await db_session.refresh(empresa)

        registro = Auditoria(
            empresa_id=empresa.id,
            accion="AJUSTAR",
            entidad_tipo="stock",
            entidad_id=uuid.uuid4(),
            payload={"antes": 10.0, "despues": 8.0},
            fecha=datetime.now(timezone.utc).date(),
            hora=datetime.now(timezone.utc).time(),
        )
        db_session.add(registro)
        await db_session.commit()
        await db_session.refresh(registro)

        result = await db_session.execute(
            select(Auditoria).where(Auditoria.id == registro.id)
        )
        fetched = result.scalar_one_or_none()
        assert fetched is not None
        assert fetched.accion == "AJUSTAR"
        assert fetched.empresa_id == empresa.id
        assert fetched.payload == {"antes": 10.0, "despues": 8.0}
