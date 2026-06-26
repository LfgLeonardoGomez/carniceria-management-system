import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.notificacion.models import Notificacion
from src.modules.empresa.models import Empresa


class TestNotificacionModel:
    """TASK-4.4: Tests para modelo Notificacion."""

    def test_notificacion_columns_exist(self):
        cols = {c.name for c in Notificacion.__table__.columns}
        required = {
            "id", "empresa_id", "tipo", "mensaje", "leida",
            "fecha_lectura", "entidad_tipo", "entidad_id", "created_at",
        }
        assert required.issubset(cols), f"Notificacion falta columnas: {required - cols}"

    def test_notificacion_leida_default(self):
        col = Notificacion.__table__.columns["leida"]
        assert col.default is not None or col.server_default is not None, \
            "leida debe tener default=False"

    def test_notificacion_instance_creation(self):
        notif = Notificacion(
            empresa_id=uuid.uuid4(),
            tipo="stock_bajo",
            mensaje="Stock bajo para producto X",
            entidad_tipo="producto",
            entidad_id=uuid.uuid4(),
        )
        assert notif.tipo == "stock_bajo"
        assert notif.leida is False
        assert notif.fecha_lectura is None

    @pytest.mark.asyncio
    async def test_notificacion_insert_and_query(self, db_session: AsyncSession):
        empresa = Empresa(nombre_comercial="Test Empresa Notif")
        db_session.add(empresa)
        await db_session.commit()
        await db_session.refresh(empresa)

        notif = Notificacion(
            empresa_id=empresa.id,
            tipo="diferencia_caja",
            mensaje="Diferencia de caja detectada",
            entidad_tipo="caja",
            entidad_id=uuid.uuid4(),
        )
        db_session.add(notif)
        await db_session.commit()
        await db_session.refresh(notif)

        result = await db_session.execute(
            select(Notificacion).where(Notificacion.id == notif.id)
        )
        fetched = result.scalar_one_or_none()
        assert fetched is not None
        assert fetched.tipo == "diferencia_caja"
        assert fetched.leida is False
        assert fetched.empresa_id == empresa.id
