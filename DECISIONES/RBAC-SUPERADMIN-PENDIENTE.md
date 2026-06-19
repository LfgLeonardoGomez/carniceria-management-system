# Decisiones de RBAC y Multi-tenancy — Pendiente de Implementación

> **Status**: Pendiente (no implementado en sesión actual)  
> **Prioridad**: CRÍTICA — Próximo paso al retomar el proyecto  
> **Guardado**: 2026-06-15

---

## El Problema Actual

El sistema actual tiene un modelo RBAC con 4 roles:

| Rol | Permisos | Scope |
|-----|----------|-------|
| Administrador | `*` (wildcard = todo) | Tenant-scoped (empresa_id obligatorio) |
| Encargado | Operaciones diarias | Tenant-scoped |
| Cajero | Ventas, caja | Tenant-scoped |
| Vendedor | Solo ventas | Tenant-scoped |

**Problema**: El "Administrador" tiene `*` — puede TODO, incluyendo crear otros admins. No hay un rol por encima del sistema. No hay Superadmin.

**Esto es incorrecto para un SaaS multi-tenant.** El modelo actual mezcla "admin del sistema" con "admin de carnicería".

---

## El Modelo Correcto (Requerimiento del Negocio)

### Actores del Sistema

| Actor | Rol | Descripción | Scope |
|-------|-----|-------------|-------|
| **Soporte / Superadmin** | `superadmin` | El dueño del SaaS (yo). Crea empresas, crea admins, asigna admins a empresas. Ingresa a empresas como admin para pruebas y soporte. | **Global** — sin empresa_id |
| **Admin de Empresa** | `admin` | El dueño de la carnicería. Gestiona su empresa, crea usuarios (cajero, encargado, vendedor). Solo en su empresa. | **Tenant-scoped** — empresa_id obligatorio |
| **Encargado** | `encargado` | Responsable de operación diaria. Stock, compras, desposte. | Tenant-scoped |
| **Cajero** | `cajero` | Atiende caja y cobra. Ventas, clientes. | Tenant-scoped |
| **Vendedor** | `vendedor` | Solo realiza ventas. | Tenant-scoped |

### Reglas de Gobierno (Obligatorias)

1. **NO hay registro público** — nadie puede registrarse por su cuenta
2. **Superadmin crea empresas** — `POST /empresas` solo accesible por `superadmin`
3. **Superadmin crea admins** — `POST /usuarios` con rol `admin` solo accesible por `superadmin`
4. **Superadmin asigna admin a empresa** — al crear un admin, el superadmin le asigna `empresa_id`
5. **Admin crea roles operativos** — `POST /usuarios` con roles `encargado`, `cajero`, `vendedor` solo accesible por `admin` (de su empresa)
6. **Superadmin puede ingresar a cualquier empresa** — endpoint de "impersonación" o login directo a empresa para soporte
7. **Admin NO puede crear otros admins** — validación explícita en el servicio de usuarios
8. **Superadmin NO tiene empresa_id** — su JWT no tiene `empresa_id` obligatorio
9. **Admin TIENE empresa_id** — su JWT tiene `empresa_id` del tenant al que pertenece

### Matriz de Permisos RBAC (Propuesta)

```python
PERMISSION_MATRIX = {
    "superadmin": {
        "empresas:create",
        "empresas:read",
        "empresas:update",
        "empresas:delete",
        "usuarios:create",       # puede crear admins
        "usuarios:read",         # puede ver todos los usuarios
        "usuarios:update",       # puede modificar cualquier usuario
        "usuarios:delete",       # puede desactivar cualquier usuario
        "impersonate:admin",     # puede ingresar como admin a una empresa
        "auditoria:read",        # puede ver auditoría global
        "reportes:read",         # puede ver reportes globales
        "soporte:admin",         # panel de soporte
    },
    "admin": {
        "usuarios:create",       # solo encargado, cajero, vendedor
        "usuarios:read",         # solo de su empresa
        "usuarios:update",       # solo de su empresa
        "usuarios:delete",       # solo de su empresa
        "empresas:read",         # solo su empresa
        "empresas:update",       # solo su empresa
        "productos:crud",
        "clientes:crud",
        "proveedores:crud",
        "compras:crud",
        "desposte:crud",
        "stock:crud",
        "ventas:crud",
        "caja:crud",
        "gastos:crud",
        "cuenta-corriente:crud",
        "reportes:read",
        "auditoria:read",        # solo de su empresa
    },
    "encargado": {
        "productos:crud",
        "clientes:crud",
        "proveedores:crud",
        "compras:crud",
        "desposte:crud",
        "stock:crud",
        "ventas:read",
        "caja:read",
        "gastos:crud",
        "cuenta-corriente:read",
        "reportes:read",
    },
    "cajero": {
        "ventas:crud",
        "caja:crud",
        "clientes:read",
        "clientes:update",
        "productos:read",
        "cuenta-corriente:read",
    },
    "vendedor": {
        "ventas:crud",
        "productos:read",
        "clientes:read",
    },
}
```

---

## Cambios Necesarios para Implementar

### 1. Database / Seed Data

- [ ] Agregar rol `superadmin` al seed de roles
- [ ] Modificar seed data: el superadmin por defecto se crea con `empresa_id = NULL`
- [ ] Agregar campo `superadmin` a la tabla `empresa` (FK al superadmin que la creó)

### 2. Backend — RBAC

- [ ] Modificar `backend/src/common/rbac.py`:
  - Agregar `"superadmin"` al `PERMISSION_MATRIX`
  - Quitar `*` de `"admin"`, poner permisos explícitos
  - Agregar `impersonate:admin` permiso
- [ ] Modificar `require_role` para manejar caso `empresa_id = NULL` (superadmin sin tenant)
- [ ] Modificar `get_current_user` para cargar superadmin correctamente

### 3. Backend — Usuarios

- [ ] Modificar `UsuarioService.crear_usuario`:
  - Validar: si `rol == "admin"`, requiere `superadmin`
  - Validar: si `rol` operativo (`encargado`, `cajero`, `vendedor`), requiere `admin` del mismo tenant
  - Validar: si `rol == "superadmin"`, rechazar (solo seed puede crear superadmin)
- [ ] Modificar `UsuarioService.actualizar_usuario`:
  - Validar: `admin` no puede cambiar `rol` a `"admin"` ni `"superadmin"`
  - Validar: `superadmin` puede cambiar cualquier rol

### 4. Backend — Empresas

- [ ] Modificar `EmpresaService`:
  - `POST /empresas` — solo `superadmin`
  - `GET /empresas` — superadmin ve todas, admin ve solo la suya
  - `PUT /empresas/{id}` — superadmin puede modificar cualquiera, admin solo la suya
  - Agregar campo `admin_id` a `empresa` (FK al admin asignado)
- [ ] Endpoint `POST /empresas/{id}/asignar-admin` — solo superadmin

### 5. Backend — Impersonación

- [ ] Nuevo endpoint `POST /soporte/impersonate`:
  - Recibe `empresa_id`
  - Genera un JWT temporal con rol `"admin"` y `empresa_id` de la empresa seleccionada
  - El superadmin puede usar este token para navegar como admin de esa empresa
  - Duración: corta (15 min), auditado en tabla `Auditoria` (acción: `IMPERSONATE_ADMIN`)

### 6. Frontend

- [ ] Panel de Superadmin:
  - Grid de empresas con admin asignado
  - Grid de usuarios (todos)
  - Botón "Ingresar como admin" en cada empresa
- [ ] Ocultar/mostrar rutas según rol:
  - `/admin/empresas` — solo superadmin
  - `/admin/usuarios` — superadmin ve todos, admin ve solo su empresa
  - `/admin/soporte` — solo superadmin

### 7. Tests

- [ ] Test: superadmin crea empresa
- [ ] Test: superadmin crea admin
- [ ] Test: superadmin asigna admin a empresa
- [ ] Test: admin NO puede crear otro admin
- [ ] Test: admin NO puede crear usuarios de otra empresa
- [ ] Test: superadmin impersona admin
- [ ] Test: impersonate JWT tiene claims correctos
- [ ] Test: admin puede crear cajero, encargado, vendedor
- [ ] Test: cajero NO puede crear usuarios
- [ ] Test: multi-tenant: superadmin ve todo, admin ve solo su empresa

---

## Cambios en el Flujo de Autenticación

### Login actual (problema)
```
POST /auth/login
email: admin@carniceria.com
password: ***
→ JWT con empresa_id, rol="admin"
```

### Login correcto (superadmin)
```
POST /auth/login
email: soporte@basile.com
password: ***
→ JWT con rol="superadmin", sin empresa_id
```

### Impersonación
```
POST /soporte/impersonate
empresa_id: 42
→ JWT temporal con rol="admin", empresa_id=42, original_role="superadmin"
```

---

## Impacto en Changes Futuros

### Changes afectados por este cambio

| Change | Impacto | Acción |
|--------|---------|--------|
| C-04 usuarios-rbac | ✅ Ya implementado | Necesita refactor: quitar `*` de admin, agregar superadmin |
| C-03 empresa-config | ✅ Ya implementado | Necesita refactor: `POST /empresas` solo superadmin |
| C-12 ventas-cobro | ❌ No implementado | Debe usar `require_role` correctamente |
| C-13 caja-operaciones | ❌ No implementado | Debe usar `require_role` correctamente |
| C-20 auditoria-notificaciones | ❌ No implementado | Debe registrar acciones de superadmin |

### Recomendación

**Implementar este cambio ANTES de C-12 (ventas-cobro)**. Porque:
- C-12 es el corazón del sistema (donde cobra plata)
- Si el admin tiene `*` (wildcard), puede hacer todo en ventas
- El RBAC correcto debe estar definido antes de que los usuarios reales usen el sistema

---

## Archivos a Modificar

### Existentes (ya implementados)
- `backend/src/common/rbac.py` — Matriz de permisos
- `backend/src/modules/auth/dependencies.py` — `get_current_user`
- `backend/src/modules/auth/router.py` — Login
- `backend/src/modules/usuario/router.py` — CRUD usuarios
- `backend/src/modules/usuario/service.py` — Reglas de negocio
- `backend/src/modules/empresa/router.py` — CRUD empresas
- `backend/src/modules/empresa/service.py` — Reglas de negocio
- `backend/src/database/seeds/roles.py` — Seed de roles
- `backend/src/database/seeds/empresa.py` — Seed de empresa + admin
- `frontend/src/App.tsx` — Rutas
- `frontend/src/stores/authStore.ts` — Estado de autenticación

### Nuevos
- `backend/src/modules/soporte/router.py` — Endpoints de impersonación
- `backend/src/modules/soporte/service.py` — Lógica de impersonación
- `frontend/src/pages/SoportePage.tsx` — Panel de superadmin
- `frontend/src/pages/EmpresasAdminPage.tsx` — Grid de empresas para superadmin
- `frontend/src/components/ImpersonateModal.tsx` — Modal para ingresar como admin

---

## Notas de Implementación

1. **El superadmin no está en la KB original** — este es un requerimiento nuevo que el usuario agregó en la sesión del 2026-06-15. Es correcto para SaaS multi-tenant.

2. **El campo `empresa_id` en JWT** debe ser opcional para superadmin. El middleware debe manejar:
   - `empresa_id` presente → scope del tenant
   - `empresa_id` ausente → scope global (superadmin)
   - `empresa_id` presente en JWT de superadmin → impersonación activa

3. **Auditoría de impersonación** es crítica: cada vez que un superadmin ingresa a una empresa, debe quedar registrado.

4. **No registro público** significa que el endpoint `POST /auth/register` NO debe existir. Actualmente C-02 tiene `/auth/login` y `/auth/recover` — no hay `/auth/register`, pero hay que asegurarse de que nunca se agregue.

---

## Next Action

Cuando se retome el proyecto, ejecutar:

```bash
# Crear change de RBAC refactor
opsx:propose c-rbac-superadmin
# O actualizar C-04 (usuarios-rbac) si no está archivado
```

Esto debe implementarse antes de C-12 (ventas-cobro).

---

## Autor

**User requirement**: El usuario (dueño del proyecto) estableció este modelo el 2026-06-15. Es un requerimiento de negocio crítico para el modelo SaaS.

**Contexto**: El usuario es el "Soporte/Superadmin" del sistema. Necesita poder crear empresas, asignar admins, y dar soporte ingresando a las empresas como admin.
