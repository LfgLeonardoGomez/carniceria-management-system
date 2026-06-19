## Why

El control de proveedores es el prerequisito operativo para el registro de compras de media res (C-08). Sin un catálogo de proveedores confiable y aislado por empresa, no se puede trazar la cadena de abastecimiento ni calcular costos promedio históricos. BASILE necesita un módulo de proveedores que permita al Administrador y al Encargado registrar, consultar y auditar a sus abastecedores antes de que entren las compras.

## What Changes

- **Backend — CRUD de proveedores**: Nuevo módulo `backend/src/modules/proveedor/` con modelos SQLModel, router FastAPI y servicios.
  - Endpoints: `GET /proveedores`, `POST /proveedores`, `GET /proveedores/{id}`, `PUT /proveedores/{id}`, `DELETE /proveedores/{id}` (baja lógica, nunca física — RN-GLOBAL-02).
  - Campos: nombre, CUIT, teléfono, email, dirección.
  - Aislamiento multi-tenant: `empresa_id` en toda query y RLS en PostgreSQL (RN-SEG-02, RN-PROV-01).
  - Índice obligatorio en `(empresa_id, nombre)` para búsquedas rápidas.

- **Backend — Historial de compras**: Endpoint `GET /proveedores/{id}/historial` que lista compras de media res vinculadas al proveedor (inmutable, solo lectura, RN-PROV-02).
  - Se alimenta de la tabla `Compra` que se creará en C-08; en este change se deja el endpoint como placeholder que devuelve `[]` si no hay compras, para no romper la interfaz.

- **Frontend — Grid y ficha de proveedores**: Nuevo feature `frontend/src/features/proveedores/`.
  - Pantalla de listado: grid con filtros, búsqueda por nombre.
  - Formulario de alta/edición: validación de CUIT (11 dígitos), teléfono, email.
  - Ficha detalle: datos del proveedor + panel de historial de compras (placeholder hasta C-08).
  - Acceso restringido: solo Administrador y Encargado (matriz RBAC).

- **Database**: Migración Alembic para crear tabla `proveedor` con `empresa_id`, timestamps y constraints.

- **Testing**: Tests de backend con `pytest` + `testcontainers` (PostgreSQL real) — CRUD, aislamiento multi-tenant, validación CUIT. Tests de frontend con `Vitest` + React Testing Library.

## Capabilities

### New Capabilities
- `proveedores-crud`: Gestión completa del catálogo de proveedores (alta, edición, baja lógica, listado, búsqueda) con aislamiento multi-tenant.
- `proveedores-historial`: Consulta inmutable del historial de compras de media res asociadas a un proveedor.

### Modified Capabilities
- *(Ninguno — este change introduce solo capacidades nuevas sin alterar requisitos de specs existentes.)*

## Impact

- **Backend**: Nuevo módulo `proveedor/` con `models.py`, `router.py`, `service.py`, `schemas.py`.
- **Frontend**: Nuevo feature `proveedores/` con componentes, hooks, servicios y rutas.
- **Database**: Nueva tabla `proveedor` + índice; RLS policy.
- **Dependencias**: Requiere `C-03 empresa-config` ✅ (tabla `empresa` ya existe).
- **Futuro**: El endpoint de historial se conectará con `Compra` en `C-08 compras-media-res`.
