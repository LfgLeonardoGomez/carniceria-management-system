## 1. Schema y Seed Data

- [x] 1.1 Verificar/actualizar modelo SQLModel de `Usuario`: asegurar FK `rol_id` con índice, índice compuesto `(empresa_id, activo)`.
- [x] 1.2 Actualizar seed data: crear usuario Administrador por defecto asociado a la empresa seed (idempotente, email/contraseña configurable por env var).
- [x] 1.3 Ejecutar migración Alembic si hay cambios de schema.

## 2. RBAC Core (Backend)

- [x] 2.1 Crear módulo `backend/src/common/rbac.py` con la matriz de permisos inmutable (dict) mapeando los 4 roles a recursos/operaciones.
- [x] 2.2 Implementar dependency `require_role(permiso: str)` que lee `request.state.current_user.rol`, consulta la matriz y lanza 403 si no tiene permiso.
- [x] 2.3 Extender `get_current_user` (C-02) para cargar el objeto `Rol` completo y exponer `request.state.current_user.rol`.
- [x] 2.4 Agregar claim `rol` al JWT access token (revisar generación de token en C-02).
- [x] 2.5 Tests unitarios para `require_role` y la matriz RBAC.

## 3. Servicio de Usuarios (Backend)

- [x] 3.1 Crear módulo `backend/src/modules/usuario/` con `service.py`.
- [x] 3.2 Implementar `crear_usuario`: validar email único global, generar contraseña temporal, hashear con bcrypt, asociar `empresa_id` del admin creador.
- [x] 3.3 Implementar `listar_usuarios`: filtrar por `empresa_id` + paginación (`skip`/`limit`) + filtro `activo`.
- [x] 3.4 Implementar `actualizar_usuario`: permitir cambio de nombre, apellido, email (validar unicidad), rol.
- [x] 3.5 Implementar regla de negocio "protección del último admin": antes de desactivar o cambiar rol de un admin, verificar que quede al menos 1 admin activo en la empresa → 409 si viola.
- [x] 3.6 Implementar `desactivar_usuario` (soft-delete: `activo = false`) y `reactivar_usuario` (`activo = true`), ambos con la misma protección del último admin.
- [x] 3.7 Implementar `obtener_perfil_propio` y `actualizar_perfil_propio`: solo nombre, apellido, email (ignorar rol_id si viene en el body).
- [x] 3.8 Tests de integración del servicio (pytest + testcontainers PostgreSQL).

## 4. Router y Schemas de Usuarios (Backend)

- [x] 4.1 Crear schemas Pydantic: `UsuarioCreate`, `UsuarioUpdate`, `UsuarioPublic`, `UsuarioListResponse`, `PerfilUpdate`, `PerfilPublic`, `ContrasenaTemporalResponse`.
- [x] 4.2 Implementar router `backend/src/modules/usuario/router.py` con endpoints:
  - `POST /usuarios` (admin only, dependency `require_role("usuarios:create")`)
  - `GET /usuarios` (admin only, dependency `require_role("usuarios:read")`)
  - `PUT /usuarios/{id}` (admin only, dependency `require_role("usuarios:update")`)
  - `PATCH /usuarios/{id}/desactivar` (admin only)
  - `PATCH /usuarios/{id}/reactivar` (admin only)
  - `GET /usuarios/me` (cualquier usuario autenticado)
  - `PUT /usuarios/me` (cualquier usuario autenticado)
- [x] 4.3 Asegurar `extra='forbid'` en todos los schemas.
- [x] 4.4 Incluir router en `main.py` con prefijo `/usuarios`.

## 5. Integración con Auth y Seguridad Existente

- [x] 5.1 Aplicar `require_role("empresas:admin")` a endpoints de `/empresas` (C-03) para que solo Administrador pueda gestionar empresa.
- [x] 5.2 Verificar que el middleware de auth (C-02) siga inyectando `empresa_id` correctamente en requests a `/usuarios`.
- [x] 5.3 Rate limiting: aplicar limitación de 10 req/min a endpoints de creación de usuario (mitigar spam de alta).

## 6. Tests de Integración y E2E

- [x] 6.1 Test: login de usuario desactivado → 403.
- [x] 6.2 Test: CRUD de usuarios con admin → 200/201; con encargado/cajero/vendedor → 403.
- [x] 6.3 Test: protección del último admin → 409 al intentar desactivar/ cambiar rol del único admin.
- [x] 6.4 Test: aislamiento multi-tenant: admin de empresa A no lista usuarios de empresa B.
- [x] 6.5 Test: email duplicado global → 409.
- [x] 6.6 Test: `/usuarios/me` accesible por todos los roles; `/usuarios` solo por admin.
- [x] 6.7 Test: seed data crea admin por defecto y es idempotente.
- [x] 6.8 Coverage mínimo 90% del módulo `app/modules/usuario`.

## 7. Frontend

- [x] 7.1 Crear Zustand store `usuarioStore` con estado de listado de usuarios y perfil propio.
- [x] 7.2 Implementar página `/usuarios` con grid de usuarios (nombre, email, rol, estado), filtros por activo/inactivo y paginación.
- [x] 7.3 Implementar modal/formulario de alta de usuario: nombre, apellido, email, selector de rol. Mostrar contraseña temporal en toast/modal de éxito (una sola vez).
- [x] 7.4 Implementar modal de edición de usuario (cambio de rol, reactivación).
- [x] 7.5 Implementar diálogo de confirmación para desactivar usuario, con advertencia si es el último admin.
- [x] 7.6 Implementar página/perfil `/perfil` para que cualquier usuario edite sus datos (nombre, apellido, email).
- [x] 7.7 Proteger rutas `/usuarios` para que solo Administrador acceda; redirigir a dashboard si otro rol intenta acceder.

## 8. Documentación y Cierre

- [x] 8.1 Actualizar `AGENTS.md` si hay nuevas convenciones o patrones establecidos.
- [x] 8.2 Verificar que todos los endpoints nuevos aparecen en la documentación OpenAPI generada por FastAPI.
- [x] 8.3 Ejecutar suite de tests completa (C-01 + C-02 + C-03 + C-04) y confirmar que pasa.
