## 1. Base de datos y modelo

- [x] 1.1 Verificar tabla MovimientoStock; agregar stock_resultante, referencia_tipo, referencia_id, motivo si faltan
- [x] 1.2 Crear indice compuesto (empresa_id, producto_id, fecha) en MovimientoStock
- [x] 1.3 Actualizar modelo SQLModel MovimientoStock con campos faltantes y validaciones

## 2. Backend - Servicios

- [x] 2.1 Crear StockService con get_stock_actual(empresa_id) - calcula suma de movimientos por producto
- [x] 2.2 Crear StockService.get_kardex(empresa_id, producto_id, pagination) - lista movimientos ordenados por fecha descendente
- [x] 2.3 Crear StockService.ajustar_stock(empresa_id, producto_id, cantidad, motivo, usuario_id) - crea movimiento tipo ajuste y calcula stock_resultante
- [x] 2.4 Crear StockService.get_alertas(empresa_id) - lista productos con stock_actual <= stock_minimo
- [x] 2.5 Implementar validacion validar_stock_no_negativo(empresa_id, producto_id, cantidad_a_descontar) - lanza excepcion si resultaria negativo

## 3. Backend - Router y endpoints

- [x] 3.1 Crear router /stock en FastAPI con prefijo y tags
- [x] 3.2 Implementar GET /stock - respuesta con stock actual por producto, estado y stock_minimo
- [x] 3.3 Implementar GET /stock/movimientos/{producto_id} - kardex paginado
- [x] 3.4 Implementar POST /stock/ajustes - ajuste manual con body Pydantic extra=forbid; requiere rol Encargado/Admin
- [x] 3.5 Implementar GET /stock/alertas - lista de productos con stock bajo/critico
- [x] 3.6 Inyectar empresa_id desde JWT en todos los endpoints; devolver 404 si producto no pertenece a la empresa
- [x] 3.7 Wire router en main.py

## 4. Backend - Tests (TDD)

- [x] 4.1 Escribir test test_stock_calculado_desde_movimientos - multiples entradas y salidas, verifica stock resultante
- [x] 4.2 Escribir test test_bloqueo_stock_negativo_en_venta - intento de salida que dejaria stock < 0, espera 409
- [x] 4.3 Escribir test test_bloqueo_stock_negativo_en_ajuste - ajuste negativo que excede stock, espera 409
- [x] 4.4 Escribir test test_alertas_stock_minimo - producto con stock <= minimo aparece en alertas
- [x] 4.5 Escribir test test_kardex_paginado - consulta con page/page_size, verifica orden descendente y totales
- [x] 4.6 Escribir test test_aislamiento_multi_tenant - usuario de empresa A no ve stock de empresa B
- [x] 4.7 Escribir test test_ajuste_requiere_rol_encargado - cajero intenta ajuste, espera 403
- [x] 4.8 Ejecutar tests y asegurar que pasen

## 5. Frontend - Estado y tipos

- [x] 5.1 Crear tipos TypeScript: MovimientoStock, StockItem, AlertaStock, AjusteStockPayload
- [x] 5.2 Crear Zustand store useStockStore con estado: stock, kardex, alertas, loading, error
- [x] 5.3 Crear acciones: fetchStock, fetchKardex(productoId), fetchAlertas, ajustarStock(payload)

## 6. Frontend - Pantallas y componentes

- [x] 6.1 Crear pagina /stock - grid de productos con columnas: nombre, stock actual, stock minimo, estado (badge OK/alerta/critico)
- [x] 6.2 Crear componente KardexTable - tabla de movimientos para producto seleccionado, con paginacion
- [x] 6.3 Crear modal AjusteStockModal - formulario con producto_id (preseleccionado), cantidad_kilos, motivo; valida cantidad y motivo
- [x] 6.4 Crear panel/componente AlertasPanel - lista de productos con stock bajo; navegable al kardex del producto
- [x] 6.5 Agregar rutas a App.tsx y navegacion en sidebar/menu

## 7. Integracion y verificacion

- [x] 7.1 Verificar que POST /stock/ajustes actualice stock y aparezca en kardex inmediatamente
- [x] 7.2 Verificar que GET /stock/alertas refleje cambios tras ajuste o venta
- [x] 7.3 Correr suite completa de backend (pytest) y confirmar verde
- [x] 7.4 Correr linter TypeScript y build de frontend sin errores
