## Context

BASILE es un SaaS multiempresa para carnicerías. El punto de venta (POS) permite registrar ventas de productos. Muchas carnicerías utilizan balanzas SYSTEL que, al pesar un producto, imprimen una etiqueta con un código de barras EAN-13 de 13 dígitos. Este código encapsula el PLU del producto y su peso. El lector de código de barras emula un teclado USB (HID), enviando los dígitos como keystrokes al navegador.

El frontend está construido con React 18, TypeScript strict, Vite y Zustand. No se usará ninguna librería de terceros para la lectura de códigos de barras; se aprovecha la emulación HID universal del lector.

## Goals / Non-Goals

**Goals:**
- Leer y parsear correctamente códigos SYSTEL de 13 dígitos (PLU + peso) en el POS.
- Integrar la lectura con el flujo de ventas: buscar producto por PLU y agregarlo al carrito con el peso correspondiente.
- Proveer una UX transparente: el cajero escanea y el producto aparece en el carrito sin pasos intermedios.
- Manejar errores de forma graceful: código inválido, PLU no encontrado, lectura parcial.

**Non-Goals:**
- Soporte para balanzas que NO usen emulación HID (requerirían SDK nativo o driver específico).
- Modificación del backend (se reutiliza `GET /productos?plu={plu}` existente).
- Cálculo de precio con descuentos o promociones (es responsabilidad del carrito/venta).
- Soporte para formatos de código de barras distintos a SYSTEL EAN-13 de 13 dígitos.

## Decisions

### 1. HID Keyboard Emulation vs. SDK/Direct USB
**Decision:** Usar la emulación de teclado HID del lector de código de barras.
**Rationale:** Es universal en todos los navegadores y sistemas operativos sin requerir permisos especiales, drivers ni librerías nativas. Un lector HID se comporta exactamente como un teclado que tipea muy rápido.
**Alternative considered:** Integrar con SDK del fabricante vía WebUSB o aplicación nativa. Rechazado porque aumenta complejidad de deployment, requiere permisos de navegador y no funciona en todos los entornos.

### 2. Buffering con Timeout vs. Delimiter
**Decision:** Acumular dígitos en un buffer interno. Si se recibe un dígito y pasan 100ms sin otro dígito, se intenta parsear. Si el buffer llega a 13 dígitos, se parsea inmediatamente.
**Rationale:** Los lectores HID envían dígitos consecutivos en ráfagas de ~5-20ms entre keystrokes. El timeout de 100ms es seguro para distinguir entre lectura de código y tipeo humano (mínimo ~100-200ms entre teclas). No se usa un delimitador (ej. Enter) porque el formato SYSTEL es fijo de 13 dígitos.
**Alternative considered:** Escuchar un carácter de fin (ej. Enter). Rechazado porque la configuración del lector puede variar y no todos envían sufijo; además, el formato fijo de 13 dígitos es suficiente.

### 3. Hidden Input vs. Global Key Listener
**Decision:** Usar un `<input type="text">` oculto (visualmente oculto pero focusable) que reciba los keystrokes.
**Rationale:** Garantiza que el navegador reciba el foco de entrada incluso cuando el usuario hace click fuera. El input puede ser re-enfocado automáticamente en eventos `blur`. Un `window.addEventListener('keypress')` global puede perderse si otro elemento consume el evento o si hay un `<input>` activo.
**Alternative considered:** Listener global en `document` o `window`. Rechazado porque es más frágil frente a modales, forms y otros inputs; además, el hidden input permite control explícito del foco.

### 4. Sincronía del Parser
**Decision:** El parser es una función pura síncrona (`parseSystelCode`) que recibe un string y devuelve un resultado tipado o un error.
**Rationale:** No hay I/O ni efectos secundarios; es más fácil de testear y razonar. La responsabilidad de llamar al backend y manejar el estado del carrito queda en el hook.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| El cajero tipea manualmente números y el buffer los confunde con un código SYSTEL | Timeout de 100ms: el tipeo humano es más lento. Si aún así ocurre, el parser valida checksum y longitud exacta, reduciendo falsos positivos. |
| El lector envía caracteres no numéricos (configuración incorrecta) | El componente filtra solo dígitos (`0-9`) antes de agregarlos al buffer. |
| PLU escaneado no existe en la base de datos | El hook maneja el error 404 del backend, muestra alerta al usuario y permite búsqueda manual. |
| Múltiples escaneos rápidos se superponen | Cada parseo exitoso limpia el buffer inmediatamente. El estado de "procesando" en el hook previene duplicados concurrentes. |
| Accesibilidad: el input oculto puede confundir a screen readers | Se usa `aria-hidden="true"` y `tabIndex={-1}` para que no sea navegable ni visible para assistive tech. |
| Focus management en modales o drawers | El componente re-enfoca el input al cerrarse un modal o al detectar `blur`. Se puede pausar/reanudar escucha explícitamente. |

## Migration Plan

No aplica. Esta change es puramente aditiva en el frontend. No hay cambios en base de datos ni en API. El despliegue es incremental: se mergea el frontend y el POS de las carnicerías que tengan balanza SYSTEL comienza a funcionar inmediatamente.

## Open Questions

1. ¿Se requiere soporte para códigos de balanzas de otros fabricantes (Mettler Toledo, Digi, etc.) en el futuro? Esto impactaría en la arquitectura del parser (strategy pattern).
2. ¿El lector de código de barras está configurado para enviar un prefijo/sufijo (ej. F1 antes del código)? Si es así, el componente necesitaría un paso de sanitización adicional configurable.
