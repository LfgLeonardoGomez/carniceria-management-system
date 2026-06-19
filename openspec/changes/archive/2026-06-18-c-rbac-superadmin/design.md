## Context

El sistema BASILE es un SaaS multi-tenant para carnicerías. Actualmente el RBAC tiene 4 roles y el rol `Administrador` posee wildcard `*`, lo que le permite cualquier operación. No existe un rol por encima del tenant.

Esto impide que el dueño del SaaS (superadmin) cree empresas, asigne administradores a tenants, o ingrese a una empresa para soporte técnico sin tener un usuario dentro de cada tenant.

El código actual tiene:
- `backend/src/common/rbac.py` con `PERMISSION_MATRIX` de 4 roles.
- `backend/src/modules/auth/dependencies.py` con `get_current_user` y `require_admin`.
- `backend/src/modules/usuario/service.py` con `crear_usuario` que asigna automáticamente `empresa_id = current_user.empresa_id`.
- Frontend con `AdminRoute` que chequea `rol === 'Administrador'`.

## Goals / Non-Goals

**Goals:**
- Separar claramente `superadmin` (global, sin `empresa_id`) de `admin` (tenant-scoped).
- Eliminar wildcard `*` del rol `admin` y asignarle permisos explícitos de tenant.
- Permitir que `superadmin` cree empresas, cree admins, e ingrese a cualquier empresa mediante impersonación auditada.
- Proteger la creación de usuarios: `admin` solo crea roles operativos dentro de su tenant; `superadmin` solo crea `admin`.
- Frontend: panel de superadmin y route guards que reconozcan `superadmin`.

**Non-Goals:**
- No se modifica el flujo de login (solo se adapta para aceptar JWT sin `empresa_id`).
- No se implementa registro público (sigue siendo prohibido).
- No se modifica la lógica de negocio de ventas, stock, caja, desposte (solo se asegura que usen `require_role` correctamente).

## Decisions

### 1. Mantener nombres de roles en español y minúsculas en código
**Decision**: Los roles en la matriz RBAC se renombran a minúsculas y sin tildes: `superadmin`, `admin`, `encargado`, `cajero`, `vendedor`. Los nombres en DB seed se actualizan acorde.
**Rationale**: Consistencia con la base de conocimiento (`03_actores_y_roles.md`) y evita problemas de casing. El campo `rol.nombre` en DB ya es string, no hay migración de tipo.
**Alternativa**: Mantener `Administrador` → Rechazada porque genera inconsistencia con los nuevos roles.

### 2. `empresa_id = NULL` en DB para superadmin
**Decision**: El usuario `superadmin` tiene `empresa_id = NULL` en la tabla `usuario`. `get_current_user` lo carga normalmente; `require_auth` no establece `request.state.empresa_id` cuando es `NULL`.
**Rationale**: Es la forma más simple de representar scope global en un modelo relacional. No requiere tablas adicionales.
**Alternativa**: Tabla `superadmin` separada → Rechazada porque complica las relaciones y el login unificado.

### 3. Permisos explícitos en `admin`, sin wildcard
**Decision**: El `PERMISSION_MATRIX` para `admin` contiene solo los permisos que necesita un admin de carnicería (CRUD de usuarios de su empresa, productos, clientes, proveedores, compras, desposte, stock, ventas, caja, gastos, cuenta-corriente, reportes, auditoría de su empresa). `superadmin` tiene permisos globales explícitos.
**Rationale**: Principio de menor privilegio. El wildcard `*` era un riesgo de seguridad.
**Alternativa**: Dejar `*` y filtrar en servicio → Rechazada porque la matriz RBAC debe ser la fuente de verdad; el servicio no debe compensar una matriz permisiva.

### 4. Impersonación via JWT temporal con claim `original_role`
**Decision**: El endpoint `POST /soporte/impersonate` genera un access token JWT estándar con `rol = "admin"`, `empresa_id = <target>`, y un claim adicional `original_role = "superadmin"`. El refresh token no se renueva.
**Rationale**: El frontend existente ya entiende JWT con `empresa_id` y `rol = admin`. Agregar `original_role` permite al frontend saber que está en modo impersonación y ofrecer un botón "Salir".
**Alternativa**: Session-sidecar con estado en Redis → Rechazada por simplicidad; no se quiere infraestructura adicional.

### 5. Auditoría de impersonación en tabla `Auditoria`
**Decision**: Cada llamada a `impersonate` inserta un registro en `Auditoria` con `action = "IMPERSONATE_ADMIN"`, `actor_id = superadmin.id`, `target_empresa_id = empresa_id`, `details = {"ip": ..., "user_agent": ...}`.
**Rationale**: Es un evento de seguridad crítico; debe quedar trazado.
**Alternativa**: Log de aplicación → Rechazada porque los logs rotan; la tabla `Auditoria` es permanente.

### 6. `admin_id` FK en `empresa` (nullable)
**Decision**: Se agrega `empresa.admin_id` como FK a `usuario.id` (nullable). Se establece al crear la empresa o al asignar admin posteriormente.
**Rationale**: Permite al superadmin ver qué admin tiene asignada cada empresa en el panel.
**Alternativa**: Query inversa `SELECT usuario WHERE rol = admin AND empresa_id = X` → Rechazada porque no garantiza unicidad y es más costosa.

### 7. Frontend: Zustand flag `isImpersonating`
**Decision**: `authStore` agrega `isImpersonating: boolean` y `originalRole: string | null`. Se setean cuando el JWT contiene `original_role = "superadmin"`.
**Rationale**: El frontend necesita saber si está en modo impersonación para mostrar un banner y el botón "Volver a superadmin".

## Risks / Trade-offs

- **[Risk]** Renombrar `Administrador` a `admin` en la matriz puede romper endpoints que hacen string-match directo en código (ej. `require_admin`).
  → **Mitigation**: Buscar y actualizar TODAS las referencias a `"Administrador"` en el backend y frontend antes de mergear.

- **[Risk]** `empresa_id = NULL` puede romper queries que asumen `empresa_id IS NOT NULL` (RLS, índices, joins).
  → **Mitigation**: Auditar todas las queries de negocio para soportar `NULL`. Activar RLS con política que permita `NULL` solo para `superadmin`.

- **[Risk]** El JWT de impersonación tiene la misma firma y estructura que un JWT normal. Si un atacante roba el JWT de impersonación, puede actuar como admin de ese tenant.
  → **Mitigation**: Duración corta (15 min). El endpoint no genera refresh token. Se audita cada generación.

- **[Risk]** Cambio breaking en la API: `POST /empresas` pasa de estar disponible para `admin` a solo `superadmin`.
  → **Mitigation**: Este es un cambio intencional y documentado. No hay clientes externos; el frontend se actualiza en el mismo change.

## Migration Plan

1. **DB Seed**: Agregar rol `superadmin` al seed. Modificar seed de empresa para que no cree un admin automáticamente (o que lo cree con superadmin).
2. **Backend RBAC**: Actualizar `rbac.py` y `dependencies.py`.
3. **Backend Services**: Actualizar `UsuarioService` y `EmpresaService`.
4. **Backend Impersonación**: Crear módulo `soporte`.
5. **Frontend**: Actualizar route guards, auth store, crear páginas.
6. **Tests**: Correr suite completa de integración.

Rollback: Revertir commits. No hay migración de datos destructiva (el campo `admin_id` es nullable; los roles existentes no se borran).

## Open Questions

- ¿Se quiere que el superadmin pueda desactivar/reactivar admins de cualquier empresa? (Se asume SÍ, dado que tiene `usuarios:update` y `usuarios:delete` globales.)
- ¿Se necesita un endpoint `GET /soporte/auditoria` para que superadmin vea logs de impersonación? (Fuera de scope por ahora; se puede agregar en C-20.)
