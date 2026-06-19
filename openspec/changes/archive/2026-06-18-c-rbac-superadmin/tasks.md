## 1. Database & Seed Data

- [ ] 1.1 Agregar rol `superadmin` al seed de roles (`backend/src/database/seeds/roles.py`)
- [ ] 1.2 Actualizar seed de empresa para no crear admin automáticamente o crearlo vía superadmin
- [ ] 1.3 Agregar campo `admin_id` (nullable, FK a `usuario.id`) a modelo `Empresa` y generar migración Alembic
- [ ] 1.4 Actualizar seed de usuarios para crear superadmin por defecto con `empresa_id = NULL`

## 2. Backend RBAC Core

- [ ] 2.1 Actualizar `backend/src/common/rbac.py`: renombrar roles a minúsculas, agregar `superadmin`, quitar `*` de `admin`, agregar permisos explícitos
- [ ] 2.2 Actualizar `backend/src/modules/auth/dependencies.py`: `get_current_user` debe cargar superadmin con `empresa_id = NULL`; `require_auth` debe manejar `NULL`; renombrar `require_admin` a `require_superadmin` o adaptar para nuevos roles
- [ ] 2.3 Actualizar todos los endpoints que usan `require_admin` o string-match `"Administrador"` para usar nueva matriz RBAC
- [ ] 2.4 Actualizar `has_permission` para que no use wildcard `*` (solo permisos explícitos)

## 3. Backend Usuario Service

- [ ] 3.1 Refactorizar `UsuarioService.crear_usuario` para recibir `current_user` y validar: superadmin puede crear admin; admin solo crea operativos; admin no crea admin
- [ ] 3.2 Actualizar `UsuarioService.actualizar_usuario` para validar que admin no pueda elevar rol a admin ni superadmin
- [ ] 3.3 Actualizar `UsuarioService.listar_usuarios` para que superadmin vea todos sin filtro de empresa
- [ ] 3.4 Actualizar `backend/src/modules/usuario/router.py` para aplicar `require_role` correcto en cada endpoint
- [ ] 3.5 Asegurar que `_check_ultimo_admin` funcione con rol renombrado `admin`

## 4. Backend Empresa Service

- [ ] 4.1 Modificar `EmpresaService.crear_empresa` para que solo `superadmin` pueda crear (usar `require_role("empresas:create")`)
- [ ] 4.2 Modificar `EmpresaService.listar_empresas` para que superadmin vea todas y admin vea solo la suya
- [ ] 4.3 Modificar `EmpresaService.actualizar_empresa` para permitir superadmin modificar cualquiera y admin solo la suya; soportar `admin_id`
- [ ] 4.4 Actualizar `backend/src/modules/empresa/router.py` para aplicar `require_role` correcto
- [ ] 4.5 Crear endpoint `POST /empresas/{id}/asignar-admin` (solo superadmin) o usar PATCH existente con validación de `admin_id`

## 5. Backend Soporte / Impersonate

- [ ] 5.1 Crear módulo `backend/src/modules/soporte/` con `router.py` y `service.py`
- [ ] 5.2 Implementar `POST /soporte/impersonate`: recibe `empresa_id`, genera JWT temporal (15 min) con `rol=admin`, `empresa_id`, `original_role=superadmin`, sin refresh token
- [ ] 5.3 Implementar auditoría: insertar registro en `Auditoria` con `action = "IMPERSONATE_ADMIN"`, actor, target, IP, user agent
- [ ] 5.4 Implementar `POST /soporte/exit-impersonate` o lógica en frontend para volver a superadmin (limpiar token, redirigir)
- [ ] 5.5 Registrar router de soporte en aplicación FastAPI principal

## 6. Frontend Auth & Routes

- [ ] 6.1 Actualizar `frontend/src/store/authStore.ts`: agregar `isImpersonating`, `originalRole`, `empresaId` al interface `User`; actualizar `setUser` para parsear `original_role`
- [ ] 6.2 Crear componente `SuperadminRoute` que permita acceso solo a `rol === 'superadmin'`
- [ ] 6.3 Actualizar `AdminRoute` para permitir `rol === 'admin'` (no superadmin) y ajustar según nueva matriz
- [ ] 6.4 Actualizar `frontend/src/App.tsx`: agregar rutas `/admin/soporte` (SuperadminRoute), `/admin/empresas` (SuperadminRoute); actualizar guards existentes
- [ ] 6.5 Actualizar lógica de login para manejar JWT sin `empresa_id` (superadmin)

## 7. Frontend Superadmin Panel

- [ ] 7.1 Crear página `frontend/src/pages/SoportePage.tsx`: grid de empresas con admin asignado y botón "Ingresar como admin"
- [ ] 7.2 Crear página `frontend/src/pages/EmpresasAdminPage.tsx`: listado de empresas para superadmin (opcional si está incluido en SoportePage)
- [ ] 7.3 Crear componente `ImpersonateModal.tsx`: modal para confirmar impersonación y manejar respuesta JWT
- [ ] 7.4 Crear banner de impersonación: componente visible cuando `isImpersonating === true` con botón "Volver a superadmin"
- [ ] 7.5 Actualizar navegación/layout para mostrar/ocultar ítems de menú según rol (superadmin vs admin vs operativo)

## 8. Tests

- [ ] 8.1 Test: superadmin crea empresa (POST /empresas)
- [ ] 8.2 Test: superadmin crea admin (POST /usuarios con rol admin)
- [ ] 8.3 Test: superadmin asigna admin a empresa (PATCH /empresas/{id} con admin_id)
- [ ] 8.4 Test: admin NO puede crear otro admin (POST /usuarios con rol admin → 403)
- [ ] 8.5 Test: admin NO puede crear usuarios de otra empresa (validar empresa_id forzado)
- [ ] 8.6 Test: superadmin impersona admin (POST /soporte/impersonate)
- [ ] 8.7 Test: impersonate JWT tiene claims correctos (rol=admin, original_role=superadmin, empresa_id)
- [ ] 8.8 Test: admin puede crear cajero, encargado, vendedor
- [ ] 8.9 Test: cajero NO puede crear usuarios (POST /usuarios → 403)
- [ ] 8.10 Test: multi-tenant: superadmin ve todas las empresas en GET /empresas; admin ve solo la suya
- [ ] 8.11 Test: require_role funciona con empresa_id = NULL (superadmin accede a endpoint global)
- [ ] 8.12 Test: auditoría de impersonación registra en tabla Auditoria
- [ ] 8.13 Test: frontend route guard redirige a no superadmin que intenta acceder a /admin/soporte
