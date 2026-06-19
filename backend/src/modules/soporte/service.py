import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.empresa.models import Empresa
from src.modules.auditoria.models import Auditoria
from src.core.security import create_access_token
from src.common.exceptions import NotFoundException


async def impersonate_admin(
    db: AsyncSession,
    superadmin_id: uuid.UUID,
    empresa_id: uuid.UUID,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> str:
    """Genera un JWT temporal de impersonación para un superadmin.

    - El JWT tiene rol='admin', empresa_id=<target>, original_role='superadmin'
    - Duración: 15 minutos
    - No genera refresh token
    - Registra auditoría
    """
    # Verificar que la empresa existe
    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise NotFoundException("Empresa no encontrada")

    token_data = {
        "sub": str(superadmin_id),
        "empresa_id": str(empresa_id),
        "rol": "admin",
        "original_role": "superadmin",
    }
    access_token = create_access_token(token_data, expires_delta=timedelta(minutes=15))

    # Registrar auditoría
    auditoria = Auditoria(
        action="IMPERSONATE_ADMIN",
        actor_id=superadmin_id,
        target_empresa_id=empresa_id,
        details=f"Impersonación como admin de empresa {empresa_id}",
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(auditoria)
    await db.commit()

    return access_token
