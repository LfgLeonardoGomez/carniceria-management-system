## 1. Database Migration & Models

- [x] 1.1 Create Alembic migration for `compra` table: `id`, `empresa_id`, `proveedor_id`, `fecha`, `cantidad_medias_reses`, `peso_total`, `costo_total`, `costo_por_kilo`, `costo_promedio_historico`, `observaciones`, `estado`, `created_at`, `updated_at`
- [x] 1.2 Add composite index on `(empresa_id, fecha, proveedor_id)` and `empresa_id` index
- [x] 1.3 Create SQLModel `Compra` with `Decimal` fields (`Numeric(19,3)`), FK to `proveedor` and `empresa`, relationship to `Proveedor`
- [x] 1.4 Add `estado` enum field (activa, anulada) with default `activa`
- [x] 1.5 Run migration and verify schema in PostgreSQL

## 2. Pydantic Schemas

- [x] 2.1 Create `CompraCreate` schema with `extra='forbid'`, fields: fecha, proveedor_id, cantidad_medias_reses, peso_total, costo_total, observaciones (optional)
- [x] 2.2 Add validators: `peso_total > 0`, `costo_total > 0`, `cantidad_medias_reses >= 1`, `fecha` not in future
- [x] 2.3 Create `CompraUpdate` schema (partial, same fields optional)
- [x] 2.4 Create `CompraResponse` schema with all fields including `costo_por_kilo`, `costo_promedio_historico`, `estado`, nested `proveedor` data
- [x] 2.5 Create `CompraListResponse` schema with paginated list + metadata (total, skip, limit)

## 3. Service Layer (CompraService)

- [x] 3.1 Implement `create_compra` with auto-calculation of `costo_por_kilo = costo_total / peso_total` (3 decimal precision)
- [x] 3.2 Add validation: proveedor exists and belongs to empresa; protect division by zero
- [x] 3.3 Implement `update_compra` with recalculation of `costo_por_kilo` if peso/costo changes; block updates on anulada or desposteada
- [x] 3.4 Implement `delete_compra` (soft delete → estado = anulada); block if despostes exist
- [x] 3.5 Implement `list_compras` with filters: proveedor_id, fecha_desde, fecha_hasta, estado, incluir_anuladas; paginated; default order fecha DESC
- [x] 3.6 Implement `get_compra_by_id` with empresa isolation
- [x] 3.7 Implement `get_historial_por_proveedor` with fecha DESC order, pagination, and costo_promedio calculation (exclude anuladas)
- [x] 3.8 Implement `get_costo_promedio_proveedor` helper

## 4. Stock Integration (MovimientoStock)

- [x] 4.1 Create helper `get_or_create_media_res_product` in product service (PLU = "MEDIA_RES", generic product per empresa)
- [x] 4.2 Implement `create_movimiento_stock_entrada` in CompraService: MovimientoStock tipo `entrada_compra`, linked to compra, updates stock_actual
- [x] 4.3 Implement `create_movimiento_stock_salida` for anulaciones: reverse stock, block if stock insufficient
- [x] 4.4 Add `operador_id` to MovimientoStock (current user)
- [x] 4.5 Ensure stock never goes negative (RN-STOCK-04)

## 5. Router Layer

- [x] 5.1 Create `POST /compras` endpoint with `CompraCreate`, inject `db`, `current_user`, `tenant`
- [x] 5.2 Create `GET /compras` endpoint with query params: skip, limit, proveedor_id, fecha_desde, fecha_hasta, incluir_anuladas
- [x] 5.3 Create `GET /compras/{id}` endpoint with empresa validation
- [x] 5.4 Create `PUT /compras/{id}` endpoint with `CompraUpdate`
- [x] 5.5 Create `DELETE /compras/{id}` endpoint for soft delete
- [x] 5.6 Wire `CompraService` into all endpoints; add RBAC (Admin, Encargado only)
- [x] 5.7 Populate `GET /proveedores/{id}/historial` in proveedor router using `CompraService.get_historial_por_proveedor`
- [x] 5.8 Add `costo_promedio_historico` to proveedor historial response metadata

## 6. Frontend

- [x] 6.1 Create Zustand store `useCompraStore` with state: compras, filters, loading, pagination
- [x] 6.2 Create React Query hooks: `useCompras`, `useCompra`, `useCreateCompra`, `useUpdateCompra`, `useDeleteCompra`
- [x] 6.3 Build `CompraGrid` component: table with columns fecha, proveedor, cantidad, peso, costo, costo_por_kilo, estado; filters by fecha and proveedor; pagination
- [x] 6.4 Build `CompraForm` component: form with validation (fecha, proveedor selector, cantidad, peso, costo, observaciones); real-time costo_por_kilo preview
- [x] 6.5 Build `CompraDetail` component: detail view with costo_por_kilo highlighted, proveedor data, estado badge
- [x] 6.6 Add routes: `/compras`, `/compras/nueva`, `/compras/:id`
- [x] 6.7 Add RBAC route guards: only Admin/Encargado can access
- [x] 6.8 Connect to proveedor detail page: show historial de compras panel with real data

## 7. Tests (TDD)

- [x] 7.1 Write test `test_create_compra_calculates_costo_por_kilo` — FAIL first, then implement
- [x] 7.2 Write test `test_create_compra_protege_division_por_cero` — FAIL first
- [x] 7.3 Write test `test_create_compra_genera_movimiento_stock` — FAIL first
- [x] 7.4 Write test `test_create_compra_crea_producto_media_res_si_no_existe` — FAIL first
- [x] 7.5 Write test `test_list_compras_filtra_por_empresa` — FAIL first
- [x] 7.6 Write test `test_anular_compra_genera_salida_stock` — FAIL first
- [x] 7.7 Write test `test_anular_compra_bloqueada_si_stock_insuficiente` — FAIL first
- [x] 7.8 Write test `test_historial_proveedor_ordenado_por_fecha_desc` — FAIL first
- [x] 7.9 Write test `test_historial_proveedor_costo_promedio_excluye_anuladas` — FAIL first
- [x] 7.10 Write test `test_update_compra_recalcula_costo_por_kilo` — FAIL first
- [x] 7.11 Write test `test_update_compra_anulada_retorna_409` — FAIL first
- [x] 7.12 Write test `test_rol_cajero_no_puede_crear_compra` — FAIL first
- [x] 7.13 Run full test suite; fix any failures
- [x] 7.14 Add frontend tests: CompraForm validation, CompraGrid render, cost preview

## 8. Integration & Verification

- [x] 8.1 Verify all endpoints with `curl`/Postman: POST, GET list, GET detail, PUT, DELETE
- [x] 8.2 Verify stock kardex shows correct entries after compra creation
- [x] 8.3 Verify proveedor historial returns real data and costo_promedio
- [x] 8.4 Verify frontend renders grid, form, and detail correctly
- [x] 8.5 Run `pytest` backend suite — all tests pass
- [x] 8.6 Run `vitest` frontend suite — all tests pass
- [x] 8.7 Run `openspec verify` for change c-08
- [ ] 8.8 Archive change with `openspec archive`
