## 1. Database & Migration

- [x] 1.1 Crear migración Alembic para tabla `proveedor` con campos: `id` (PK), `empresa_id` (FK), `nombre`, `cuit`, `telefono`, `email`, `direccion`, `activo`, `created_at`, `updated_at`
- [x] 1.2 Agregar índice compuesto `(empresa_id, nombre)` y índice único parcial `(empresa_id, cuit)` donde `cuit IS NOT NULL`
- [x] 1.3 Crear RLS policy en `proveedor`: `CREATE POLICY proveedor_empresa_isolation ON proveedor USING (empresa_id = current_setting('app.current_empresa', true)::uuid)`
- [ ] 1.4 Ejecutar migración en entorno de desarrollo y verificar con `alembic upgrade head`
- [x] 1.5 Escribir test de migración: verificar que tabla existe, índices están presentes, RLS está activo

## 2. Backend — Modelo & Schemas

- [x] 2.1 Crear `backend/src/modules/proveedor/models.py` con `Proveedor` (SQLModel) incluyendo `empresa_id` FK y `activo` (default True)
- [x] 2.2 Crear `backend/src/modules/proveedor/schemas.py` con Pydantic `ProveedorCreate`, `ProveedorUpdate`, `ProveedorResponse` usando `extra='forbid'`
- [x] 2.3 Agregar validación de CUIT en schema: 11 dígitos numéricos, opcional
- [x] 2.4 Escribir tests de schemas: validación CUIT válido, CUIT inválido, campos extra rechazados

## 3. Backend — Service & CRUD

- [x] 3.1 Crear `backend/src/modules/proveedor/service.py` con funciones async: `create`, `get_by_id`, `list_by_empresa`, `update`, `delete_logic` (activo=false)
- [x] 3.2 Implementar búsqueda por nombre con `ilike` filtrada por `empresa_id`
- [x] 3.3 Implementar paginación (`skip`/`limit`) en listado
- [x] 3.4 Implementar validación de unicidad de CUIT por empresa en create y update
- [x] 3.5 Escribir tests de service con `testcontainers` (PostgreSQL real): CRUD, búsqueda, paginación, aislamiento multi-tenant

## 4. Backend — Router & API

- [x] 4.1 Crear `backend/src/modules/proveedor/router.py` con router FastAPI y dependencias: `db: AsyncSession`, `current_user`, `tenant`
- [x] 4.2 Implementar endpoints: `GET /proveedores`, `POST /proveedores`, `GET /proveedores/{id}`, `PUT /proveedores/{id}`, `DELETE /proveedores/{id}`
- [x] 4.3 Implementar endpoint `GET /proveedores/{id}/historial` que retorna `[]` (placeholder para C-08) o LEFT JOIN a `compra` si existe
- [x] 4.4 Agregar middleware de autorización RBAC: solo roles Administrador y Encargado pueden acceder
- [x] 4.5 Agregar `empresa_id` implícito en todas las queries (RN-SEG-02)
- [x] 4.6 Escribir tests de router: todos los endpoints, códigos de estado, validación CUIT, aislamiento, permisos RBAC

## 5. Backend — Registro de módulo

- [x] 5.1 Registrar router de proveedores en `backend/src/main.py` con prefijo `/proveedores`
- [x] 5.2 Verificar que la aplicación levanta sin errores (`uvicorn main:app`)
- [x] 5.3 Verificar endpoints con Swagger UI (`/docs`)

## 6. Frontend — Estructura y Rutas

- [x] 6.1 Crear estructura de directorios en `frontend/src/features/proveedores/`: `components/`, `hooks/`, `services/`, `types/`, `pages/`
- [x] 6.2 Definir tipos TypeScript en `types/proveedor.ts`: `Proveedor`, `ProveedorCreate`, `ProveedorUpdate`, `ProveedorFilters`
- [x] 6.3 Crear servicio API en `services/proveedorApi.ts` usando fetch/axios: CRUD + historial
- [x] 6.4 Registrar rutas en el router de la aplicación: `/proveedores` (grid), `/proveedores/nuevo`, `/proveedores/:id`, `/proveedores/:id/editar`
- [x] 6.5 Agregar protección de rutas según RBAC (solo Admin/Encargado)

## 7. Frontend — Grid de Proveedores

- [x] 7.1 Crear `ProveedorGrid` componente con tabla, paginación y búsqueda por nombre
- [x] 7.2 Implementar hook `useProveedores` con React Query para listado, cacheo y mutaciones
- [x] 7.3 Implementar botón "Nuevo proveedor" y acciones de editar/eliminar en cada fila
- [x] 7.4 Implementar confirmación de eliminación (baja lógica) con modal
- [x] 7.5 Escribir tests del grid con React Testing Library: renderizado, búsqueda, paginación, acciones

## 8. Frontend — Formulario de Proveedor

- [x] 8.1 Crear `ProveedorForm` componente reutilizable para alta y edición
- [x] 8.2 Implementar validación en tiempo real: nombre obligatorio, CUIT 11 dígitos si se proporciona, email válido
- [x] 8.3 Integrar con servicio API para crear/actualizar
- [x] 8.4 Manejar errores del backend (409 CUIT duplicado, 422 validación) y mostrar en UI
- [x] 8.5 Escribir tests del formulario: validación, submit, manejo de errores

## 9. Frontend — Ficha y Historial

- [x] 9.1 Crear `ProveedorFicha` componente con datos del proveedor y botón de editar
- [x] 9.2 Crear `ProveedorHistorial` componente que consume `GET /proveedores/{id}/historial`
- [x] 9.3 Mostrar mensaje "Sin compras registradas" cuando el historial está vacío
- [x] 9.4 Implementar navegación entre grid y ficha
- [x] 9.5 Escribir tests de ficha: renderizado, datos, historial vacío

## 10. Testing & QA

- [x] 10.1 Ejecutar suite completa de backend: `pytest backend/tests/modules/proveedor/` — todos deben pasar
- [x] 10.2 Ejecutar suite de frontend: `vitest run frontend/src/features/proveedores/` — todos deben pasar
- [x] 10.3 Verificar aislamiento multi-tenant: crear proveedor en empresa A, confirmar que no aparece en empresa B
- [x] 10.4 Verificar RBAC: intentar acceder como Cajero/Vendedor y confirmar 403
- [x] 10.5 Verificar endpoint de historial: retorna `[]` sin error cuando no hay compras
- [x] 10.6 Revisar coverage de tests: backend > 80%, frontend > 70% de líneas del feature

## 11. Documentación & Sync

- [x] 11.1 Actualizar `CHANGES.md`: marcar `C-07 proveedores` como `[x]` completado
- [x] 11.2 Actualizar `knowledge-base/04_modelo_de_datos.md` si hay discrepancias con el modelo implementado
- [x] 11.3 Verificar que `AGENTS.md` no requiere actualización
- [ ] 11.4 Archivar change con `/opsx:archive c-07-proveedores` (post-merge)
