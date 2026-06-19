# Flujos Principales

Cada flujo se documenta extremo a extremo, mostrando interacciones entre componentes.

---

## Flujo 1: Autenticación

**Disparador**: El usuario accede a la aplicación BASILE.
**Actor**: Usuario no autenticado.

**Pasos**:
1. **Frontend** muestra pantalla de login con campos Email y Contraseña.
2. **Usuario** ingresa credenciales y presiona "Iniciar sesión".
3. **Frontend** envía POST `/auth/login` con email y contraseña.
4. **API** valida credenciales contra la base de datos.
5. **API** genera token de sesión (JWT o similar) con claims: `user_id`, `empresa_id`, `rol`.
6. **API** responde con token y datos básicos del usuario.
7. **Frontend** almacena token y redirige al Dashboard.
8. **Frontend** configura interceptores para incluir `Authorization: Bearer <token>` en cada request posterior.

**Diagrama de secuencia**:
```
Usuario → Frontend → API → Base de datos
                        ← token + user
           ← redirección Dashboard
```

**Casos de error**:
- Credenciales inválidas → Frontend muestra error genérico (no revela si el email existe).
- Cuenta inactiva → Frontend informa que la cuenta está deshabilitada.
- Error de red → Frontend muestra mensaje de conectividad.

---

## Flujo 2: Venta con balanza SYSTEL (cobro completo)

**Disparador**: Un cliente llega a la caja con productos pesados.
**Actor**: Cajero o Vendedor.

**Pasos**:
1. **Cajero** abre la Pantalla de Caja.
2. **Frontend** muestra estado del lector, campos para cliente (opcional) y carrito vacío.
3. **Cajero** coloca producto en balanza SYSTEL y genera etiqueta.
4. **Balanza SYSTEL** emite código numérico (ej: `2000270048052`) simulando teclado USB/HID.
5. **Frontend** captura el código en campo oculto de lectura rápida.
6. **Frontend** parsea el código: extrae PLU (posiciones 2-6) y peso (posiciones 7-12 con decimales).
7. **Frontend** envía GET `/productos?plu={plu}` a la API.
8. **API** busca producto por PLU dentro de la empresa del usuario.
9. **API** responde con datos del producto incluyendo precio unitario según tipo de cliente.
10. **Frontend** calcula importe: `peso * precio_unitario` y agrega ítem al carrito.
11. **Cajero** repite pasos 3-10 para cada producto.
12. **Frontend** muestra subtotal, permite aplicar descuentos y muestra total.
13. **Cajero** selecciona medio de pago (Efectivo, Transferencia, Débito, Crédito o Cuenta Corriente).
14. **Cajero** presiona "Cobrar".
15. **Frontend** envía POST `/ventas` con carrito, cliente, descuentos, medio de pago.
16. **API** valida stock suficiente de cada producto (bloqueo de stock negativo).
17. **API** crea la venta, detalles y pago asociado.
18. **API** genera salidas de stock (MovimientoStock tipo `salida_venta`).
19. **API** si el medio es Cuenta Corriente, genera deuda en CuentaCorriente del cliente.
20. **API** actualiza totales de caja abierta (MovimientoCaja).
21. **API** responde con ticket/imprimible.
22. **Frontend** muestra ticket y opción de imprimir.

**Diagrama de secuencia**:
```
Cajero → Frontend → API → Base de datos
   │        ↑            │
   └─ SYSTEL (USB/HID)   │
           │              │
           └──────────────┘
Balanza emula teclado → Frontend captura → API procesa → DB actualiza stock/caja/cc
```

**Casos de error**:
- PLU no encontrado → Frontend muestra alerta y permite búsqueda manual.
- Stock insuficiente → API rechaza la venta, Frontend informa producto y cantidad faltante.
- Cliente con límite de CC excedido → API alerta (comportamiento exacto a definir: bloqueo o advertencia).
- Caja cerrada → Frontend informa que debe abrir caja antes de vender.

---

## Flujo 3: Compra de media res

**Disparador**: La carnicería adquiere una o más medias reses de un proveedor.
**Actor**: Encargado o Administrador.

**Pasos**:
1. **Encargado** accede al módulo "Compras de Media Res".
2. **Frontend** muestra formulario: proveedor, fecha, cantidad, peso total, costo total, observaciones.
3. **Encargado** completa datos y selecciona proveedor existente o crea uno nuevo.
4. **Frontend** envía POST `/compras`.
5. **API** valida datos numéricos (peso > 0, costo > 0).
6. **API** calcula `costo_por_kilo = costo_total / peso_total`.
7. **API** actualiza `costo_promedio_historico` considerando compras anteriores.
8. **API** crea la compra y genera entrada de stock de "media res" (si se maneja como producto genérico) o deja disponible para desposte.
9. **API** registra auditoría.
10. **Frontend** muestra confirmación y detalle de la compra.

**Diagrama de secuencia**:
```
Encargado → Frontend → API → Base de datos
                         ← compra creada
               ← confirmación
```

**Casos de error**:
- Proveedor inexistente y sin permiso para crear → Error de validación.
- División por cero (peso total = 0) → Validación en Frontend y API.

---

## Flujo 4: Desposte de media res

**Disparador**: Se recibió una compra de media res y se procede al desposte.
**Actor**: Encargado o Administrador.

**Pasos**:
1. **Encargado** accede al módulo "Desposte".
2. **Frontend** muestra lista de compras de media res pendientes de desposte.
3. **Encargado** selecciona una compra y presiona "Nuevo desposte".
4. **Frontend** muestra formulario: fecha, operador, y tabla de cortes.
5. **Encargado** ingresa kilos obtenidos para cada corte.
6. **Frontend** calcula en tiempo real: porcentaje de rendimiento por corte.
7. **Encargado** asigna costo a cada corte (distribución automática o manual).
8. **Frontend** calcula `costo_final_por_kilo = costo_asignado / kilos_obtenidos`.
9. **Encargado** presiona "Finalizar desposte".
10. **Frontend** envía POST `/despostes`.
11. **API** valida que `rendimiento_total <= peso_total de la compra`.
12. **API** calcula `merma = peso_total - rendimiento_total`.
13. **API** crea el desposte y los cortes asociados.
14. **API** genera automáticamente entradas de stock (MovimientoStock tipo `entrada_desposte`) para cada corte, vinculando `producto_id` correspondiente.
15. **API** registra auditoría.
16. **Frontend** muestra resumen del desposte: rendimiento, merma, costos finales.

**Diagrama de secuencia**:
```
Encargado → Frontend → API → Base de datos
              │           │
              └─ cálculos └─ genera stock
                 en vivo      automático
```

**Casos de error**:
- Rendimiento mayor al peso original → API rechaza con error de validación.
- Costo asignado total excede costo de compra → Advertencia o bloqueo (comportamiento a definir).
- Producto destino no existe para un corte → Permite crear producto en el momento o requiere pre-carga.

---

## Flujo 5: Cierre de caja

**Disparador**: Final del turno o jornada de ventas.
**Actor**: Cajero, Encargado o Administrador.

**Pasos**:
1. **Cajero** accede al módulo "Caja".
2. **Frontend** muestra caja actualmente abierta (si existe) o solicita apertura.
3. **Cajero** selecciona "Cerrar caja".
4. **Frontend** muestra totales esperados calculados por el sistema:
   - Efectivo esperado = apertura + ventas en efectivo + ingresos manuales - retiros.
   - Transferencias esperadas = suma de ventas por transferencia.
   - Tarjetas esperadas = suma de ventas con débito + crédito.
5. **Cajero** ingresa montos reales contados.
6. **Frontend** calcula diferencias: `real - esperado` para cada medio.
7. **Cajero** confirma cierre.
8. **Frontend** envía POST `/caja/cierre`.
9. **API** guarda montos reales y diferencias.
10. **API** marca caja como `cerrada`.
11. **API** si hay diferencias significativas, genera notificación de alerta.
12. **Frontend** muestra resumen de cierre con diferencias.

**Diagrama de secuencia**:
```
Cajero → Frontend → API → Base de datos
           ← cálculos   ← movimientos
           esperados      de caja
             │
             └─ ingresa reales
                compara
```

**Casos de error**:
- No hay caja abierta → Frontend solicita apertura primero.
- Diferencia muy grande → API puede requerir confirmación de supervisor (rol Encargado/Admin) o generar alerta.

---

## Flujo 6: Recuperación de contraseña

**Disparador**: El usuario olvidó su contraseña.
**Actor**: Usuario registrado.

**Pasos**:
1. **Usuario** accede a `/recuperar-contrasena`.
2. **Frontend** solicita email.
3. **Usuario** ingresa email y envía.
4. **Frontend** envía POST `/auth/recover`.
5. **API** verifica que el email exista (sin revelar si existe o no al usuario para evitar enumeración).
6. **API** genera token único de recuperación con expiración.
7. **API** envía email con enlace `/restablecer-contrasena?token={token}`.
8. **Usuario** accede al enlace desde su correo.
9. **Frontend** valida token con GET (o lo incluye en carga inicial).
10. **Usuario** ingresa nueva contraseña y confirmación.
11. **Frontend** envía POST `/auth/reset` con token y nueva contraseña.
12. **API** valida token, expiración y fuerza de contraseña.
13. **API** actualiza hash de contraseña e invalida token.
14. **Frontend** confirma y redirige a login.

**Casos de error**:
- Token expirado → Frontend informa y solicita reenvío.
- Token inválido → Frontend muestra error de enlace corrupto.
- Contraseña débil → Validación en Frontend y API.
