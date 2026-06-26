## 1. Backend: Auditoría — Modelos y Base de Datos

- [x] 1.1 Crear modelo SQLModel `Auditoria` con campos: `id`, `empresa_id`, `usuario_id`, `accion`, `entidad_tipo`, `entidad_id`, `payload` (JSON), `fecha`, `hora`, `created_at`
- [x] 1.2 Generar migración Alembic para tabla `auditoria` con índices en `empresa_id`, `fecha`, `usuario_id`, `accion`, `entidad_tipo`
- [x] 1.3 Activar RLS en tabla `auditoria` con políticas que filtren por `empresa_id`
- [x] 1.4 Escribir test de modelo: inserción válida y campos obligatorios

## 2. Backend: Auditoría — Servicio y Middleware

- [x] 2.1 Crear `AuditoriaService` con método `registrar(db, usuario_id, empresa_id, accion, entidad_tipo, entidad_id, payload)`
- [x] 2.2 Implementar middleware FastAPI que capture requests mutantes (POST, PUT, PATCH, DELETE) y llame a `AuditoriaService.registrar()` con snapshot del request/response
- [x] 2.3 Agregar hooks explícitos en servicios de negocio (ventas, stock, caja, etc.) para registrar eventos internos no capturados por middleware
- [x] 2.4 Escribir tests de servicio: registro exitoso, payload correcto, inmutabilidad (intento de update/delete debe fallar)

## 3. Backend: Auditoría — Router y Permisos

- [x] 3.1 Crear router `GET /auditoria` con filtros query: `usuario_id`, `fecha_desde`, `fecha_hasta`, `accion`, `entidad_tipo`, paginación con `limit`/`offset`
- [x] 3.2 Proteger endpoint con dependencia `require_admin`
- [x] 3.3 Validar que `empresa_id` del JWT se inyecte en todas las queries
- [x] 3.4 Escribir tests de integración: consulta con filtros, acceso denegado para no-admin, aislamiento multi-tenant

## 4. Backend: Notificaciones — Modelos y Base de Datos

- [x] 4.1 Crear modelo SQLModel `Notificacion` con campos: `id`, `empresa_id`, `tipo` (enum), `mensaje`, `leida`, `fecha_lectura`, `entidad_tipo`, `entidad_id`, `created_at`
- [x] 4.2 Generar migración Alembic para tabla `notificacion` con índices en `empresa_id`, `tipo`, `leida`, `created_at`
- [x] 4.3 Activar RLS en tabla `notificacion` con políticas que filtren por `empresa_id`
- [x] 4.4 Escribir test de modelo: inserción válida, valores por defecto, campos obligatorios

## 5. Backend: Notificaciones — Servicio y Triggers

- [x] 5.1 Crear `NotificacionService` con métodos: `generar_stock_bajo(db, producto)`, `generar_stock_critico(db, producto)`, `generar_diferencia_caja(db, cierre)`, `generar_deuda_vencida(db, cuenta_corriente)`, `generar_gasto_elevado(db, gasto)`
- [x] 5.2 Integrar llamadas a `NotificacionService` en `StockService` (bajo/crítico), `CajaService` (diferencia), `CuentaCorrienteService` (vencida), `GastoService` (elevado)
- [x] 5.3 Implementar verificación de configuración por empresa (`dias_vencimiento`, `umbral_gasto`) antes de generar notificaciones placeholder
- [x] 5.4 Escribir tests de servicio: cada tipo de notificación se genera correctamente ante el evento de negocio correspondiente

## 6. Backend: Notificaciones — Router

- [x] 6.1 Crear router `GET /notificaciones` con filtro `leida` opcional, ordenado por `created_at DESC`, paginado
- [x] 6.2 Crear router `PATCH /notificaciones/{id}/leida` que actualice `leida = true` y `fecha_lectura = now()` solo para notificaciones del tenant del usuario
- [x] 6.3 Validar que `empresa_id` del JWT se inyecte en todas las queries
- [x] 6.4 Escribir tests de integración: listado filtrado, marcado como leída, 404 para notificación de otra empresa, aislamiento multi-tenant

## 7. Frontend: Panel de Notificaciones

- [x] 7.1 Crear store Zustand `useNotificacionStore` con estado de notificaciones, contador de no leídas, acciones `fetchNotificaciones`, `marcarLeida`
- [x] 7.2 Crear componente `NotificationBadge` en el header que muestre el contador de no leídas
- [x] 7.3 Crear componente `NotificationPanel` (lista desplegable) con scroll, marca de lectura individual, y tiempo relativo
- [x] 7.4 Integrar `NotificationPanel` en el layout principal y conectar con API

## 8. Frontend: Pantalla de Auditoría

- [x] 8.1 Crear ruta `/auditoria` protegida por rol `admin`
- [x] 8.2 Crear store Zustand `useAuditoriaStore` con filtros (usuario, fecha, acción, entidad) y paginación
- [x] 8.3 Crear componente `AuditoriaTable` con columnas: fecha, usuario, acción, entidad, payload comprimido/expansible
- [x] 8.4 Agregar filtros de búsqueda en la UI y botón de exportación a CSV/JSON

## 9. Testing E2E y Verificación

- [x] 9.1 Tests de componentes (reemplazo E2E Playwright — pendiente C futuro): flujo de notificación (badge + panel + marcar leída)
- [x] 9.2 Tests de componentes (reemplazo E2E Playwright — pendiente C futuro): pantalla de auditoría accesible solo por admin, filtros funcionan
- [x] 9.3 Ejecutar suite completa de backend (`pytest`) y asegurar que no hay regresiones en módulos previos
- [x] 9.4 Ejecutar suite de frontend (`vitest`) y verificar cobertura de nuevos componentes

## 10. Documentación y Cierre

- [x] 10.1 Actualizar `knowledge-base/05_reglas_de_negocio.md` con RN-AUD-01, RN-AUD-02, RN-NOTIF-01 a RN-NOTIF-05
- [x] 10.2 Actualizar `knowledge-base/06_funcionalidades.md` con historias de usuario de auditoría y notificaciones
- [x] 10.3 Actualizar `CHANGES.md` marcando C-20 como listo para apply
- [x] 10.4 Revisar `AGENTS.md` para confirmar que no hay reglas duras nuevas que agregar
