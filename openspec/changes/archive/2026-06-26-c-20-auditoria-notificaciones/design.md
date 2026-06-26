## Context

BASILE es un SaaS multi-tenant para gestión de carnicerías. Todos los changes anteriores (C-01 a C-19) están implementados y archivados. Las entidades de negocio existen: Venta, Producto, Stock, Caja, CuentaCorriente, Gasto, Cliente. El proyecto usa FastAPI con SQLModel/SQLAlchemy 2.0 async, PostgreSQL con RLS, React 18+ SPA, Zustand, JWT con tenant en subclaim, y TDD obligatorio.

Actualmente existen los directorios `backend/src/modules/auditoria/` y `notificacion/` con routers de 3 líneas y modelos TODO. Este change completa ambos módulos como cierre del MVP.

## Goals / Non-Goals

**Goals:**
- Registrar automáticamente cada operación relevante del sistema de forma inmutable (auditoría).
- Generar alertas automáticas ante condiciones de negocio críticas (stock bajo/crítico, diferencia de caja, deuda vencida, gasto elevado).
- Proveer endpoints y pantallas para consultar auditoría (admin) y notificaciones (usuarios).
- Garantizar aislamiento multi-tenant y cumplimiento de reglas de negocio codificadas.

**Non-Goals:**
- Dashboards analíticos avanzados sobre auditoría (solo listado filtrado y exportación básica).
- Notificaciones push o email (solo in-app).
- Definición final de días de vencimiento para deuda ni umbral para gasto elevado (se dejan como placeholders configurables).
- Modificar specs de los módulos existentes; solo se agregan hooks de eventos.

## Decisions

1. **Middleware vs Decorator para auditoría**
   - Elegido: Middleware global en FastAPI (`app.middleware`) + servicio explícito `AuditoriaService.registrar()` para acciones críticas que no pasan por HTTP (jobs, triggers internos).
   - Rationale: El middleware captura automáticamente requests relevantes sin modificar cada endpoint. El servicio permite registrar eventos internos (por ejemplo, ajustes de stock manuales).
   - Alternativa: Decorator `@audit` en cada endpoint → rechazado porque es propenso a olvidos y ensucia el código de negocio.

2. **Modelo de datos: snapshot JSON en auditoría**
   - Elegido: Campo `payload` de tipo JSONB con el snapshot completo de la entidad afectada.
   - Rationale: Permite reconstruir el estado histórico sin joins complejos. Inmutable por definición.
   - Alternativa: Tabla de versionado por campo → rechazado por complejidad innecesaria para MVP.

3. **Trigger síncrono en el mismo request para notificaciones**
   - Elegido: Llamada explícita a `NotificacionService.generar()` desde los servicios de negocio (stock, caja) dentro de la misma transacción.
   - Rationale: Garantiza consistencia ACID (si el evento de negocio se confirma, la notificación también). Para el MVP no se justifica un bus de eventos asíncrono.
   - Alternativa: Celery/background task → rechazado porque agrega infraestructura y complejidad fuera del scope del MVP.

4. **RLS en tablas de auditoría y notificaciones**
   - Elegido: Activar RLS en ambas tablas con políticas que filtran por `empresa_id`.
   - Rationale: Cumple con el aislamiento estricto multi-tenant del proyecto. Las queries del backend NUNCA omiten `empresa_id`, pero RLS es la capa de seguridad adicional obligatoria.

5. **Frontend: panel de notificaciones como componente global**
   - Elegido: Componente `NotificationPanel` montado en el layout principal, con badge en el header y lista desplegable.
   - Rationale: Acceso inmediato desde cualquier pantalla. Zustand para el estado global de notificaciones no leídas.
   - Alternativa: Pantalla separada de notificaciones → rechazado porque reduce la visibilidad inmediata.

## Risks / Trade-offs

- **[Risk] Payload JSON de auditoría puede crecer mucho** → Mitigación: no almacenar payloads de lecturas masivas (solo mutaciones). En futuras versiones evaluar TTL o compresión.
- **[Risk] Generación síncrona de notificaciones ralentiza operaciones de stock/caja** → Mitigación: las inserciones son simples (1 fila) y el índice está optimizado. Monitorear tiempos de respuesta; si hay problemas, migrar a background jobs post-MVP.
- **[Risk] Lógica de placeholders (deuda vencida, gasto elevado) queda incompleta** → Mitigación: se implementan con flags de configuración por empresa (`dias_vencimiento`, `umbral_gasto`). Si no están definidas, los triggers no se ejecutan. Documentar en KB que requieren definición posterior.
- **[Trade-off] No hay soft-delete en notificaciones** → Se permite `DELETE` solo para limpieza de notificaciones leídas por el propio usuario, pero se audita el evento. Esto respeta RN-GLOBAL-01 para historia financiera, pero notificaciones no son historia financiera.
