## Why

Tres problemas bloquean el uso real de BASILE en producción desde el primer login del admin:

1. **Categorías vacías en el dropdown de Productos** — el seed crea categorías con `empresa_id=NULL` (globales), pero la API filtra por la `empresa_id` del usuario del JWT. El admin de "Carnicería Don Juan" ve 0 categorías y no puede crear productos.

2. **Permisos RBAC sin poblar y 403 en desposte** — la columna `rol.permisos` está en `NULL` para los 5 roles. Además, las rutas existentes de desposte usan el string `despostes:read` (plural) mientras la matriz RBAC está definida con `desposte:read` (singular), por lo que TODOS los roles (incluso admin) reciben 403 al listar despostes. El frontend no puede cargar tipos de corte.

3. **Inconsistencia de UX** — el sidebar dice "POS" pero la pantalla se llama "Venta" en el dominio. Alineamos el copy.

Este change cierra los tres bloqueos y agrega el rol `desposte` (operador de cámara de despostes) limitado al módulo de despostes + lectura de productos/stock.

## What Changes

- **Backend seeds — categorías por empresa**
  - `seed_categorias_producto` se invoca una vez por cada `Empresa` existente en la DB.
  - `seed_tipos_corte` se sigue invocando una sola vez (la tabla `tipo_corte` es global, no tiene columna `empresa_id` por diseño).
  - Seeds **idempotentes** (no duplican registros al re-ejecutar).

- **Backend seeds — permisos RBAC + nuevo rol `desposte`**
  - Se crea `permisos.py` que popula `rol.permisos` desde `PERMISSION_MATRIX` (single source of truth). Formato JSON: `{"recurso": ["operacion", ...]}`.
  - Se agrega el rol `desposte` (UUID determinístico) con permisos: `desposte:read`, `desposte:create`, `desposte:update`, `productos:read`, `stock:read`. Sin acceso a ventas, caja, clientes, ni admin de empresa.
  - `PERMISSION_MATRIX` y `normalize_rol` actualizados para reconocer `desposte`.

- **Backend — endpoint `GET /desposte/tipos`**
  - Lista los 12 tipos de corte (catálogo global) para alimentar el wizard de despostes.
  - Permiso requerido: `desposte:read` (singular, alineado con la matriz).
  - Schema nuevo: `TipoCorteRead`.

- **Backend — fix bug preexistente en router de desposte**
  - 5 endpoints en `desposte/router.py` usaban `despostes:*` (plural) en vez de `desposte:*` (singular). Corregido para que admin/encargado puedan usar el módulo.

- **Frontend — copy del sidebar**
  - "POS" → "Venta" (label del item con path `/pos`). El path y el componente `PosPage` se mantienen; solo cambia el label visible.

## Capabilities

### New Capabilities
- (ninguna; las capacidades `seed-data`, `rbac-middleware` y `frontend-layout` ya existen — se modifican via delta specs)

### Modified Capabilities
- `seed-data`: el seed ahora itera empresas y popula permisos.
- `rbac-middleware`: nuevo rol `desposte` en la matriz.
- `frontend-layout`: label del item POS cambia a Venta.

## Impact

- **Backend**: 2 archivos de seed modificados, 1 nuevo (`permisos.py`), 1 schema nuevo, 1 endpoint nuevo, 1 router con strings de permiso corregidos, 1 matriz RBAC extendida.
- **Frontend**: 1 string de label en `menuConfig.ts`.
- **DB**: ningún cambio de schema. Solo se insertan filas (`categoria_producto`, `rol`, `permisos` JSON).
- **Dependencias**: C-05 (productos), C-09 (desposte), C-04 (usuarios/RBAC).
