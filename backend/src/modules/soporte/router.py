from typing import Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.modules.auth.dependencies import require_auth
from src.modules.auth.models import Usuario
from src.common.rbac import require_role
from src.modules.soporte import service as soporte_service

router = APIRouter()


class ImpersonateRequest(BaseModel):
    empresa_id: str

    model_config = ConfigDict(extra="forbid")


class ImpersonateResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(extra="forbid")


@router.post(
    "/impersonate",
    response_model=ImpersonateResponse,
    dependencies=[Depends(require_role("soporte:impersonate"))],
)
async def impersonate(
    request: Request,
    payload: ImpersonateRequest,
    db: AsyncSession = Depends(get_db),
) -> ImpersonateResponse:
    current_user: Usuario = request.state.current_user
    token = await soporte_service.impersonate_admin(
        db=db,
        superadmin_id=current_user.id,
        empresa_id=payload.empresa_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return ImpersonateResponse(access_token=token)


@router.post(
    "/exit-impersonate",
    dependencies=[Depends(require_auth)],
)
async def exit_impersonate(
    request: Request,
) -> dict:
    """Endpoint de conveniencia para que el frontend notifique salida de impersonación.

    El frontend debe limpiar el token de impersonación y redirigir.
    Este endpoint solo confirma que la sesión original sigue válida.
    """
    return {"message": "Exit impersonate acknowledged. Redirect to superadmin panel."}
