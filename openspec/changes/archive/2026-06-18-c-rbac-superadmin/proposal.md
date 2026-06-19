## Why

El modelo RBAC actual mezcla "admin de sistema" con "admin de carnicería": el rol `Administrador` tiene wildcard `*` y puede hacer todo, incluyendo crear otros admins. No existe un rol `superadmin` global para el dueño del SaaS. Esto es incorrecto para un SaaS multi-tenant: se necesita separar claramente al operador del SaaS (superadmin, sin `empresa_id`) de los administradores de cada tenant (admin, con `empresa_id` obligatorio). Sin esta separación, no hay forma de que el dueño del SaaS cree empresas, asigne admins, o ingrese a tenants para soporte.

## What Changes

- **BREAKING**: Reemplazar rol `Administrador` wildcard `*` por permisos explícitos de tenant.
- **BREAKING**: Introducir rol `superadmin` con scope global (`empresa_id = NULL`) y permisos globales.
- **BREAKING**: Solo `superadmin` puede crear empresas (`POST /empresas`).
- **BREAKING**: Solo `superadmin` puede crear usuarios con rol `admin`.
- **BREAKING**: `admin` de tenant solo puede crear roles operativos (`encargado`, `cajero`, `vendedor`) dentro de su empresa.
- **BREAKING**: `admin` NO puede crear otros `admin`.
- Nuevo endpoint `POST /soporte/impersonate` para que `superadmin` genere JWT temporal con rol `admin` + `empresa_id` de un tenant (auditoría obligatoria).
- Agregar `admin_id` FK a tabla `empresa` para rastrear admin asignado.
- Nuevo panel de superadmin en frontend con grid de empresas, grid de usuarios globales, y botón de impersonación.
- Actualizar route guards del frontend para reconocer `superadmin` y proteger rutas globales.
- Tests de integración para todas las reglas de gobierno RBAC.

## Capabilities

### New Capabilities
- `superadmin-impersonate`: Endpoint seguro para que superadmin ingrese temporalmente a un tenant como admin, con JWT de corta duración y auditoría en tabla `Auditoria` (action: `IMPERSONATE_ADMIN`).
- `superadmin-panel`: Página frontend exclusiva para superadmin con visualización de todas las empresas, todos los usuarios, y controles de impersonación.
- `empresa-admin-assignment`: Lógica para que superadmin asigne un admin a una empresa mediante FK `admin_id` en tabla `empresa`.

### Modified Capabilities
- `rbac-middleware`: La matriz de permisos pasa de 4 roles a 5 roles (`superadmin`, `admin`, `encargado`, `cajero`, `vendedor`). Se elimina wildcard `*` del rol `admin` y se agrega `superadmin` con permisos globales. `require_role` debe manejar `empresa_id = NULL`.
- `usuarios-crud`: Los requisitos de creación de usuario cambian: `superadmin` puede crear `admin`; `admin` solo puede crear roles operativos dentro de su tenant; `admin` no puede crear otros `admin`. Los tests de escenarios deben reflejar estas restricciones.

## Impact

- **Backend**: `backend/src/common/rbac.py`, `backend/src/modules/auth/dependencies.py`, `backend/src/modules/usuario/service.py`, `backend/src/modules/empresa/service.py`, seeders de roles y empresas.
- **Nuevos archivos backend**: `backend/src/modules/soporte/router.py`, `backend/src/modules/soporte/service.py`.
- **Frontend**: `frontend/src/App.tsx` (route guards), `frontend/src/store/authStore.ts` (rol superadmin), nuevas páginas `SoportePage`, `EmpresasAdminPage`, componente `ImpersonateModal`.
- **Base de datos**: Seed de rol `superadmin`, campo `admin_id` en `empresa`, reglas RLS ajustadas para `empresa_id = NULL`.
- **Tests**: pytest para lógica de creación de usuarios, empresas, impersonación, y route guards.
