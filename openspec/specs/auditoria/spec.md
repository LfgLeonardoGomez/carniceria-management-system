# auditoria Specification

## Purpose
TBD - created by archiving change c-20-auditoria-notificaciones. Update Purpose after archive.
## Requirements
### Requirement: Registro inmutable de operaciones
El sistema SHALL registrar automáticamente cada operación relevante en la tabla `Auditoria` con los campos: `usuario_id`, `accion`, `entidad_tipo`, `entidad_id`, `payload` (snapshot JSON), `fecha`, `hora` y `empresa_id`.

#### Scenario: Registro de creación de venta
- **WHEN** un usuario autenticado crea una venta exitosamente
- **THEN** el sistema inserta un registro en `Auditoria` con `accion = 'CREAR'`, `entidad_tipo = 'venta'`, `entidad_id` igual al ID de la venta, y `payload` conteniendo el snapshot completo de la venta

#### Scenario: Registro de ajuste de stock
- **WHEN** un usuario autenticado realiza un ajuste de stock
- **THEN** el sistema inserta un registro en `Auditoria` con `accion = 'AJUSTAR'`, `entidad_tipo = 'stock'`, y `payload` con el estado antes y después del ajuste

### Requirement: Inmutabilidad de registros de auditoría
El sistema SHALL permitir únicamente inserciones en la tabla `Auditoria`. Ningún rol, incluido el administrador, SHALL poder actualizar o eliminar registros de auditoría.

#### Scenario: Intento de modificación de registro de auditoría
- **WHEN** cualquier usuario intenta ejecutar un UPDATE o DELETE sobre la tabla `Auditoria`
- **THEN** el sistema rechaza la operación y retorna un error 403 Forbidden

### Requirement: Consulta filtrada de auditoría para administradores
El sistema SHALL exponer el endpoint `GET /auditoria` que devuelva registros de auditoría paginados y permita filtrar por `usuario_id`, `fecha_desde`, `fecha_hasta`, `accion` y `entidad_tipo`. Solo usuarios con rol `admin` SHALL poder acceder.

#### Scenario: Administrador consulta auditoría con filtros
- **WHEN** un usuario con rol `admin` realiza `GET /auditoria?accion=CREAR&fecha_desde=2026-06-01`
- **THEN** el sistema retorna solo los registros de auditoría de su empresa que coincidan con los filtros, paginados

#### Scenario: Usuario no admin intenta consultar auditoría
- **WHEN** un usuario sin rol `admin` realiza `GET /auditoria`
- **THEN** el sistema retorna 403 Forbidden

### Requirement: Aislamiento multi-tenant en auditoría
El sistema SHALL garantizar que los registros de `Auditoria` de una empresa no sean visibles ni accesibles por usuarios de otra empresa.

#### Scenario: Consulta de auditoría cross-tenant
- **WHEN** un usuario autenticado de la empresa A consulta `GET /auditoria`
- **THEN** el sistema retorna únicamente registros donde `empresa_id` corresponde a la empresa A

