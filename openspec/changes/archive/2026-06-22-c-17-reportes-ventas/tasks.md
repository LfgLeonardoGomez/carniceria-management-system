# Tasks: C-17 — Reportes de ventas

References: spec at `specs/reporte-ventas/spec.md`, design at `design.md`.
TDD OBLIGATORIO: write the test first (RED), then the minimum code (GREEN), then refactor.
Backend: pytest + testcontainers (real PostgreSQL). Frontend: Vitest + React Testing Library.

---

## 1. Backend — Dependencies and Module Setup

- [x] 1.1 Add `openpyxl` and `reportlab` to `backend/requirements.txt` (and `pyproject.toml` if used); confirm they install cleanly with `pip install -r requirements.txt`
- [x] 1.2 Create `backend/src/modules/reporte/schemas.py` with Pydantic models: `VentaReporteRow` (all RN-REP-03 fields), `ReporteVentasResponse` (paginated wrapper), `ExportFormato` (Literal["xlsx","csv","pdf"])
- [x] 1.3 Verify `reporte/models.py` stays a stub (no new DB tables); confirm no Alembic migration is needed

---

## 2. Backend — Report Service (TDD)

- [x] 2.1 **[RED]** Write `tests/reporte/test_service.py`: test `listar_ventas_reporte` returns only `cobrada` sales for the empresa, with correct `cliente_nombre`, `productos`, `total_kilos`, `subtotal`, `total`, `medios_pago` fields — using testcontainers PostgreSQL
- [x] 2.2 **[GREEN]** Implement `reporte/service.py::listar_ventas_reporte(db, empresa_id, fecha_desde, fecha_hasta, cliente_id, skip, limit)` — SQLAlchemy async query with GROUP BY aggregation, joined to `cliente` and `producto`, filtered by `estado='cobrada'` and `empresa_id`
- [x] 2.3 **[TRIANGULATE]** Add test cases: filter by `fecha_desde`/`fecha_hasta` returns only matching rows; filter by `cliente_id` from another empresa returns 0 rows (not 403)
- [x] 2.4 **[RED]** Write test: `ganancia_estimada` is a Decimal when all `costo_unitario` are set; is `None` when any is NULL — calls `calcular_ganancia` from `venta.service`
- [x] 2.5 **[GREEN]** Wire `calcular_ganancia(venta.detalles)` inside the service after loading detalles; populate `ganancia_estimada` on each `VentaReporteRow`
- [x] 2.6 **[RED]** Write test: sales with `cliente_id IS NULL` return `cliente_nombre = "Público general"`
- [x] 2.7 **[GREEN/REFACTOR]** Ensure the client-name resolution logic (razon_social → nombre+apellido → "Público general") is correct and readable

---

## 3. Backend — Excel Export (TDD)

- [x] 3.1 **[RED]** Write `tests/reporte/test_export_xlsx.py`: test `generar_xlsx(rows)` returns valid bytes decodable as a workbook with sheet "Ventas", correct header row, data rows matching input, numeric types for monetary/kilo columns, blank cell for null ganancia
- [x] 3.2 **[GREEN]** Implement `reporte/service.py::generar_xlsx(rows: list[VentaReporteRow]) -> bytes` using `openpyxl`; sheet name "Ventas"; monetary columns as `Decimal`-safe floats (2 d.p.), kilos as 3 d.p., null ganancia as blank cell
- [x] 3.3 **[TRIANGULATE]** Add test: accented characters in product names and client names are preserved in the xlsx output (no encoding error)

---

## 4. Backend — CSV Export (TDD)

- [x] 4.1 **[RED]** Write `tests/reporte/test_export_csv.py`: test `generar_csv(rows)` returns UTF-8 bytes starting with BOM, header matches RN-REP-03 column order, null ganancia renders as empty string, strings with commas are quoted
- [x] 4.2 **[GREEN]** Implement `reporte/service.py::generar_csv(rows: list[VentaReporteRow]) -> bytes` using stdlib `csv` with `utf-8-sig` encoding (BOM included)
- [x] 4.3 **[TRIANGULATE]** Add test: product list containing a comma (e.g., "Nalga, Cuadril") is quoted correctly in the CSV output

---

## 5. Backend — PDF Export (TDD)

- [x] 5.1 **[RED]** Write `tests/reporte/test_export_pdf.py`: test `generar_pdf(rows, empresa_nombre, fecha_desde, fecha_hasta)` returns non-empty bytes starting with `%PDF`; null ganancia renders as em-dash `—`; empresa name appears in the output bytes (basic smoke check)
- [x] 5.2 **[GREEN]** Implement `reporte/service.py::generar_pdf(rows, empresa_nombre, fecha_desde, fecha_hasta) -> bytes` using `reportlab` SimpleDocTemplate + TableStyle; include header (empresa + date range), data table (RN-REP-03 columns), footer totals row (sum of total, sum of total_kilos)
- [x] 5.3 **[TRIANGULATE]** Add test: accented characters (e.g., "Público general", "Costilla") do not raise `UnicodeEncodeError` (register `Helvetica` or bundled font if needed)

---

## 6. Backend — Router (TDD)

- [x] 6.1 **[RED]** Write `tests/reporte/test_router.py`: test `GET /reportes/ventas` returns 200 with paginated JSON for `administrador` role; returns 403 for `cajero` role; returns 401 without JWT
- [x] 6.2 **[GREEN]** Implement `reporte/router.py`: route `GET /reportes/ventas` with query params `fecha_desde`, `fecha_hasta`, `cliente_id`, `skip`, `limit`; dependency `require_roles(["administrador","encargado"])`; calls `listar_ventas_reporte`; returns `ReporteVentasResponse`
- [x] 6.3 **[RED]** Write test: `GET /reportes/ventas/exportar?formato=xlsx` returns 200 with correct `Content-Type` and non-empty body; `formato=csv` returns 200 `text/csv`; `formato=pdf` returns 200 `application/pdf`; `formato=docx` returns 422
- [x] 6.4 **[GREEN]** Implement `GET /reportes/ventas/exportar` route: validate `formato` via `ExportFormato`; build `StreamingResponse` with correct media type and `Content-Disposition: attachment; filename=ventas.<fmt>`; call the corresponding generator (`generar_xlsx`, `generar_csv`, `generar_pdf`)
- [x] 6.5 **[TRIANGULATE]** Add test: export with date-range filter params are passed through correctly (response contains only rows matching those dates)
- [x] 6.6 Register the reporte router in the FastAPI app (check existing pattern in `main.py` or `src/app.py`); confirm both routes appear in `GET /openapi.json`

---

## 7. Frontend — Hook and API Client (TDD)

- [x] 7.1 **[RED]** Write `features/reportes/useReportesVentas.test.ts` (Vitest): test that `useReportesVentas` calls `GET /reportes/ventas` with correct filter params; returns `rows`, `total`, `isLoading`, `error`
- [x] 7.2 **[GREEN]** Implement `frontend/src/features/reportes/useReportesVentas.ts` using React Query (`useQuery`); accept filter params; typed return with `VentaReporteRow[]` (TypeScript strict, no `any`)
- [x] 7.3 Add TypeScript types file `features/reportes/types.ts` with `VentaReporteRow`, `ReportesFilters`, `ExportFormato` — all fields Decimal as `string` (safe JS representation)

---

## 8. Frontend — Filter Component (TDD)

- [x] 8.1 **[RED]** Write `features/reportes/ReportesFilters.test.tsx` (Vitest + RTL): test that date range inputs and cliente selector render; clicking "Apply" calls `onFilter` with correct values; "All clients" option clears `cliente_id`
- [x] 8.2 **[GREEN]** Implement `frontend/src/features/reportes/ReportesFilters.tsx`: date range inputs (`fecha_desde`, `fecha_hasta`), cliente dropdown (fetches empresa's clients via existing client API), "Apply" button; typed props (`onFilter: (filters: ReportesFilters) => void`); no `any`
- [x] 8.3 **[TRIANGULATE]** Add test: submitting with no dates calls `onFilter` with `fecha_desde: undefined, fecha_hasta: undefined` (not empty string)

---

## 9. Frontend — Results Table (TDD)

- [x] 9.1 **[RED]** Write `features/reportes/ReportesTable.test.tsx` (Vitest + RTL): test that rows render with correct columns; null `ganancia_estimada` displays `—`; empty state displays "No results" message; export buttons are disabled when `rows` is empty
- [x] 9.2 **[GREEN]** Implement `frontend/src/features/reportes/ReportesTable.tsx`: table with RN-REP-03 columns; `ganancia_estimada === null` → `—`; empty state; export buttons ("Export Excel", "Export PDF", "Export CSV") that construct the export URL with current filters and trigger a file download via a hidden `<a download>` element; buttons disabled when rows empty
- [x] 9.3 **[TRIANGULATE]** Add test: export button href includes the correct `formato` param and any currently active filter params

---

## 10. Frontend — Page and Routing

- [x] 10.1 Implement `frontend/src/pages/ReportesVentasPage.tsx`: composes `ReportesFilters` + `ReportesTable`; manages filter state; shows loading spinner while `isLoading`; shows error message on API error; role-guard (redirect or "No autorizado" if role is `cajero` or `vendedor`)
- [x] 10.2 Add route `/reportes` in `frontend/src/App.tsx` pointing to `ReportesVentasPage`
- [x] 10.3 Add "Reportes" nav link in the sidebar/nav component (visible only to `administrador` and `encargado`)

---

## 11. Integration Smoke Test

- [x] 11.1 Write `tests/reporte/test_integration.py`: end-to-end test using testcontainers — seed a Venta with detalles (all `costo_unitario` set) and one with a NULL cost; call `GET /reportes/ventas` and assert both appear with correct `ganancia_estimada` values (Decimal vs null)
- [x] 11.2 Write integration test: call `GET /reportes/ventas/exportar?formato=xlsx` for a seeded venta; assert response bytes parse as a valid workbook with at least 2 rows (header + 1 data)
- [x] 11.3 Write integration test: call `GET /reportes/ventas/exportar?formato=csv`; assert UTF-8 BOM present and header row matches RN-REP-03 columns
- [x] 11.4 Write integration test: call `GET /reportes/ventas/exportar?formato=pdf`; assert response body starts with `%PDF`
