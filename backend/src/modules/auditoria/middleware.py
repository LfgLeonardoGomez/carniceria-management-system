"""Middleware global de auditoría.

Captura automáticamente requests HTTP mutantes (POST, PUT, PATCH, DELETE)
exitosos (status 2xx) y crea un registro en la tabla `auditoria` con un
snapshot del request y la response. Las operaciones internas (jobs,
triggers de negocio) deben llamar directamente a `service.registrar()`.

Reglas que aplica:
- Solo métodos mutantes: POST, PUT, PATCH, DELETE.
- Solo respuestas 2xx: 4xx y 5xx no se registran.
- Skip de paths ruidosos: `/auditoria` (recursión), `/health`, `/docs`,
  `/redoc`, `/openapi.json`.
- `usuario_id` se extrae del JWT (claim `sub`) cuando hay Authorization.
- `empresa_id` se extrae del JWT (claim `empresa_id`).
- El body del request se trunca a 4 KB para evitar payloads enormes.
- Errores al persistir la auditoría NO rompen el request original.
"""

import json
import logging
import time
import uuid
from typing import Callable, Optional

import jwt
from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.config.database import AsyncSessionLocal
from src.config.settings import settings
from src.core.security import ALGORITHM
from src.modules.auditoria.service import registrar

logger = logging.getLogger("basile.api.audit")

# Llave de ``app.state`` donde el conftest de tests puede registrar un
# factory de sesiones (async_sessionmaker) que use la conexión compartida
# de testcontainers. En producción nunca se setea y se usa AsyncSessionLocal.
AUDIT_SESSION_FACTORY_KEY = "audit_session_factory"

# Tipo del factory: callable que devuelve una AsyncSession (context manager).
AuditSessionFactory = Callable[[], AsyncSession]

MUTANT_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Prefijos de path que el middleware debe ignorar (recursión / ruido).
SKIP_PREFIXES = (
    "/auditoria",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
)

# Tamaño máximo del body que se persiste en el payload (en bytes).
MAX_BODY_BYTES = 4096

# Mapa método HTTP -> acción legible para auditoría.
ACCION_POR_METODO = {
    "POST": "CREAR",
    "PUT": "ACTUALIZAR",
    "PATCH": "ACTUALIZAR",
    "DELETE": "ELIMINAR",
}


def _decode_jwt_claims(request: Request) -> tuple[Optional[uuid.UUID], Optional[uuid.UUID]]:
    """Devuelve (user_id, empresa_id) decodificando el JWT, o (None, None)."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None, None
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except Exception:
        return None, None
    user_id_raw = payload.get("sub")
    empresa_id_raw = payload.get("empresa_id")
    try:
        user_id = uuid.UUID(user_id_raw) if user_id_raw else None
    except (ValueError, TypeError):
        user_id = None
    try:
        empresa_id = uuid.UUID(empresa_id_raw) if empresa_id_raw else None
    except (ValueError, TypeError):
        empresa_id = None
    return user_id, empresa_id


def _debe_saltarse(path: str, method: str) -> bool:
    """True si la request no debe procesarse por el middleware."""
    if method not in MUTANT_METHODS:
        return True
    for prefix in SKIP_PREFIXES:
        if path == prefix or path.startswith(prefix + "/"):
            return True
    return False


def _parsear_entidad(path: str) -> tuple[Optional[str], Optional[uuid.UUID]]:
    """Extrae (entidad_tipo, entidad_id) del path. Ej: /producto/<uuid>.

    Devuelve (None, None) si el path no tiene la forma esperada.
    """
    parts = [p for p in path.split("/") if p]
    if not parts:
        return None, None
    tipo = parts[0]
    entidad_id: Optional[uuid.UUID] = None
    if len(parts) >= 2:
        try:
            entidad_id = uuid.UUID(parts[1])
        except (ValueError, TypeError):
            entidad_id = None
    return tipo, entidad_id


def _truncar_body(body: bytes) -> str:
    """Convierte el body a string truncado a MAX_BODY_BYTES."""
    if not body:
        return ""
    truncado = body[:MAX_BODY_BYTES]
    try:
        texto = truncado.decode("utf-8")
    except UnicodeDecodeError:
        texto = truncado.decode("utf-8", errors="replace")
    if len(body) > MAX_BODY_BYTES:
        texto += "...[truncado]"
    return texto


async def audit_middleware(request: Request, call_next):
    """Middleware FastAPI de auditoría.

    Debe montarse vía `@app.middleware("http")` en `main.py`. Se ejecuta
    antes que los routers, así que la lectura del body se hace ANTES de
    `call_next` para no romper el parseo que hace FastAPI del request.
    """
    method = request.method
    path = request.url.path

    if _debe_saltarse(path, method):
        return await call_next(request)

    # Leemos el body antes de que FastAPI lo consuma.
    # Starlette cachea el resultado, así que el endpoint puede releerlo.
    try:
        body_bytes = await request.body()
    except Exception:
        body_bytes = b""

    start = time.perf_counter()
    response: Response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    # Solo registramos respuestas exitosas (2xx).
    if response.status_code < 200 or response.status_code >= 300:
        return response

    user_id, empresa_id = _decode_jwt_claims(request)
    # Sin empresa no podemos asociar la auditoría a un tenant.
    if empresa_id is None:
        return response

    entidad_tipo, entidad_id = _parsear_entidad(path)
    accion = ACCION_POR_METODO.get(method, method)

    payload = {
        "method": method,
        "path": path,
        "query": dict(request.query_params),
        "body": _truncar_body(body_bytes),
        "status": response.status_code,
        "duration_ms": duration_ms,
    }

    try:
        factory: Optional[async_sessionmaker] = getattr(
            request.app.state, AUDIT_SESSION_FACTORY_KEY, None
        )
        session_ctx = factory() if factory is not None else AsyncSessionLocal()
        async with session_ctx as session:
            await registrar(
                db=session,
                empresa_id=empresa_id,
                usuario_id=user_id,
                accion=accion,
                entidad_tipo=entidad_tipo or "desconocido",
                entidad_id=entidad_id,
                payload=payload,
            )
    except Exception as exc:  # noqa: BLE001
        # La auditoría nunca debe romper el request del usuario.
        logger.warning("No se pudo registrar auditoría para %s %s: %s", method, path, exc)

    return response
