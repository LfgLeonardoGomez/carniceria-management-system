## 1. Parser SYSTEL

- [x] 1.1 Crear `frontend/src/utils/systelParser.ts` con función pura `parseSystelCode(code: string): { plu: string; pesoKg: number } | SystelParseError`
- [x] 1.2 Implementar validación de longitud exacta 13 dígitos
- [x] 1.3 Implementar validación de prefijo `2` en posición 1
- [x] 1.4 Extraer PLU (posiciones 2-6) y peso en gramos (posiciones 7-12), convertir a kg con 3 decimales
- [x] 1.5 Definir tipo `SystelParseError` con mensajes descriptivos

## 2. Tests del Parser

- [x] 2.1 Crear `frontend/src/utils/systelParser.test.ts` con Vitest
- [x] 2.2 Test: código válido `2000270048052` → `{ plu: "00027", pesoKg: 4.805 }`
- [x] 2.3 Test: código válido con peso pequeño `2000270001005` → `{ plu: "00027", pesoKg: 0.1 }`
- [x] 2.4 Test: código válido con peso máximo `2999999999995` → `{ plu: "99999", pesoKg: 999.999 }`
- [x] 2.5 Test: longitud inválida (12 y 14 dígitos) → error
- [x] 2.6 Test: caracteres no numéricos → error
- [x] 2.7 Test: prefijo distinto a `2` → error
- [x] 2.8 Test: string vacío y `null`/`undefined` → error
- [x] 2.9 Ejecutar tests y verificar que todos pasan

## 3. Componente SystelReader

- [x] 3.1 Crear `frontend/src/components/SystelReader.tsx`
- [x] 3.2 Implementar input oculto (`opacity: 0`, `position: absolute`) con `aria-hidden="true"` y `tabIndex={-1}`
- [x] 3.3 Implementar buffer de dígitos con `useRef` para acumulación
- [x] 3.4 Implementar timeout de 100ms: si no llega dígito nuevo, limpiar buffer
- [x] 3.5 Implementar parseo inmediato al alcanzar 13 dígitos
- [x] 3.6 Filtrar solo dígitos `0-9` (ignorar letras, símbolos, etc.)
- [x] 3.7 Implementar re-enfoque automático en `blur` con debounce de 50ms
- [x] 3.8 Exponer callback `onProductRead({ plu: string; pesoKg: number })` como prop

## 4. Hook useSystelReader

- [x] 4.1 Crear `frontend/src/hooks/useSystelReader.ts`
- [x] 4.2 Integrar `SystelReader` y manejar estado `enabled` / `paused`
- [x] 4.3 Implementar llamada a `GET /productos?plu={plu}` al recibir código válido
- [x] 4.4 Manejar respuesta exitosa: agregar producto al carrito Zustand con peso como cantidad
- [x] 4.5 Manejar PLU no encontrado (HTTP 404): mostrar alerta/notificación y permitir búsqueda manual
- [x] 4.6 Manejar error de red: mostrar alerta de conexión
- [x] 4.7 Implementar flag `isProcessing` para prevenir duplicados en lecturas rápidas
- [x] 4.8 Implementar cálculo de subtotal con precisión decimal (usar librería decimal o string math, nunca float)

## 5. Tests E2E / Integración

- [x] 5.1 Crear test de integración del hook simulando keystrokes y mock de API
- [x] 5.2 Verificar flujo completo: keystrokes → parseo → API → carrito
- [x] 5.3 Verificar comportamiento de timeout con keystrokes espaciados
- [x] 5.4 Verificar que lecturas rápidas no duplican ítems
- [x] 5.5 Verificar manejo de errores (404, timeout de red)

## 6. Documentación y Cierre

- [x] 6.1 Agregar JSDoc a `parseSystelCode`, `SystelReader` y `useSystelReader`
- [x] 6.2 Actualizar README o docs de frontend si existe sección de integraciones (no aplica — no existe docs de frontend)
- [x] 6.3 Verificar linting y TypeScript strict sin errores
- [x] 6.4 Ejecutar suite completa de tests del proyecto (parser + existentes)
