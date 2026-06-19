## Why

BASILE necesita un catálogo de productos operativo antes de poder registrar compras, realizar despostes, controlar stock o vender. Sin productos con PLU, precios y stock, los flujos core del negocio (compras → desposte → ventas) están bloqueados. Este change habilita el catálogo completo con importación masiva desde QUENDRA para reducir la carga manual al migrar.

## What Changes

- **Nuevas tablas**: `productos` y `categorias_producto` con migración Alembic, índices y RLS.
- **CRUD REST completo** de productos: alta, edición, baja lógica (`activo = false`), listado paginado y búsqueda rápida por PLU o nombre.
- **CRUD REST de categorías de producto**: seed inicial (Carne vacuna, Carne de cerdo, Pollo, Embutidos, Otros) + creación/edición/eliminación por empresa.
- **Cálculo automático de margen**: campo calculado en cada creación/actualización como `(precio_publico - costo_por_kilo) / precio_publico`.
- **Importación masiva desde Excel QUENDRA**: endpoint `POST /productos/import` que acepta `.xlsx`, parsea filas, muestra vista previa, detecta duplicados de PLU y errores de formato antes de confirmar la carga.
- **Frontend**: grid de productos con filtros, formulario de alta/edición con validaciones en vivo, modal de importación con preview de filas válidas/inválidas.
- **Aislamiento multi-tenant estricto**: todas las queries filtran por `empresa_id`; índice compuesto `(empresa_id, plu)`.

## Capabilities

### New Capabilities
- `product-catalog`: CRUD de productos, búsqueda, cálculo de margen, soft-delete, validaciones de unicidad de PLU por empresa.
- `product-category`: CRUD de categorías de producto, seed inicial por empresa, asignación a productos.
- `product-import`: Importación masiva desde Excel QUENDRA con preview, detección de duplicados y errores de formato.

### Modified Capabilities
- Ninguna. Este change introduce solo capacidades nuevas.

## Impact

- **Backend**: Nuevos routers FastAPI (`/productos`, `/categorias-producto`), nuevos modelos SQLAlchemy (`Producto`, `CategoriaProducto`), repositorios, schemas Pydantic, servicios de importación XLSX.
- **Frontend**: Nuevos feature modules `productos/` con grid, form, modal de importación; integración con Zustand y React Query.
- **Base de datos**: Nuevas tablas con RLS activado; índices en `empresa_id`, `plu`, `nombre`, `categoria_id`.
- **Dependencias**: Requiere `C-03 empresa-config` (empresa_id debe existir). No modifica auth/RBAC (C-02/C-04) pero los consume para proteger endpoints.
