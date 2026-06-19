## 1. Base de datos y modelos

- [x] 1.1 Crear migración Alembic para tablas `producto` y `categoria_producto` con índices `(empresa_id, plu)` único, índice `lower(nombre)`, FK a `empresa`, campos `Decimal(19,4)` para precios/stock, RLS activado
- [x] 1.2 Implementar modelo SQLModel `Producto` en `backend/src/modules/producto/models.py` con validaciones y cálculo automático de `margen` en pre-save
- [x] 1.3 Implementar modelo SQLModel `CategoriaProducto` (completar existente) con constraint de unicidad `(empresa_id, nombre)`
- [x] 1.4 Actualizar `Empresa` service/seed para crear automáticamente 5 categorías seed al registrar empresa
- [x] 1.5 Seed script retroactivo para empresas existentes que no tengan categorías

## 2. Repositorios y lógica de negocio (Backend) — TDD

- [x] 2.1 Escribir tests para `ProductoRepository`: crear, buscar por PLU, búsqueda por nombre, paginación, unicidad de PLU por empresa
- [x] 2.2 Implementar `ProductoRepository` con async SQLAlchemy, filtros por `empresa_id`, soft-delete (`activo`)
- [x] 2.3 Escribir tests para cálculo automático de margen: `(precio_publico - costo_por_kilo) / precio_publico`, edge case precio=0
- [x] 2.4 Implementar servicio `ProductoService` con método `calcular_margen()` y lógica de negocio
- [x] 2.5 Escribir tests para `CategoriaProductoRepository`: CRUD, unicidad nombre por empresa, eliminación con productos asociados
- [x] 2.6 Implementar `CategoriaProductoRepository` y `CategoriaProductoService`

## 3. Schemas Pydantic (Backend)

- [x] 3.1 Crear schemas `ProductoCreate`, `ProductoUpdate`, `ProductoPublic` en `backend/src/modules/producto/schemas.py` con `extra='forbid'`, validaciones de Decimal >= 0
- [x] 3.2 Crear schemas `CategoriaProductoCreate`, `CategoriaProductoUpdate`, `CategoriaProductoPublic`
- [x] 3.3 Crear schemas de respuesta paginada `PaginatedProductoResponse`, `PaginatedCategoriaResponse`

## 4. Router FastAPI — Productos

- [x] 4.1 Implementar `POST /productos` — crear producto, calcular margen, validar PLU único por empresa, devolver 201
- [x] 4.2 Implementar `GET /productos` — listado paginado con filtros: `search` (PLU/nombre), `categoria_id`, `activo`, orden por nombre
- [x] 4.3 Implementar `GET /productos/{id}` — obtener producto por ID con verificación de `empresa_id`
- [x] 4.4 Implementar `PUT /productos/{id}` — editar producto, recalcular margen, verificar `empresa_id`
- [x] 4.5 Implementar `PATCH /productos/{id}` — baja/alta lógica (activo true/false)
- [x] 4.6 Escribir tests de integración para todos los endpoints de productos con testcontainers (PostgreSQL real)

## 5. Router FastAPI — Categorías

- [x] 5.1 Implementar `POST /categorias-producto` — crear categoría, validar nombre único por empresa
- [x] 5.2 Implementar `GET /categorias-producto` — listar categorías de la empresa autenticada (seed + personalizadas)
- [x] 5.3 Implementar `PUT /categorias-producto/{id}` — editar nombre
- [x] 5.4 Implementar `DELETE /categorias-producto/{id}` — eliminar solo si no tiene productos asociados
- [x] 5.5 Escribir tests de integración para endpoints de categorías

## 6. Importación masiva desde Excel QUENDRA

- [x] 6.1 Agregar dependencia `openpyxl` al backend
- [x] 6.2 Escribir tests para parser de Excel QUENDRA: mapeo de columnas, detección de tipos, filas válidas/inválidas
- [x] 6.3 Implementar servicio `ProductoImportService` con parser `openpyxl`, validación de filas, detección de duplicados (archivo vs DB)
- [x] 6.4 Implementar `POST /productos/import` — recibe archivo, genera preview con session_id (TTL 10 min en memoria/cache), devuelve filas válidas/inválidas/duplicadas
- [x] 6.5 Implementar `POST /productos/import/confirm` — recibe session_id, persiste filas válidas en transacción ACID, devuelve resumen
- [x] 6.6 Escribir tests de integración para importación: archivo válido, duplicados, formato inválido, límite de 5000 filas

## 7. Frontend — Productos

- [x] 7.1 Crear estructura de feature module `frontend/src/features/productos/` con store Zustand
- [x] 7.2 Implementar pantalla grid de productos: tabla paginada, búsqueda rápida, filtros por categoría/activo, columna margen con color
- [x] 7.3 Implementar formulario de alta/edición de producto: validaciones en vivo (PLU único, precios >= 0), selector de categoría, cálculo de margen preview
- [x] 7.4 Implementar acciones de baja/alta lógica con confirmación
- [x] 7.5 Implementar modal de importación Excel: drag & drop, preview de filas válidas/inválidas, barra de progreso, resumen post-confirmación
- [x] 7.6 Escribir tests unitarios con Vitest + React Testing Library para componentes de productos

## 8. Frontend — Categorías

- [x] 8.1 Implementar CRUD de categorías en UI: listado, crear, editar, eliminar (con validación de productos asociados)
- [x] 8.2 Integrar selector de categoría en formulario de producto con posibilidad de crear categoría al vuelo

## 9. Integración y cierre

- [x] 9.1 Conectar routers al `main.py` del backend con prefix `/productos` y `/categorias-producto`
- [x] 9.2 Verificar protección RBAC: solo Administrador y Encargado pueden mutar productos/categorías; todos los roles autenticados pueden leer
- [x] 9.3 Verificar aislamiento multi-tenant en todos los endpoints con tests específicos
- [x] 9.4 Ejecutar suite de tests completa (backend + frontend) y asegurar que todos pasen
- [x] 9.5 Revisar que no haya uso de `float` para dinero ni `any` en TypeScript
