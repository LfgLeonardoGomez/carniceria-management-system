import logging
import time

from pathlib import Path

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from src.config.settings import settings
from src.common.logging import setup_logging
from src.common.exceptions import add_exception_handlers

# Setup structured logging
setup_logging()
logger = logging.getLogger("basile.api")

app = FastAPI(
    title="BASILE API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Security headers middleware
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response: Response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)
    logger.info(
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(settings.cors_origin)],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
add_exception_handlers(app)

# Static files for uploads (logos, etc.)
_upload_dir = Path(settings.upload_path)
_upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_upload_dir, check_dir=False), name="uploads")

# Rate limiting for /auth/* endpoints (5 intentos / 60s por IP+email)
# Implemented via src.common.rate_limit dependency in auth router

from src.modules.auth.router import router as auth_router
from src.modules.auth.dependencies import require_auth

app.include_router(auth_router, prefix="/auth", tags=["auth"])

# Domain routers — all protected except auth public endpoints and health
from src.modules.empresa.router import router as empresa_router
from src.modules.usuario.router import router as usuario_router
from src.modules.cliente.router import router as cliente_router
from src.modules.proveedor.router import router as proveedor_router
from src.modules.compra.router import router as compra_router
from src.modules.stock.router import router as stock_router
from src.modules.venta.router import router as venta_router
from src.modules.caja.router import router as caja_router
from src.modules.desposte.router import router as desposte_router
from src.modules.producto.router import router as producto_router
from src.modules.cuenta_corriente.router import router as cuenta_corriente_router
from src.modules.reporte.router import router as reporte_router
from src.modules.auditoria.router import router as auditoria_router
from src.modules.notificacion.router import router as notificacion_router
from src.modules.gasto.router import router as gasto_router
from src.modules.soporte.router import router as soporte_router
from src.modules.dashboard.router import router as dashboard_router

auth_dep = [Depends(require_auth)]

app.include_router(empresa_router, prefix="/empresas", tags=["empresa"], dependencies=auth_dep)
app.include_router(usuario_router, prefix="/usuarios", tags=["usuarios"], dependencies=auth_dep)
app.include_router(cliente_router, prefix="/cliente", tags=["cliente"], dependencies=auth_dep)
app.include_router(proveedor_router, prefix="/proveedores", tags=["proveedor"], dependencies=auth_dep)
app.include_router(compra_router, prefix="/compra", tags=["compra"], dependencies=auth_dep)
app.include_router(stock_router, prefix="/stock", tags=["stock"], dependencies=auth_dep)
app.include_router(venta_router, prefix="/venta", tags=["venta"], dependencies=auth_dep)
app.include_router(caja_router, prefix="/caja", tags=["caja"], dependencies=auth_dep)
app.include_router(desposte_router, prefix="/desposte", tags=["desposte"], dependencies=auth_dep)
app.include_router(producto_router, prefix="/producto", tags=["producto"], dependencies=auth_dep)
app.include_router(cuenta_corriente_router, prefix="/cuenta-corriente", tags=["cuenta-corriente"], dependencies=auth_dep)
app.include_router(reporte_router, prefix="/reporte", tags=["reporte"], dependencies=auth_dep)
app.include_router(auditoria_router, prefix="/auditoria", tags=["auditoria"], dependencies=auth_dep)
app.include_router(notificacion_router, prefix="/notificacion", tags=["notificacion"], dependencies=auth_dep)
app.include_router(gasto_router, prefix="/gasto", tags=["gasto"], dependencies=auth_dep)
app.include_router(soporte_router, prefix="/soporte", tags=["soporte"], dependencies=auth_dep)
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"], dependencies=auth_dep)

# Health router (included early for monitoring) — public
from src.modules.health.router import router as health_router

app.include_router(health_router, prefix="/health", tags=["health"])
