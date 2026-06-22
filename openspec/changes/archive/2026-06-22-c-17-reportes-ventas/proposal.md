# C-17 — Reportes de ventas

## Why

Un Administrador o Encargado (US-017) necesita exportar reportes de ventas filtrados por fecha y cliente para análisis externo o presentación contable. Hoy los datos de ventas viven en `venta`, `detalle_venta` y `pago_venta` sin ninguna vista tabular consolidada ni capacidad de exportación: para llevar las ventas a un contador o analizarlas fuera del sistema, el dueño no tiene forma de sacarlas. El dashboard (C-16) da KPIs agregados de un vistazo, pero no entrega el detalle fila-por-venta ni archivos descargables.

C-17 es el segundo change de la FASE 6 (reportes). Depende solo de C-12 (ventas), que ya provee el modelo real de `venta`/`detalle_venta`/`pago_venta`. Vive en el módulo `reporte`, hoy un stub (`router.py` con un `APIRouter` vacío, `models.py` con solo un `TODO`), por lo que no se pisa con el módulo `dashboard` de C-16.

## What Changes

- **`GET /reportes/ventas`** — listado tabular de ventas, filtrado por `empresa_id` del usuario autenticado, con filtros opcionales:
  - Rango de fechas (`fecha_desde`, `fecha_hasta`) sobre `venta.fecha`.
  - Cliente (`cliente_id`).
  - Devuelve filas con: fecha, cliente, productos, kilos vendidos, subtotal, total, medio de pago, ganancia estimada (RN-REP-03).
- **Exportación en 3 formatos** (RN-REP-02): Excel (`.xlsx`), PDF y CSV, sobre el mismo conjunto filtrado.
- **Frontend**: pantalla de reportes con controles de filtro (rango de fechas + selector de cliente), preview de la tabla de resultados y botones de exportación por formato.

## Approach

- **Agregación en vivo** (misma decisión de producto que C-16, este change): cada request consulta directo sobre las tablas reales (`venta`, `detalle_venta`, `pago_venta`, y joins a `cliente` / `producto`) con SQL + índices. Exacto siempre, sin tablas precomputadas ni jobs de sincronización. Si el volumen escala, se migra a read-model en un change futuro — los cálculos quedan validados por estos tests.
- **Solo lectura**: el endpoint no muta estado. Toda query lleva `WHERE empresa_id = :empresa` (aislamiento multi-tenant, RN-SEG-01). El filtro `cliente_id` también se valida contra la empresa del usuario para que no se pueda filtrar por un cliente de otra empresa.
- **Solo ventas `cobrada`** entran al reporte; las `anulada`/`en_curso`/`suspendida` se excluyen (consistente con C-16). El estado `estado` ya tiene índice por `(empresa_id, estado)`.
- **Índices existentes** cubren los filtros: `ix_venta_empresa_id_fecha` para rango de fechas y `ix_venta_empresa_id_cliente_id` para el filtro de cliente.
- **Dinero en `Decimal`**, kilos con 3 decimales (`detalle_venta.cantidad_kilos` ya es `decimal_places=3`). La exportación preserva la precisión decimal, sin pasar por `float`.

## Out of scope

- Reportes financieros agrupados por período (ventas/costos/utilidad bruta/neta) → es **C-18 reportes-financieros**.
- Análisis de rentabilidad por producto/corte → es **C-19 rentabilidad**.
- KPIs agregados de un vistazo y gráficos → ya cubierto por **C-16 dashboard**.
- Read-model / CQRS / vistas materializadas (diferido; misma postura que C-16).
- Reportes programados, envío por email o almacenamiento de los archivos generados (solo descarga on-demand).

## Open questions (a resolver en design)

1. **"Ganancia estimada" — fuente del costo.** El modelo de datos de la KB (§04) declara `Venta.ganancia_estimada` (calculado) y `DetalleVenta.costo_unitario_estimado` (snapshot del costo al momento de la venta), pero **el modelo real NO tiene ninguno de los dos**: `Venta` no expone `ganancia_estimada` y `DetalleVenta` no expone `costo_unitario_estimado` (solo `cantidad_kilos`, `precio_unitario`, `importe`). El único costo disponible hoy es `Producto.costo_por_kilo`, que es el costo **actual**, no un snapshot histórico. Entonces: ¿la ganancia estimada se calcula con `costo_por_kilo` actual del producto (rápido pero impreciso para ventas viejas si el costo cambió), o este change requiere primero persistir un snapshot del costo en la venta? Decisión con impacto en la exactitud del reporte y posiblemente en el modelo de C-12.

2. **Exportación: ¿backend o frontend?** El CHANGES.md sugiere librerías de ambos lados (SheetJS/xlsx, PDFKit/jspdf). ¿Los 3 archivos se generan en el backend (un endpoint por formato, o `?formato=`) o el frontend arma xlsx/pdf/csv desde el JSON de `GET /reportes/ventas`? Generar en backend garantiza consistencia de datos y formato; generar en frontend ahorra carga del servidor pero duplica la lógica de formateo. Definir la frontera.

3. **Filtro de cliente y "público general".** `venta.cliente_id` es nullable (las ventas a público general no tienen cliente). ¿El reporte sin filtro de cliente incluye las ventas de público general? ¿Hay que ofrecer un filtro explícito tipo "solo público general" (cliente_id IS NULL)? En la columna "cliente" de la tabla, ¿qué se muestra para esas filas — "Público general", o el snapshot `tipo_cliente_al_momento`?

4. **Granularidad de las filas: ¿una fila por venta o por línea de detalle?** RN-REP-03 lista "productos" y "kilos vendidos" como columnas. Una venta tiene N `detalle_venta` (N productos) y puede tener M `pago_venta` (M medios de pago). ¿Una fila por venta con productos/kilos agregados (concatenados/sumados) y medios de pago concatenados, o una fila por línea de detalle? Esto define la forma de la tabla, las columnas "productos"/"medio de pago" y cómo se reparte el total.

5. **Paginación vs. exportación completa.** El preview en pantalla probablemente quiera paginar, pero la exportación debe traer el set completo del filtro. ¿El endpoint pagina y la exportación corre una query sin límite, o se define un tope de filas por reporte para acotar la agregación en vivo?
