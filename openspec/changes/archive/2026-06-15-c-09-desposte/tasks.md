## 1. Backend — Migrations y Modelos

- [x] 1.1 Crear migración Alembic: tabla `desposte` con `id`, `empresa_id`, `compra_id`, `fecha`, `operador_id`, `estado`, `rendimiento_total`, `merma`, `created_at`, `updated_at`
- [x] 1.2 Crear migración Alembic: tabla `corte_desposte` con `id`, `desposte_id`, `tipo_corte`, `kilos_obtenidos`, `porcentaje_rendimiento`, `costo_asignado`, `costo_final_por_kilo`, `producto_id`, `created_at`, `updated_at`
- [x] 1.3 Agregar índices: `desposte(empresa_id)`, `desposte(compra_id)`, `corte_desposte(desposte_id)`, `corte_desposte(producto_id)`
- [x] 1.4 Activar RLS en ambas tablas con política `empresa_id = current_setting('app.current_tenant')::UUID`
- [x] 1.5 Crear SQLModel `Desposte` con relación a `Compra`, `Usuario` y `CorteDesposte`
- [x] 1.6 Crear SQLModel `CorteDesposte` con relación a `Desposte` y `Producto`
- [x] 1.7 Definir enum `TipoCorte` como `Literal` con los 12 valores fijos

## 2. Backend — Schemas Pydantic

- [x] 2.1 Crear `DesposteCreate` schema: `compra_id` (UUID), `fecha` (date), `operador_id` (UUID) — `extra='forbid'`
- [x] 2.2 Crear `DesposteResponse` schema con campos calculados y lista de cortes
- [x] 2.3 Crear `CorteDesposteCreate` schema: `tipo_corte`, `kilos_obtenidos` (Decimal), `producto_id` (UUID, nullable) — `extra='forbid'`
- [x] 2.4 Crear `CorteDesposteResponse` schema con campos calculados
- [x] 2.5 Crear `DesposteFinalizarResponse` schema extendido con `movimientos_stock`
- [x] 2.6 Crear `DesposteListParams` schema para filtros de query (fecha, estado)

## 3. Backend — Servicio de Desposte

- [x] 3.1 Implementar `crear_desposte(db, empresa_id, data)` — validar compra y operador existan y pertenezcan a la empresa, crear en estado "en_proceso"
- [x] 3.2 Implementar `agregar_corte(db, desposte_id, empresa_id, data)` — validar desposte en_proceso, validar tipo_corte, calcular porcentaje_rendimiento y costos, actualizar rendimiento_total del desposte
- [x] 3.3 Implementar `calcular_costos_corte(corte, compra)` — `costo_asignado = (costo_total / peso_total) * kilos_obtenidos`, `costo_final_por_kilo = costo_asignado / kilos_obtenidos`
- [x] 3.4 Implementar `finalizar_desposte(db, desposte_id, empresa_id)` — validar estado en_proceso, validar al menos un corte, validar `rendimiento_total <= peso_total_compra`, calcular merma, asignar costos, generar MovimientoStock por corte, cambiar estado a "finalizado"
- [x] 3.5 Implementar `generar_stock_desposte(db, desposte)` — por cada corte con producto_id, crear `MovimientoStock` tipo `entrada_desposte` con `cantidad_kilos = kilos_obtenidos`, actualizar `producto.stock_actual`
- [x] 3.6 Implementar `listar_despostes(db, empresa_id, filtros)` — paginación, filtros opcionales, eager load de compra y operador
- [x] 3.7 Implementar `obtener_desposte(db, desposte_id, empresa_id)` — eager load de compra, operador, cortes y productos

## 4. Backend — Router /despostes

- [x] 4.1 Implementar `POST /despostes` — inyectar `db`, `current_user`, `tenant`, validar rol Encargado/Admin, retornar 201
- [x] 4.2 Implementar `POST /despostes/{id}/cortes` — validar desposte pertenece a empresa, retornar 201
- [x] 4.3 Implementar `POST /despostes/{id}/finalizar` — transacción ACID, registrar auditoría, retornar 200 con desposte completo y movimientos
- [x] 4.4 Implementar `GET /despostes` — paginación, filtros, retornar 200
- [x] 4.5 Implementar `GET /despostes/{id}` — retornar 404 si no existe o no pertenece a empresa
- [x] 4.6 Registrar router en `main.py` con prefijo `/despostes` y tags=["Desposte"]

## 5. Backend — Auditoría

- [x] 5.1 Implementar `registrar_auditoria_desposte(db, desposte, usuario_id)` — acción "FINALIZAR_DESPOSTE", snapshot JSON completo con desposte y cortes
- [x] 5.2 Integrar llamada a auditoría en `finalizar_desposte` dentro de la misma transacción

## 6. Backend — Tests (TDD)

- [x] 6.1 Escribir test `test_crear_desposte` — creación exitosa, compra no existe, operador no existe, aislamiento multi-tenant
- [x] 6.2 Escribir test `test_agregar_corte` — corte exitoso, tipo inválido, kilos <= 0, desposte finalizado
- [x] 6.3 Escribir test `test_finalizar_desposte` — finalización exitosa, rendimiento > peso (error 422), desposte sin cortes (error 422), desposte ya finalizado (error 409)
- [x] 6.4 Escribir test `test_calculos_desposte` — rendimiento_total, merma, porcentaje_rendimiento, costo_asignado, costo_final_por_kilo con Decimal preciso
- [x] 6.5 Escribir test `test_generacion_stock` — movimientos creados, stock_actual actualizado, corte sin producto no genera movimiento, rollback en error
- [x] 6.6 Escribir test `test_auditoria_desposte` — registro creado con snapshot, inmutabilidad, filtro por desposte
- [x] 6.7 Escribir test `test_listar_obtener_desposte` — paginación, filtros, 404 cuando no pertenece

## 7. Frontend — Wizard de Desposte

- [x] 7.1 Crear ruta `/despostes/nuevo` y componente `DesposteWizard`
- [x] 7.2 Implementar paso 1: selección de compra de media res pendiente (fetch GET /compras?pendientes=true)
- [x] 7.3 Implementar paso 1: selección de fecha y operador (dropdown de usuarios)
- [x] 7.4 Implementar paso 2: tabla de cortes con los 12 tipos fijos, inputs de kilos, selector de producto
- [x] 7.5 Implementar cálculos en vivo: porcentaje_rendimiento, costo_asignado, costo_final_por_kilo por corte
- [x] 7.6 Implementar resumen en vivo: rendimiento_total, merma, porcentaje_total, costo_total
- [x] 7.7 Implementar validación visual: advertencia cuando rendimiento_total se acerca a peso_total_compra, error en rojo si lo excede
- [x] 7.8 Implementar paso 3: resumen de desposte y botón "Finalizar"
- [x] 7.9 Implementar estado global con Zustand: `DesposteStore` para manejar pasos, datos del desposte, cortes y cálculos
- [x] 7.10 Integrar con React Query para server state: mutaciones POST /despostes, POST /despostes/{id}/cortes, POST /despostes/{id}/finalizar

## 8. Frontend — Listado y Detalle

- [x] 8.1 Crear ruta `/despostes` y componente `DespostesList` con tabla paginada
- [x] 8.2 Implementar filtros por fecha y estado
- [x] 8.3 Crear ruta `/despostes/{id}` y componente `DesposteDetail` con resumen completo
- [x] 8.4 Mostrar en detalle: compra origen, operador, fecha, rendimiento, merma, tabla de cortes con costos
- [x] 8.5 Mostrar movimientos de stock generados (si está finalizado)

## 9. Frontend — Tests

- [ ] 9.1 Escribir test de integración: flujo completo wizard → crear desposte → agregar cortes → finalizar → verificar stock generado
- [ ] 9.2 Escribir test de componente: cálculos en vivo renderizan correctamente
- [ ] 9.3 Escribir test de validación: mensaje de error cuando rendimiento > peso

## 10. Integración y Verificación

- [x] 10.1 Correr migraciones en ambiente de desarrollo
- [x] 10.2 Verificar RLS activo con queries directas
- [x] 10.3 Ejecutar test suite completo de backend: pytest con testcontainers
- [x] 10.4 Ejecutar test suite completo de frontend: Vitest + React Testing Library
- [x] 10.5 Verificar con OPSX: `openspec status --change c-09-desposte` (verify no disponible en esta versión de CLI)
- [x] 10.6 Actualizar CHANGES.md: marcar [C-09] como completado
