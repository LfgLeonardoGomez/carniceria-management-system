# CHANGES — Secuencia de Implementación BASILE

> Índice canónico de todos los changes del proyecto BASILE.
> Cada change es atómico: un agente puede implementarlo en una sesión (~4-6 horas).
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**

---

## Cómo usar este documento

1. **Identificá el change** que corresponde a la épica o funcionalidad que vas a implementar (usá el árbol de dependencias para saber qué ya debe existir).
2. **Leé la KB** referenciada en la sección *Leer antes* de ese change.
3. Ejecutá `/opsx:propose C-NN-{nombre}` para que OpenSpec genere la especificación completa del change.
4. Implementá siguiendo el diseño, las specs y las tareas.
5. Marcá el checkbox `[x]` una vez mergeado a `main`.

---

## Árbol de dependencias

```
C-01 foundation-setup
│
├── C-02 auth-core
│   └── C-04 usuarios-rbac
│
├── C-03 empresa-config
│   ├── C-05 productos-catalogo
│   ├── C-06 clientes
│   └── C-07 proveedores
│       │
       ├── C-08 compras-media-res
       │   └── C-09 desposte
       │       └── C-10 stock-movimientos
       │
       ├── C-11 balanza-systel
       │
       ├── C-12 ventas-cobro
       │   ├── C-13 caja-operaciones
       │   └── C-14 cuentas-corrientes
       │
       └── C-15 gastos
│
           ├── C-16 dashboard
           ├── C-17 reportes-ventas
           ├── C-18 reportes-financieros
           ├── C-19 rentabilidad
           └── C-20 auditoria-notificaciones
```

---

### Paralelismo por fase

**GATE 0: C-01 foundation-setup ✓**
  → C-02 auth-core                      [Agente A]
  → C-03 empresa-config                 [Agente B]

**GATE 1: C-02 auth-core + C-03 empresa-config ✓**
  → C-04 usuarios-rbac                  [Agente A]
  → C-05 productos-catalogo             [Agente B]
  → C-06 clientes                       [Agente C]

**GATE 2: C-03 empresa-config ✓  ← FORK**
  → C-07 proveedores                    [Agente A]

**GATE 3: C-05 productos-catalogo + C-06 clientes + C-07 proveedores ✓  ← FORK**
  → C-08 compras-media-res              [Agente A]
  → C-10 stock-movimientos              [Agente B — si C-05 ✓]
  → C-11 balanza-systel                 [Agente C — frontend/parser, independiente]

**GATE 4: C-08 compras-media-res ✓**
  → C-09 desposte                       [Agente A]

**GATE 5: C-09 desposte + C-10 stock-movimientos + C-06 clientes ✓  ← FORK**
  → C-12 ventas-cobro                   [Agente B]
  → C-13 caja-operaciones               [Agente A — si C-03 ✓]
  → C-15 gastos                         [Agente C — si C-03 ✓]

**GATE 6: C-12 ventas-cobro + C-13 caja-operaciones + C-15 gastos ✓  ← FORK**
  → C-14 cuentas-corrientes             [Agente A — si C-06 ✓]
  → C-16 dashboard                      [Agente B]
  → C-17 reportes-ventas                [Agente C]

**GATE 7: C-16 dashboard + C-15 gastos + C-09 desposte ✓**
  → C-18 reportes-financieros           [Agente B]
  → C-19 rentabilidad                   [Agente C — si C-09 ✓]
  → C-20 auditoria-notificaciones       [Agente A — transversal, depende de todo]

---

### Camino crítico (12 changes — mínimo irreducible)

```
C-01 → C-02 → C-03 → C-05 → C-06 → C-08 → C-09 → C-10 → C-12 → C-13 → C-16 → C-20
```

> Nota: El camino crítico asume que el sistema es usable para producción cuando tiene foundation, auth, catálogos, compras/desposte/stock, ventas/caja, dashboard y auditoría. Los reportes avanzados, rentabilidad detallada y notificaciones son value-add posterior.

---

### Plan óptimo con 3 agentes

| Paso | Agente A (Backend Core) | Agente B (Backend Aux) | Agente C (Frontend) |
|------|-------------------------|------------------------|---------------------|
| 1 | C-01 foundation-setup | — | — |
| 2 | C-02 auth-core | C-03 empresa-config | — |
| 3 | C-04 usuarios-rbac | C-05 productos-catalogo | C-06 clientes |
| 4 | C-07 proveedores | C-08 compras-media-res | C-10 stock-movimientos |
| 5 | C-09 desposte | C-12 ventas-cobro | C-11 balanza-systel |
| 6 | C-13 caja-operaciones | C-14 cuentas-corrientes | C-15 gastos |
| 7 | C-20 auditoria-notificaciones | C-16 dashboard | C-17 reportes-ventas |
| 8 | — | C-18 reportes-financieros | C-19 rentabilidad |

> El plan asume que cada change incluye su respectiva capa frontend/backend según la naturaleza (los backend-heavy se dan en A/B, los frontend-heavy en C). Si el stack elegido es full-stack (ej. Next.js), el agente C puede también cubrir backend cuando el frontend es predominante.

---

## FASE 1 — Fundación e Infraestructura

> Todo change de esta fase es pre-requisito estricto del resto. No se puede saltar ninguno.

### [C-01] `foundation-setup`
- **Estado**: `[x]` completado
- **Scope**:
  - Scaffolding del proyecto según stack aprobado (ver `08_arquitectura_propuesta.md` §Estructura de directorios).
  - Configuración base de base de datos (conexión, pool, migraciones framework).
  - Tablas iniciales: `empresa`, `rol`, `usuario` (schema mínimo para auth).
  - Seed data obligatorio: roles (Administrador, Encargado, Cajero, Vendedor), categorías de producto sugeridas, tipos de corte de desposte, categorías de gasto.
  - Variables de entorno documentadas: `DATABASE_URL`, `JWT_SECRET`, `EMAIL_HOST`, `FRONTEND_URL`, etc.
  - Setup de CORS, rate limiting básico en auth, logging estructurado.
  - Tests: conexión a DB, seed data completa, health-check endpoint.
- **Dependencias**: ninguna
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones aplicados, §Seguridad
  - `knowledge-base/04_modelo_de_datos.md` §Empresa, §Rol, §Usuario
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-01 Multi-tenancia

### [C-02] `auth-core`
- **Estado**: `[x]` completado
- **Scope**:
  - `POST /auth/login` — validación email/contraseña, JWT access + refresh tokens, claims: `user_id`, `empresa_id`, `rol`.
  - Middleware de autenticación que inyecta `empresa_id` en el request para aislamiento multi-tenant (RN-SEG-02).
  - `POST /auth/recover` — generación de token único de recuperación con expiración (1h).
  - `POST /auth/reset` — validación de token, fuerza de contraseña, actualización de hash.
  - Protección de rutas: todo excepto `/login`, `/recuperar-contrasena`, `/restablecer-contrasena` requiere token válido.
  - Rate limiting en endpoints de auth: 5 intentos / 60s por IP+email.
  - Tests: login exitoso/fallido, token claims, middleware empresa_id, rate limiting, recuperación completa.
- **Dependencias**: `C-01`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §RBAC — Matriz de permisos
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AU, §RN-SEG
  - `knowledge-base/07_flujos_principales.md` §Flujo 1: Autenticación

### [C-03] `empresa-config`
- **Estado**: `[x]` completado
- **Scope**:
  - `CRUD /empresas` — datos fiscales, nombre comercial, razón social, CUIT (validación 11 dígitos), domicilio, teléfono, email.
  - Upload de logo: endpoint `POST /empresas/:id/logo`, almacenamiento en `UPLOAD_PATH` o servicio de files (S3/Cloudinary).
  - Campo `configuracion_general` y `parametros_operativos` como JSON/estructurado (placeholder para umbrales de alertas futuros).
  - Soft delete (`activa = false`) sin eliminación física.
  - Frontend: pantalla de configuración de empresa accesible solo para Administrador.
  - Tests: CRUD, validación CUIT, upload, aislamiento multi-tenant.
- **Dependencias**: `C-01`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Empresa
  - `knowledge-base/06_funcionalidades.md` §US-003
  - `knowledge-base/05_reglas_de_negocio.md` §RN-SEG-01

### [C-04] `usuarios-rbac`
- **Estado**: `[x]` completado — 5 roles (superadmin, admin, encargado, cajero, vendedor), matriz de permisos sin wildcard, middleware RBAC, validaciones de creación, impersonación, tests
- **Scope**:
  - `CRUD /usuarios` — alta, baja lógica, edición, listado filtrado por empresa.
  - Asignación de rol (Administrador, Encargado, Cajero, Vendedor) con validación de permisos del solicitante.
  - Recuperación de contraseña: envío de email con enlace seguro (integración con servicio SMTP/SendGrid/AWS SES).
  - Endpoint `GET /usuarios/me` con datos del usuario autenticado.
  - Middleware de autorización RBAC: verifica que el rol del usuario tenga permiso sobre el recurso solicitado (RN-AU-03).
  - Seed data: crear usuario administrador por defecto para la primera empresa.
  - Tests: CRUD con permisos, asignación de roles, middleware RBAC, envío de email (mock en tests).
- **Dependencias**: `C-02`, `C-03`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §Actores del sistema, §RBAC
  - `knowledge-base/04_modelo_de_datos.md` §Usuario
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AU-03

---

## FASE 2 — Catálogos Core

> Los catálogos son prerequisito de compras, ventas, stock y cuentas corrientes. Pueden desarrollarse en paralelo una vez que C-03 está listo.

### [C-05] `productos-catalogo`
- **Estado**: `[x]` completado
- **Scope**:
  - `CRUD /productos` — PLU (único por empresa), nombre, categoría, precio público, precio mayorista, costo por kilo, margen calculado, stock actual, stock mínimo, activo.
  - `CRUD /categorias-producto` — seed inicial + personalizables por empresa.
  - Búsqueda rápida por PLU o nombre (índice compuesto `empresa_id + plu`).
  - Cálculo automático de margen: `(precio_publico - costo_por_kilo) / precio_publico`.
  - Importación masiva desde Excel QUENDRA: `POST /productos/import`, parser xlsx, vista previa, detección de duplicados y errores de formato.
  - Frontend: grid de productos, formulario de alta/edición, modal de importación con preview.
  - Tests: unicidad PLU, cálculo margen, importación con errores, búsqueda, aislamiento multi-tenant.
- **Dependencias**: `C-03`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Producto, §CategoriaProducto
  - `knowledge-base/06_funcionalidades.md` §US-005, §US-006
  - `knowledge-base/05_reglas_de_negocio.md` §RN-PROD

### [C-06] `clientes`
- **Estado**: `[x]` completado
- **Scope**:
  - `CRUD /clientes` — nombre, apellido, razón social, CUIT, teléfono, email, dirección, tipo (publico_general, mayorista, especial), límite de cuenta corriente, saldo actual.
  - Historial de compras: endpoint `GET /clientes/:id/historial` que lista ventas asociadas.
  - Saldo de cuenta corriente: campo calculado/snapshot desde tabla `CuentaCorriente` (se actualizará en C-14).
  - Frontend: grid de clientes, ficha con historial y saldo, filtros por tipo.
  - Tests: CRUD, historial, cálculo saldo, aislamiento multi-tenant.
- **Dependencias**: `C-03`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Cliente
  - `knowledge-base/06_funcionalidades.md` §US-007
  - `knowledge-base/05_reglas_de_negocio.md` §RN-CLI

### [C-07] `proveedores`
- **Estado**: `[x]` completado — bug menor: historial vacío devuelve paginación en vez de `[]`
- **Scope**:
  - `CRUD /proveedores` — nombre, CUIT, teléfono, email, dirección.
  - Historial de compras: endpoint `GET /proveedores/:id/historial` que lista compras de media res asociadas (inmutable, RN-PROV-02).
  - Frontend: grid de proveedores, ficha con historial de compras.
  - Tests: CRUD, historial inmutable, aislamiento multi-tenant.
- **Dependencias**: `C-03`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Proveedor
  - `knowledge-base/06_funcionalidades.md` §US-008
  - `knowledge-base/05_reglas_de_negocio.md` §RN-PROV

---

## FASE 3 — Compras, Desposte y Stock

> El flujo de compra → desposte → stock es el corazón operativo de BASILE. Ninguna venta puede existir sin productos con stock.

### [C-08] `compras-media-res`
- **Estado**: `[x]` completado
- **Scope**:
  - `CRUD /compras` — fecha, proveedor (FK), cantidad de medias reses, peso total (kg), costo total, observaciones.
  - Cálculo automático: `costo_por_kilo = costo_total / peso_total` (RN-COMP-01).
  - Cálculo y actualización de `costo_promedio_historico` por proveedor/general.
  - Generación automática de entrada de stock: `MovimientoStock` tipo `entrada_compra` vinculado a la compra (producto genérico "media res" o placeholder para desposte).
  - Registro de auditoría: acción "CREAR_COMPRA" con snapshot.
  - Frontend: formulario de compra, selección de proveedor, detalle con costo por kilo calculado.
  - Tests: cálculos numéricos, división por cero protegida, entrada stock automática, auditoría, aislamiento multi-tenant.
- **Dependencias**: `C-05`, `C-07`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Compra
  - `knowledge-base/06_funcionalidades.md` §US-009
  - `knowledge-base/07_flujos_principales.md` §Flujo 3: Compra de media res

### [C-09] `desposte`
- **Estado**: `[x]` completado — backend completo (models, service, router, tests) + frontend wizard, migración 011 para tablas `desposte` y `corte_desposte`, seed de tipos de corte arreglado
- **Scope**:
  - `POST /despostes` — selección de compra origen, fecha, operador (FK → Usuario).
  - Tabla de cortes: 12 tipos fijos (asado, vacio, nalga, cuadril, peceto, bola_de_lomo, lomo, matambre, costilla, osobuco, molida, otros).
  - Por corte: kilos obtenidos, porcentaje rendimiento calculado, costo asignado, costo final por kilo (`costo_asignado / kilos_obtenidos`).
  - Cálculos automáticos: `rendimiento_total = sum(kilos_obtenidos)`, `merma = peso_total_compra - rendimiento_total` (RN-DESP-03, RN-DESP-04).
  - Validación: `rendimiento_total <= peso_total_compra`.
  - Al finalizar: generación automática de entradas de stock (`MovimientoStock` tipo `entrada_desposte`) para cada corte, vinculando `producto_id` correspondiente (RN-DESP-06).
  - Registro de auditoría: acción "FINALIZAR_DESPOSTE" con snapshot completo.
  - Frontend: wizard de desposte, tabla de cortes con cálculos en vivo, resumen de rendimiento/merma/costos.
  - Tests: validación rendimiento > peso, cálculos de merma, generación stock automática, auditoría.
- **Dependencias**: `C-08`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Desposte, §CorteDesposte
  - `knowledge-base/06_funcionalidades.md` §US-010
  - `knowledge-base/07_flujos_principales.md` §Flujo 4: Desposte de media res
  - `knowledge-base/05_reglas_de_negocio.md` §RN-DESP

### [C-10] `stock-movimientos`
- **Estado**: `[x]` completado
- **Scope**:
  - Tabla `MovimientoStock` (Kardex): `empresa_id`, `producto_id`, `tipo` (entrada_compra, entrada_desposte, salida_venta, ajuste), `cantidad_kilos`, `stock_resultante` (snapshot), `referencia_id` + `referencia_tipo` (polimórfico).
  - Índice compuesto `(empresa_id, producto_id, fecha)` para consultas de kardex performantes.
  - Endpoint `GET /stock` — stock actual por producto (calculado o snapshot).
  - Endpoint `GET /stock/movimientos/:producto_id` — kardex completo con paginación.
  - Endpoint `POST /stock/ajustes` — ajustes manuales de stock con motivo (requiere rol Encargado/Admin).
  - Bloqueo de stock negativo: validación en toda salida (RN-STOCK-04).
  - Alertas de stock mínimo: endpoint `GET /stock/alertas` que lista productos con `stock_actual <= stock_minimo`.
  - Frontend: pantalla de stock, kardex por producto, modal de ajuste, panel de alertas.
  - Tests: cálculo stock resultante, bloqueo stock negativo, alertas, kardex paginado, aislamiento multi-tenant.
- **Dependencias**: `C-05`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §MovimientoStock
  - `knowledge-base/06_funcionalidades.md` §US-011
  - `knowledge-base/05_reglas_de_negocio.md` §RN-STOCK

---

## FASE 4 — Ventas, Balanza y Caja

> Esta fase conecta el catálogo y el stock con la operación diaria de la carnicería. Es la más visible para el negocio.

### [C-11] `balanza-systel`
- **Estado**: `[x]` completado — Parser SYSTEL 13 dígitos, componente SystelReader (input oculto HID), hook useSystelReader con integración a carrito Zustand, 19 tests pasando
- **Scope**:
  - Implementación del parser de etiquetas SYSTEL: extracción de PLU (posiciones 2-6) y peso (posiciones 7-12, 2 decimales implícitos) desde string de 13 dígitos (ej. `2000270048052`).
  - Campo oculto en frontend para captura de input de teclado HID/USB sin perder foco de la UI (timeout de lectura, validación de longitud).
  - Componente reutilizable: `SystelReader` que expone evento `onProductRead({ plu, peso, importe_calculado })`.
  - Integración con backend: `GET /productos?plu={plu}` para obtener precio según tipo de cliente.
  - Manejo de errores: PLU no encontrado (alerta + búsqueda manual), formato inválido, lectura accidental.
  - Tests unitarios: parser con múltiples ejemplos, cálculo importe, manejo de errores. Tests de integración: flujo completo balanza → carrito.
- **Dependencias**: `C-05`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/05_reglas_de_negocio.md` §RN-VENT-01 a RN-VENT-04
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-03 Lectura de balanza SYSTEL
  - `knowledge-base/07_flujos_principales.md` §Flujo 2: Venta con balanza SYSTEL (pasos 3-10)

### [C-12] `ventas-cobro`
- **Estado**: `[x]` completado — backend models, schemas, state machine, service, router, tests (34 pasando); frontend POS page mínima; placeholders C-13/C-14 creados forward-compatible
- **Scope**:
  - `POST /ventas` — creación de venta con carrito, cliente (nullable), descuentos, medio de pago.
  - Carrito: array de ítems `{ producto_id, cantidad_kilos, precio_unitario, importe }`.
  - Cálculo: subtotal = sum(importes), total = subtotal - descuentos.
  - Precio automático según tipo de cliente: público → precio_publico, mayorista → precio_mayorista, especial → precio_publico (v1.0, ver IN-02).
  - Estados de venta: `en_curso`, `suspendida`, `cobrada`, `anulada`. Transiciones controladas.
  - Medios de pago: efectivo, transferencia, debito, credito, cuenta_corriente (RN-PAGO-01).
  - Al cobrar (estado `cobrada`): genera salidas de stock (`MovimientoStock` tipo `salida_venta`), actualiza caja abierta (`MovimientoCaja`), si es CC genera deuda (`CuentaCorriente` tipo `deuda`), genera ticket/imprimible.
  - Suspensión de venta: guarda estado `suspendida`, permite recuperación por ID.
  - Anulación: transición a `anulada` con reversión de stock/caja/CC (requiere Admin/Encargado).
  - Frontend: pantalla de caja completa (estado lector, cliente, carrito, subtotal, descuentos, total, medios de pago, cobrar, suspender, ticket).
  - Tests: cobro completo, suspensión/recuperación, anulación, stock negativo bloqueado, CC automática, auditoría.
- **Dependencias**: `C-05`, `C-06`, `C-10`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Venta, §DetalleVenta, §PagoVenta
  - `knowledge-base/06_funcionalidades.md` §US-012, §US-013
  - `knowledge-base/07_flujos_principales.md` §Flujo 2: Venta con balanza SYSTEL (cobro completo)
  - `knowledge-base/05_reglas_de_negocio.md` §RN-VENT, §RN-PAGO

### [C-13] `caja-operaciones`
- **Estado**: `[~]` parcial — los modelos `Caja` y `MovimientoCaja` YA existen (tabla creada en migración 012, arrastrada por C-12 para registrar movimientos al cobrar). Falta implementar los endpoints (apertura/cierre/movimientos) y el `service.py`. El `router.py` sigue siendo stub de 3 líneas. **Bloqueante**: sin apertura de caja, C-12 no puede cobrar medios != cuenta_corriente end-to-end.
- **Scope**:
  - `POST /caja/apertura` — fecha, usuario_apertura, efectivo_inicial. Valida que no exista otra caja abierta para la empresa (v1.0, SU-03).
  - `POST /caja/cierre` — fecha_cierre, usuario_cierre, montos reales (efectivo, transferencias, tarjetas).
  - Cálculos automáticos de esperado: efectivo = inicial + ventas_efectivo + ingresos_manuales - retiros; transferencias = ventas_transferencia; tarjetas = ventas_debito + ventas_credito.
  - `POST /caja/movimientos` — retiros e ingresos manuales con descripción.
  - Diferencias: `real - esperado` por medio y `diferencia_total`. Si hay diferencia significativa, genera notificación de alerta (RN-CAJA-02).
  - Estados: `abierta`, `cerrada`. Solo una caja abierta por empresa.
  - Frontend: pantalla de caja (apertura, movimientos, cierre con comparación esperado vs real).
  - Tests: apertura única, cálculos esperados, diferencias, movimientos, notificación por diferencia.
- **Dependencias**: `C-03`, `C-12`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Caja, §MovimientoCaja
  - `knowledge-base/06_funcionalidades.md` §US-014
  - `knowledge-base/07_flujos_principales.md` §Flujo 5: Cierre de caja
  - `knowledge-base/05_reglas_de_negocio.md` §RN-CAJA

---

## FASE 5 — Finanzas y Cuentas Corrientes

> Control de la financiación a clientes y gastos operativos.

### [C-14] `cuentas-corrientes`
- **Estado**: `[~]` parcial — el modelo `CuentaCorriente` y su tabla YA existen (migración 012, arrastrada por C-12 para generar deuda al cobrar con cuenta corriente; C-12 también escribe la reversión en anulación). Falta implementar los endpoints (pagos, estado de cuenta) y el `service.py`. El `router.py` sigue siendo stub de 3 líneas.
- **Scope**:
  - Tabla `CuentaCorriente` (movimientos): `cliente_id`, `tipo` (deuda, pago), `importe`, `saldo_resultante`, `venta_id` (nullable), `fecha`.
  - Generación automática de deuda: al cobrar una venta con medio `cuenta_corriente`, se crea movimiento tipo `deuda` con importe = total de la venta (RN-CC-01, RN-PAGO-02).
  - `POST /cuentas-corrientes/:cliente_id/pagos` — registro de pagos parciales o totales, actualización de `saldo_resultante`.
  - Endpoint `GET /cuentas-corrientes/:cliente_id` — historial completo + saldo actual.
  - Endpoint `GET /cuentas-corrientes/:cliente_id/estado-cuenta` — exportable/imprimible (RN-CC-02).
  - Alertas de deudas vencidas: placeholder para futuro (requiere definir días de vencimiento, ver IN-04).
  - Frontend: grid de clientes con saldo, ficha de cuenta corriente, formulario de pago, estado de cuenta imprimible.
  - Tests: cálculo saldo, pagos parciales, deuda automática por venta, historial, aislamiento multi-tenant.
- **Dependencias**: `C-06`, `C-12`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §CuentaCorriente
  - `knowledge-base/06_funcionalidades.md` §US-015
  - `knowledge-base/05_reglas_de_negocio.md` §RN-CC, §RN-PAGO-02

### [C-15] `gastos`
- **Estado**: `[ ]` pendiente — **stub vacío** en `backend/src/modules/gasto/` (router de 3 líneas, models TODO). Solo existe `CategoriaGasto` en DB.
- **Scope**:
  - `CRUD /gastos` — fecha, categoría (enum fijo), descripción, importe, medio de pago.
  - Categorías fijas: alquiler, empleados, luz, agua, gas, internet, combustible, impuestos, mantenimiento, insumos, otros.
  - Alertas de gastos elevados: placeholder comparando contra umbral configurable en empresa (ver IN-04).
  - Frontend: grid de gastos, formulario, filtros por categoría y rango de fechas.
  - Tests: CRUD, categorías válidas, alertas placeholder, aislamiento multi-tenant.
- **Dependencias**: `C-03`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Gasto
  - `knowledge-base/06_funcionalidades.md` §US-016
  - `knowledge-base/05_reglas_de_negocio.md` §RN-GAST

---

## FASE 6 — Dashboard, Reportes y Rentabilidad

> Todo change de esta fase es de solo-lectura/aggregate. Depende de que existan datos de ventas, stock, gastos y desposte.

### [C-16] `dashboard`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Endpoint `GET /dashboard/indicadores` — ventas del día, ventas del mes, kilos vendidos, clientes atendidos, stock crítico (count), ganancia bruta, ganancia neta, gastos del mes.
  - Rankings: productos más vendidos, cortes más vendidos (requiere C-09 desposte finalizado o join con ventas).
  - Gráficos: ventas diarias (últimos 7 días), ventas mensuales (últimos 12 meses), evolución de ganancias, distribución de ventas por medio de pago.
  - Todo filtrado por `empresa_id` del usuario autenticado.
  - Frontend: pantalla principal con KPI cards, gráficos de líneas/barras/torta, tabla de rankings.
  - Tests: cálculos de agregación, filtros por empresa, performance con datos de volumen.
- **Dependencias**: `C-09`, `C-12`, `C-13`, `C-15`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-004
  - `knowledge-base/04_modelo_de_datos.md` §Venta, §MovimientoStock
  - `knowledge-base/08_arquitectura_propuesta.md` §CQRS (a evaluar para este endpoint)

### [C-17] `reportes-ventas`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Endpoint `GET /reportes/ventas` — filtros: rango de fechas, cliente.
  - Columnas: fecha, cliente, productos, kilos vendidos, subtotal, total, medio de pago, ganancia estimada.
  - Exportación: Excel (SheetJS/xlsx), PDF (PDFKit/jspdf), CSV.
  - Frontend: pantalla de reportes con filtros, preview de tabla, botones de exportación.
  - Tests: filtros, exportaciones en los 3 formatos, datos correctos, aislamiento multi-tenant.
- **Dependencias**: `C-12`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-017
  - `knowledge-base/05_reglas_de_negocio.md` §RN-REP-01 a RN-REP-03

### [C-18] `reportes-financieros`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Endpoint `GET /reportes/financieros` — indicadores: ventas, costos, gastos, utilidad bruta, utilidad neta.
  - Agrupaciones: día, semana, mes, año (parámetro `group_by`).
  - Gráficos y tablas comparativas en frontend.
  - Utilidad bruta = ventas - costos de productos vendidos. Utilidad neta = utilidad bruta - gastos operativos.
  - Tests: cálculos financieros por período, agrupaciones, aislamiento multi-tenant.
- **Dependencias**: `C-12`, `C-15`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-018
  - `knowledge-base/05_reglas_de_negocio.md` §RN-REP-04, §RN-REP-05

### [C-19] `rentabilidad`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Endpoint `GET /rentabilidad/productos` — ranking de productos por margen (mayor y menor rentabilidad).
  - Endpoint `GET /rentabilidad/cortes` — margen por corte de desposte (costo final del desposte vs precio de venta promedio).
  - Endpoint `GET /rentabilidad/general` — rentabilidad del período considerando ventas, costos y gastos.
  - Frontend: tablas de ranking, gráficos de comparación, filtros por rango de fechas.
  - Tests: cálculos de margen, rankings ordenados, períodos, aislamiento multi-tenant.
- **Dependencias**: `C-09`, `C-12`, `C-15`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-019
  - `knowledge-base/05_reglas_de_negocio.md` §RN-RENT

---

## FASE 7 — Transversal y Cierre

> Auditoría inmutable y sistema de notificaciones. Se implementa al final porque necesita que todas las demás entidades y flujos existan para registrarlas correctamente.

### [C-20] `auditoria-notificaciones`
- **Estado**: `[ ]` pendiente — **stub vacío** en `backend/src/modules/auditoria/` y `notificacion/` (routers de 3 líneas, models TODO)
- **Scope**:
  - Tabla `Auditoria` — `usuario_id`, `accion` (enum/string: CREAR_VENTA, ELIMINAR_PRODUCTO, etc.), `entidad_tipo`, `entidad_id`, `payload` (JSON snapshot), `fecha`, `hora`.
  - Middleware/interceptor global que captura operaciones relevantes y escribe en auditoría (RN-AUD-01).
  - Registros inmutables: solo inserción, nunca update ni delete (RN-AUD-02).
  - Endpoint `GET /auditoria` — listado con filtros por usuario, fecha, tipo de acción. Solo Administrador.
  - Tabla `Notificacion` — `tipo` (stock_bajo, stock_critico, deuda_vencida, gasto_elevado, diferencia_caja), `mensaje`, `leida`, `entidad_tipo`, `entidad_id`.
  - Generación automática de notificaciones:
    - Stock bajo/crítico: trigger en C-10 stock (si stock_actual <= stock_minimo).
    - Diferencia de caja: trigger en C-13 cierre de caja (si diferencia_total != 0).
    - Deuda vencida: placeholder (requiere definir días de vencimiento, ver IN-04).
    - Gasto elevado: placeholder (requiere umbral configurable, ver IN-04).
  - Frontend: panel de notificaciones (badge, toast, marcar como leída), pantalla de auditoría con filtros y exportación.
  - Tests: inmutabilidad auditoría, generación de notificaciones, marcado leído, permisos de admin, aislamiento multi-tenant.
- **Dependencias**: `C-10`, `C-12`, `C-13`, `C-14`, `C-15`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Auditoría, §Notificación
  - `knowledge-base/06_funcionalidades.md` §US-020, §US-021
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AUD, §RN-NOTIF

---

## Tabla resumen

| Change | Nombre | Fase | Governance | Dependencias | Estado |
|--------|--------|------|------------|--------------|--------|
| C-01 | foundation-setup | 1 | CRITICO | — | `[x]` |
| C-02 | auth-core | 1 | CRITICO | C-01 | `[x]` |
| C-03 | empresa-config | 1 | CRITICO | C-01 | `[x]` |
| C-04 | usuarios-rbac | 1 | CRITICO | C-02, C-03 | `[x]` |
| C-05 | productos-catalogo | 2 | CRITICO | C-03 | `[x]` |
| C-06 | clientes | 2 | MEDIO | C-03 | `[x]` |
| C-07 | proveedores | 2 | MEDIO | C-03 | `[x]` |
| C-08 | compras-media-res | 3 | ALTO | C-05, C-07 | `[x]` |
| C-09 | desposte | 3 | ALTO | C-08 | `[x]` |
| C-10 | stock-movimientos | 3 | ALTO | C-05 | `[x]` |
| C-11 | balanza-systel | 4 | ALTO | C-05 | `[x]` |
| C-12 | ventas-cobro | 4 | CRITICO | C-05, C-06, C-10 | `[x]` |
| C-13 | caja-operaciones | 4 | ALTO | C-03, C-12 | `[~]` |
| C-14 | cuentas-corrientes | 5 | ALTO | C-06, C-12 | `[~]` |
| C-15 | gastos | 5 | MEDIO | C-03 | `[ ]` |
| C-16 | dashboard | 6 | MEDIO | C-09, C-12, C-13, C-15 | `[ ]` |
| C-17 | reportes-ventas | 6 | MEDIO | C-12 | `[ ]` |
| C-18 | reportes-financieros | 6 | MEDIO | C-12, C-15 | `[ ]` |
| C-19 | rentabilidad | 6 | MEDIO | C-09, C-12, C-15 | `[ ]` |
| C-20 | auditoria-notificaciones | 7 | ALTO | C-10, C-12, C-13, C-14, C-15 | `[ ]` |

**Leyenda**: `[x]` = completado | `[~]` = parcial / con deuda técnica | `[ ]` = pendiente

---

## Decisiones de arquitectura pendientes

### `[CRITICO]` RBAC Superadmin — `DECISIONES/RBAC-SUPERADMIN-PENDIENTE.md`
- **Estado**: ✅ Implementado y archivado (`openspec/changes/archive/2026-06-18-c-rbac-superadmin/`). 5 roles, matriz sin wildcard, impersonación. **Nota**: la matriz inicial omitió `productos:delete` y `proveedores:delete` para `admin` — corregido el 2026-06-19 (ver deuda técnica #6).
- **Impacto**: C-04 (usuarios-rbac), C-03 (empresa-config), y todos los changes futuros
- **Resumen**: El modelo actual no distingue "admin del SaaS" (superadmin) de "admin de carnicería". El rol `admin` tiene `*` (wildcard). Se requiere: rol `superadmin` global (sin `empresa_id`), rol `admin` tenant-scoped, middleware RBAC actualizado, endpoint de impersonación, y panel de soporte en frontend.
- **Recomendación**: Implementar **antes de C-12 (ventas-cobro)**. Es el cimiento de seguridad del SaaS multi-tenant.

---

## Deuda técnica identificada (sincronización 2026-06-18)

| # | Problema | Severidad | Estado | Archivos afectados |
|---|----------|-----------|--------|-------------------|
| 1 | ~~Desposte sin migración DB~~ | ~~CRITICA~~ | **RESUELTO 2026-06-18** — Migración 011 creada. Tablas `desposte` y `corte_desposte` existen. | `backend/src/database/migrations/versions/000000000011_add_desposte_tables.py` |
| 2 | ~~Seed `TipoCorte` roto~~ | ~~ALTA~~ | **RESUELTO 2026-06-18** — Modelo `TipoCorte` SQLModel agregado, `Literal` renombrado a `TIPOS_CORTE_LITERAL`. Seed funciona. | `backend/src/modules/desposte/models.py` |
| 3 | **Modelo `Usuario` en `auth/models.py`** | MEDIA | Pendiente | Stub en `usuario/models.py` genera confusión. Mover o consolidar. |
| 4 | **Módulos vacíos en `main.py`** | BAJA | Pendiente | Routers stub (caja, CC, reporte, auditoria, notificacion, gasto) ensucian `/docs`. (venta ya implementado en C-12) |
| 5 | ~~Historial proveedor devuelve paginación vacía~~ | ~~BAJA~~ | **RESUELTO 2026-06-19** — Contrato definido: envelope `{items, total, skip, limit, costo_promedio_historico}` (consistente con los demás list endpoints). Test ajustado. |
| 6 | ~~Matriz RBAC sin `productos:delete`/`proveedores:delete` para admin~~ | ~~ALTA~~ | **RESUELTO 2026-06-19** — Regresión de c-rbac-superadmin: el admin no podía borrar productos/proveedores (403). Permisos agregados. | `backend/src/common/rbac.py` |
| 7 | ~~`crear/actualizar_usuario` lazy-load de `current_user.rol`~~ | ~~MEDIA~~ | **RESUELTO 2026-06-19** — `MissingGreenlet` en tests de service async. Reemplazado por `await db.get(Rol, ...)`. | `backend/src/modules/usuario/service.py` |

---

## Próximo paso recomendado

### Opción A (Recomendada): Implementar C-13 caja-operaciones
```bash
/opsx:propose c-13-caja-operaciones
```
**Por qué**: Es la dependencia que falta para que **C-12 ventas-cobro sea usable end-to-end**. Hoy el cobro exige una caja abierta (`venta/service.py`) pero no existe endpoint de apertura → no se puede cobrar efectivo/tarjeta en runtime real, solo cuenta corriente. Los modelos `Caja`/`MovimientoCaja` ya existen (migración 012); falta service + endpoints + frontend.

### Opción B: Implementar C-14 cuentas-corrientes
```bash
/opsx:propose c-14-cuentas-corrientes
```
**Por qué**: Modelo `CuentaCorriente` y la generación de deuda al cobrar ya existen (los trajo C-12). Falta el registro de pagos y el estado de cuenta. Cierra el ciclo de venta a crédito.

### Opción C: Fix deuda técnica restante
1. Consolidar modelo `Usuario` (#3)
2. Limpiar routers stub de `main.py` que ensucian `/docs` (#4)

---

> **Última sincronización**: 2026-06-19 — Estado del código auditado a fondo. C-12 ventas-cobro completo (integra stock/caja/CC con reversión). C-13 caja y C-14 CC parciales (modelos + tablas existen vía migración 012, faltan endpoints). **542 tests pasan, 0 fallan** (suite completa con testcontainers). Las 10 fallas previas eran regresiones de c-rbac-superadmin + fragilidad async + contaminación del rate limiter entre tests — resueltas, no eran de C-12.
