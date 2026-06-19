## Why

Las carnicerías que usan BASILE necesitan integrar balanzas SYSTEL para agilizar la venta de productos por peso. Hoy, el cajero debe ingresar manualmente el código PLU y el peso de cada corte, lo que genera demoras, errores de tipeo y fricción en el punto de venta. Leer el código de barras que imprime la balanza SYSTEL (formato EAN-13 de 13 dígitos) permite escanear el producto y su peso en una sola acción, reduciendo el tiempo de venta y eliminando errores humanos.

## What Changes

- Nuevo parser de código SYSTEL (`frontend/src/utils/systelParser.ts`) que extrae PLU y peso en kg desde un string de 13 dígitos.
- Nuevo componente `SystelReader` (`frontend/src/components/SystelReader.tsx`) que escucha entrada de teclado HID (emulación de teclado del lector de código de barras), acumula dígitos en un buffer, y dispara un evento al detectar un código válido.
- Nuevo hook `useSystelReader` (`frontend/src/hooks/useSystelReader.ts`) que conecta el lector con el store del carrito de ventas: al leer un código válido, busca el producto por PLU vía `GET /productos?plu={plu}` y lo agrega al carrito con el peso parseado.
- Tests unitarios del parser con casos válidos, inválidos, timeouts y manejo de errores.

## Capabilities

### New Capabilities
- `balanza-systel-parser`: Parsing del código de 13 dígitos de balanza SYSTEL (PLU + peso) con validación de checksum y formato.
- `balanza-systel-reader`: Captura de entrada HID de código de barras en el frontend, buffering con timeout, y exposición de evento `onProductRead`.
- `balanza-systel-pos-integration`: Integración del lector SYSTEL con el flujo de ventas del POS (búsqueda de producto por PLU y agregado al carrito).

### Modified Capabilities
<!-- No se modifican specs existentes; esta change es puramente frontend/utilidad sin alterar contratos de API ni reglas de negocio core. -->

## Impact

- **Frontend**: Nuevos archivos en `frontend/src/utils/`, `frontend/src/components/` y `frontend/src/hooks/`.
- **Backend**: Reutiliza endpoint existente `GET /productos?plu={plu}` (capability de productos-catalogo, C-05). Sin cambios en backend.
- **Dependencias**: Ninguna librería externa nueva; usa APIs nativas del navegador (eventos de teclado).
- **POS / UX**: El flujo de venta de productos por peso se acelera significativamente. El input del lector está oculto y siempre enfocado para recibir scans sin interferir con la UI.
