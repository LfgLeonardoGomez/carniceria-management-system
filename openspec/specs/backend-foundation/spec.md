# backend-foundation Specification

## Purpose
TBD - created by archiving change c-01-foundation-setup. Update Purpose after archive.
## Requirements
### Requirement: FastAPI scaffolding con estructura por dominios
El sistema SHALL proveer un proyecto FastAPI 0.100+ con estructura de directorios por dominio, inyección de dependencias y Pydantic strict.

#### Scenario: Estructura de directorios válida
- **WHEN** se inspecciona el directorio `backend/src/`
- **THEN** existe `modules/` con subdirectorios por dominio: `auth/`, `empresa/`, `usuario/`, `producto/`, `cliente/`, `proveedor/`, `compra/`, `desposte/`, `stock/`, `venta/`, `caja/`, `gasto/`, `cuenta-corriente/`, `reporte/`, `auditoria/`, `notificacion/`
- **AND** cada dominio tiene al menos `router.py` (o `routes.py`) y `models.py`
- **AND** existe `common/` para utils, excepciones e interceptores
- **AND** existe `config/` para settings y conexión a DB
- **AND** existe `database/` para migrations y seeds

### Requirement: Async endpoints sin bloquear el event loop
El sistema SHALL usar `async/await` en todos los endpoints I/O-bound y NUNCA bloquear el event loop.

#### Scenario: Endpoint de health check es async
- **WHEN** se inspecciona el código del endpoint `/health`
- **THEN** la función está declarada con `async def`
- **AND** no contiene llamadas síncronas a DB, filesystem ni librerías bloqueantes

### Requirement: Pydantic BaseModel con extra=forbid
El sistema SHALL usar Pydantic `BaseModel` para todos los request/response bodies con `extra='forbid'`.

#### Scenario: Request con campo extra es rechazado
- **WHEN** se envía un POST a cualquier endpoint con un campo no definido en el schema Pydantic
- **THEN** el backend responde con HTTP 422 y un mensaje de error claro indicando campo inesperado

### Requirement: Inyección de dependencias estándar
El sistema SHALL inyectar `db: AsyncSession`, `current_user` y `tenant` (empresa_id) como dependencias en cada router.

#### Scenario: Router requiere db y current_user
- **WHEN** se inspecciona cualquier router de negocio
- **THEN** recibe `db: AsyncSession = Depends(get_db)` (o equivalente)
- **AND** tiene mecanismo preparado para recibir `current_user` y `empresa_id` como dependencias

