# Decisiones y Supuestos

## Decisiones documentadas

### DD-01 — Multi-tenancia por aislamiento lógico (row-level)
**Decisión**: Implementar multi-tenancia añadiendo `empresa_id` en todas las tablas de dominio y filtrando cada query por este campo.
**Contexto**: El sistema es SaaS multiempresa pero no se especifica el mecanismo de aislamiento.
**Alternativas consideradas**:
- Schema por empresa (más aislado, más costoso en infraestructura).
- Base de datos por empresa (máximo aislamiento, complejidad operativa alta).
**Justificación**: El aislamiento lógico es el equilibrio entre seguridad, simplicidad operativa y costo. Permite backups centralizados y consultas globales si en el futuro se requiere.
**Trade-offs aceptados**: Riesgo menor de filtración si se olvida el filtro `empresa_id` en alguna query. Mitigación: middleware centralizado o scope automático en ORM.

### DD-02 — Unidad de medida única: kilos
**Decisión**: Todo stock se administra exclusivamente en kilos.
**Contexto**: La especificación funcional lo declara explícitamente como requisito.
**Alternativas consideradas**:
- Soporte de múltiples unidades (unidad, paquete, caja).
- Conversión entre unidades.
**Justificación**: Simplifica drásticamente el modelo de datos, los cálculos de costo y las integraciones con balanza (que ya pesan en kilos).
**Trade-offs aceptados**: No se puede vender por unidad (ej: "1 chorizo") sin conversión manual o producto derivado.

### DD-03 — Lectura de balanza SYSTEL por HID/USB (teclado emulado)
**Decisión**: Capturar códigos de balanza SYSTEL mediante un campo oculto que reciba input de teclado, interpretando el string numérico completo.
**Contexto**: La especificación menciona compatibilidad con lectores USB, HID y dispositivos tipo teclado.
**Alternativas consideradas**:
- Integración por SDK propietario de SYSTEL (puede no existir para web).
- Conexión por puerto serie (Web Serial API, limitado a Chrome y permisos).
**Justificación**: La emulación de teclado es el método más universal, funciona en cualquier navegador y SO, y no requiere drivers especiales.
**Trade-offs aceptados**: El campo oculto puede capturar input no deseado si el usuario tipea accidentalmente. Mitigación: timeout de lectura y validación de longitud/formato del código.

### DD-04 — Soft delete + auditoría inmutable
**Decisión**: Prohibir eliminación física de registros transaccionales; usar baja lógica (`activo = false`) y tabla de auditoría inmutable.
**Contexto**: Se requiere trazabilidad financiera y de operaciones en un negocio de control de stock y caja.
**Alternativas consideradas**:
- Eliminación física con backup (riesgo de pérdida de trazabilidad).
- Event sourcing completo (muy poderoso pero overkill para v1.0).
**Justificación**: Cumple con RN-GLOBAL-01 y RN-GLOBAL-02 sin agregar complejidad excesiva.
**Trade-offs aceptados**: Base de datos crece indefinidamente. Mitigación: archivado de datos antiguos en tablas históricas si el volumen lo requiere.

### DD-05 — Precios por tipo de cliente (dual: público/mayorista)
**Decisión**: Cada producto almacena dos precios fijos: público y mayorista. El precio especial no se detalla en v1.0.
**Contexto**: Existen 3 tipos de cliente pero solo 2 precios están definidos con claridad.
**Alternativas consideradas**:
- Tabla de listas de precios por cliente (más flexible, más compleja).
- Precio único con descuentos por cliente.
**Justificación**: La especificación funcional describe explícitamente precio público y precio mayorista.
**Trade-offs aceptados**: El tipo "Especial" queda sin comportamiento definido en v1.0. Se asume que usa precio público o requiere definición adicional.

---

## Supuestos inferidos

### SU-01 — Moneda única local
**Supuesto**: El sistema opera en una única moneda (pesos argentinos) y no requiere conversión multimoneda.
**Origen**: La especificación funcional no menciona moneda ni conversión, y el contexto es una carnicería argentina (CUIT, términos locales).
**Riesgo si es falso**: Si el negocio opera en frontera o con proveedores extranjeros, se requiere refactorización del modelo de datos.
**Cómo validar**: Confirmar con el Product Owner si existe operación en otras monedas o si se planea expansión.

### SU-02 — Conectividad constante
**Supuesto**: La aplicación requiere conexión a internet en todo momento. No hay modo offline.
**Origen**: Especificación de SaaS web responsive, sin mención de sincronización offline.
**Riesgo si es falso**: Si la carnicería tiene cortes de internet frecuentes, la operación se detiene.
**Cómo validar**: Confirmar calidad de conectividad en las instalaciones objetivo. Evaluar Service Workers para v2.0.

### SU-03 — Un solo punto de venta (caja) por empresa en simultáneo
**Supuesto**: En v1.0, cada empresa opera con una única caja abierta a la vez.
**Origen**: La especificación describe "caja" en singular y no menciona múltiples puntos de venta.
**Riesgo si es falso**: Si una carnicería tiene más de un mostrador con caja, el sistema colapsa.
**Cómo validar**: Preguntar al Product Owner el escenario de múltiples cajas simultáneas.

### SU-04 — Impresora de tickets conectada localmente
**Supuesto**: La impresión de tickets se realiza desde el navegador del dispositivo local (impresora térmica conectada por USB/Bluetooth/Red) usando capacidades nativas del SO o un servicio de impresión local.
**Origen**: Se menciona "imprimir ticket" pero no se especifica integración con impresora fiscal ni servicio cloud de impresión.
**Riesgo si es falso**: Si se requiere impresora fiscal homologada (Argentina), la arquitectura cambia radicalmente.
**Cómo validar**: Confirmar si se requiere impresora fiscal AFIP o ticket no fiscal simple.

### SU-05 — Email como único canal de notificación
**Supuesto**: Las notificaciones del sistema se visualizan en la UI (badge/toast) pero el envío por email de alertas no está requerido en v1.0.
**Origen**: Solo se menciona recuperación de contraseña por email; las demás notificaciones se describen como "alertas" sin canal específico.
**Riesgo si es falso**: Si el usuario espera emails de alerta de stock, se requiere integración adicional.
**Cómo validar**: Definir roadmap de canales de notificación (email, WhatsApp, push).

### SU-06 — QUENDRA exporta Excel con formato predecible
**Supuesto**: La importación desde QUENDRA funciona con un formato de Excel estándar y predecible (columnas fijas).
**Origen**: Se menciona "archivos Excel exportados por QUENDRA" sin detalle de formato.
**Riesgo si es falso**: Si el formato varía o no es estándar, la importación fallará constantemente.
**Cómo validar**: Solicitar muestras reales de archivos Excel de QUENDRA para mapear columnas.

### SU-07 — Código SYSTEL de 13 dígitos (formato EAN-13 like)
**Supuesto**: El ejemplo `2000270048052` es un código de 13 dígitos donde las posiciones 2-6 son PLU y las posiciones 7-12 son peso con 2 decimales implícitos.
**Origen**: El documento da un solo ejemplo sin especificar el protocolo de SYSTEL.
**Riesgo si es falso**: Si el formato varía (otra longitud, otras posiciones), la lectura de balanza falla.
**Cómo validar**: Confirmar modelo exacto de balanza SYSTEL y protocolo de etiquetas con el proveedor de hardware.

### SU-08 — Sin requisitos fiscales de facturación electrónica en v1.0
**Supuesto**: El sistema no requiere integración con AFIP (Argentina) ni emisión de factura electrónica en la versión inicial.
**Origen**: No se menciona facturación electrónica, CAE, ni obligaciones fiscales en la especificación.
**Riesgo si es falso**: Si es requerido, se necesita integración con AFIP (WSFEv1) que es compleja y debe planificarse desde el inicio.
**Cómo validar**: Consultar con un contador o advisor fiscal del proyecto sobre obligaciones de facturación del rubro carnicería.
