# C-04 — usuarios-rbac

## Why

BASILE es un SaaS multi-tenant donde cada carnicería opera con múltiples empleados (Administrador, Encargado, Cajero, Vendedor). Sin un módulo de gestión de usuarios y un sistema de autorización basado en roles (RBAC), no es posible controlar quién accede a qué datos ni mantener el aislamiento entre empresas. Este change habilita la administración completa de usuarios dentro de una empresa y protege los endpoints según la matriz de permisos definida en la base de conocimiento.

## What Changes

- **CRUD de usuarios** bajo `/usuarios` (alta, listado, edición, soft-delete, reactivación) — accesible únicamente para usuarios con rol Administrador.
- **Asignación de roles** (Administrador, Encargado, Cajero, Vendedor) con validación de permisos del solicitante y protección del último administrador de la empresa.
- **Middleware de autorización RBAC**: dependency `require_role(permiso: str)` que verifica permisos del usuario autenticado contra la matriz RBAC inmutable antes de ejecutar cualquier endpoint protegido.
- **Perfil de usuario**: endpoint `GET /usuarios/me` disponible para cualquier usuario autenticado para consultar y editar sus propios datos.
- **Contraseña temporal**: al crear un usuario, el sistema genera una contraseña temporal visible **una sola vez** en la respuesta POST; el usuario debe cambiarla en su primer login.
- **Seed de usuario administrador** por defecto para la primera empresa creada en el sistema.
- **Frontend**: pantalla de gestión de usuarios con grid, formulario de alta/edición, selector de rol, y modal de visualización de contraseña temporal; protección de rutas por rol en el router.
- **Tests**: TDD obligatorio — tests de CRUD con permisos, middleware RBAC, protección del último admin, validación de reglas de negocio, aislamiento multi-tenant, y flujo de login con cuenta desactivada.

## Capabilities

### New Capabilities
- `usuarios-crud`: Alta, listado, edición, baja lógica y reactivación de usuarios dentro del ámbito de una empresa. Incluye validación de email único global y protección del último administrador.
- `rbac-middleware`: Sistema de autorización basado en roles con matriz de permisos inmutable en código. Dependency `require_role` para endpoints FastAPI. Verificación de permisos en cada request autenticado.
- `perfil-propio`: Endpoint y pantalla para que cualquier usuario autenticado consulte y edite su propio perfil (nombre, apellido, contraseña) sin permisos de administrador.
- `frontend-usuarios`: Pantalla de gestión de usuarios en el SPA React con grid, formularios, selector de rol, desactivación/reactivación, y modal de contraseña temporal. Protección de rutas por rol en el router.

### Modified Capabilities
- *(Ninguna. Los cambios en `auth-core` son de integración técnica, no de requisitos funcionales.)*

## Impact

- **Backend**: Nuevo módulo `backend/src/modules/usuario/` (reemplaza placeholders existentes), nuevo archivo `backend/src/common/rbac.py`, extensión de `backend/src/modules/auth/` para inyectar permisos en `current_user`, aplicación de `require_role` en routers existentes (`/empresas`).
- **Frontend**: Nuevas rutas `/usuarios`, `/perfil`, nuevos componentes de grid y formulario, nuevo store Zustand para usuarios, actualización del router para protección por rol.
- **API**: Nuevos endpoints REST bajo `/usuarios` y `/usuarios/me`.
- **Base de datos**: Verificación de índices en `usuario(empresa_id, activo)` y restricción de unicidad en `usuario(email)`.
- **Dependencias**: Requiere que `C-02 auth-core` y `C-03 empresa-config` estén completamente implementados y archivados.
