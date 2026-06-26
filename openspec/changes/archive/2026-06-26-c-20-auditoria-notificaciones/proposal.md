## Why

BASILE necesita trazabilidad completa de operaciones críticas y alertas proactivas para que los administradores detecten problemas antes de que escalen. Sin auditoría no hay cumplimiento ni debugging de incidentes; sin notificaciones el negocio opera a ciegas sobre stock crítico, deudas vencidas y diferencias de caja. Este change cierra el MVP con visibilidad y gobernanza.

## What Changes

- **Auditoría (nuevo módulo)**
  - Tabla `Auditoria` con snapshot JSON inmutable de cada operación relevante.
  - Middleware/interceptor global que captura automáticamente: usuario, acción, entidad, payload y timestamp.
  - Endpoint `GET /auditoria` con filtros (usuario, fecha, tipo de acción). Solo admin.
  - Pantalla frontend de auditoría con filtros y exportación.
  - Reglas duras: registros insert-only, nunca update ni delete (RN-AUD-02).

- **Notificaciones (nuevo módulo)**
  - Tabla `Notificacion` con tipos: `stock_bajo`, `stock_critico`, `deuda_vencida`, `gasto_elevado`, `diferencia_caja`.
  - Generación automática de notificaciones desde eventos de negocio existentes:
    - Stock bajo/crítico: disparado desde el módulo de stock cuando `stock_actual <= stock_minimo`.
    - Diferencia de caja: disparado desde el cierre de caja cuando `diferencia_total != 0`.
    - Deuda vencida: placeholder (requiere definición de días de vencimiento).
    - Gasto elevado: placeholder (requiere umbral configurable).
  - Panel frontend de notificaciones (badge, toast, marcar como leída).
  - Endpoint `GET /notificaciones` propio del usuario autenticado; `PATCH /notificaciones/{id}/leida`.

- **Tests obligatorios (TDD)**
  - Inmutabilidad de registros de auditoría.
  - Generación de notificaciones ante eventos de negocio.
  - Marcado de lectura y permisos de admin.
  - Aislamiento multi-tenant en ambos módulos.

## Capabilities

### New Capabilities
- `auditoria`: Sistema de registro inmutable de operaciones críticas con consulta filtrada para administradores.
- `notificaciones`: Sistema de alertas automáticas y panel de notificaciones para usuarios.

### Modified Capabilities
<!-- Los triggers de notificación se implementan como hooks en los módulos existentes sin cambiar sus specs de comportamiento. No se requieren delta specs. -->

## Impact

- **Backend**: nuevos routers `/auditoria`, `/notificaciones`; modelos `Auditoria`, `Notificacion`; middleware de auditoría; servicios de generación de notificaciones.
- **Frontend**: nueva pantalla de auditoría; componente de panel/badget de notificaciones; integración con API de lectura.
- **DB**: nuevas tablas con índices en `empresa_id`, `fecha`, `usuario_id`, `tipo`; RLS activo en ambas.
- **Dependencias**: todos los módulos de negocio previos (ventas, stock, caja, etc.) deben disparar eventos para auditoría y notificaciones.
