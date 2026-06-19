# Preguntas Abiertas

## Inconsistencias detectadas

### IN-01 — Stack tecnológico no especificado
**Documento dice**: Desarrollar una aplicación web SaaS moderna, multiempresa y multiusuario.
**Falta**: No se menciona stack frontend, backend, base de datos, lenguaje de programación, framework ni infraestructura de hosting.
**Impacto**: Bloquea la estimación técnica, la definición de arquitectura de directorios y la configuración de CI/CD.
**Resolución propuesta**: El equipo técnico debe proponer 2-3 stacks viables (ej: React + Node.js/Express + PostgreSQL, Angular + Java/Spring + MySQL, Next.js + tRPC + PostgreSQL) y el Product Owner debe aprobar uno.

### IN-02 — Precio para clientes "Especial" no definido
**Documento dice**: Existen 3 tipos de cliente: Público General, Mayorista y Especial.
**Falta**: Solo se definen precio público y precio mayorista. No se especifica qué precio aplica para "Especial" ni cómo se configura.
**Impacto**: La US-013 (cobrar venta) tiene un comportamiento ambiguo para clientes tipo Especial.
**Resolución propuesta**: Definir si "Especial" usa precio público por defecto, o si requiere precio personalizado por cliente (tabla adicional `precios_especiales`).

### IN-03 — Límite de cuenta corriente: ¿alerta o bloqueo?
**Documento dice**: Cliente tiene "Límite de cuenta corriente" y "Saldo actual".
**Falta**: No se especifica si al exceder el límite el sistema bloquea la venta, alerta al cajero, o solo notifica al administrador.
**Impacto**: Afecta la experiencia de caja y la lógica de validación en el backend.
**Resolución propuesta**: Definir comportamiento por defecto (ej: alerta + requiere override de Admin/Encargado para continuar).

### IN-04 — Umbral de alertas no definido
**Documento dice**: El sistema debe alertar por "stock crítico", "gastos elevados" y "deudas vencidas".
**Falta**: No se definen los umb numéricos ni plazos para estas alertas.
**Impacto**: Las notificaciones no pueden implementarse sin parámetros de referencia.
**Resolución propuesta**: Agregar campos configurables en la empresa: `dias_vencimiento_cc`, `porcentaje_umbral_gasto`, `factor_stock_critico`.

### IN-05 — Múltiples medios de pago por venta (split payment)
**Documento dice**: Se listan 5 medios de pago pero no se especifica si una venta puede dividirse entre varios.
**Falta**: Claridad sobre si se permite pagar parte en efectivo y parte en transferencia, por ejemplo.
**Impacto**: Modelo de datos de `PagoVenta` (1:1 o 1:N con Venta) y lógica de cierre de caja.
**Resolución propuesta**: Decidir en v1.0: ¿un solo medio de pago por venta? Si se permite split, el modelo debe soportar múltiples `PagoVenta` por venta.

### IN-06 — ¿Una o varias cajas simultáneas?
**Documento dice**: "Gestión de Caja" en singular (apertura, cierre, movimientos).
**Falta**: No se menciona si una empresa puede tener múltiples cajas abiertas al mismo tiempo (ej: dos mostradores).
**Impacto**: El modelo de datos de Caja debe soportar `caja_numero` o similar si hay múltiples puntos.
**Resolución propuesta**: Confirmar con el Product Owner. Para v1.0, asumir una sola caja por empresa.

### IN-07 — Impresora fiscal vs ticket no fiscal
**Documento dice**: "Imprimir ticket" como acción de la pantalla de caja.
**Falta**: No se especifica si es ticket no fiscal (comprobante simple) o factura/ ticket fiscal homologado (exigido por AFIP en Argentina para ciertos rubros).
**Impacto**: Si requiere fiscalidad, se necesita integración con impresora fiscal y posiblemente con AFIP.
**Resolución propuesta**: Consultar obligación fiscal del rubro carnicería en Argentina y decidir si la fiscalidad entra en v1.0 o v2.0.

### IN-08 — Formato exacto de etiqueta SYSTEL
**Documento dice**: Ejemplo `2000270048052`.
**Falta**: No se especifica la estructura del código (longitud total, posiciones de PLU, posiciones de peso, decimales, dígito verificador).
**Impacto**: El parseo de balanza puede fallar con otros modelos de SYSTEL o configuraciones distintas.
**Resolución propuesta**: Obtener manual del modelo exacto de balanza SYSTEL y confirmar protocolo.

### IN-09 — Formato de Excel de QUENDRA
**Documento dice**: "Importar productos desde archivos Excel exportados por QUENDRA".
**Falta**: No se proporciona muestra del archivo ni mapeo de columnas esperado.
**Impacto**: El parser de importación no puede desarrollarse sin conocer el formato origen.
**Resolución propuesta**: Solicitar al cliente o Product Owner un archivo de ejemplo real de QUENDRA.

### IN-10 — Método de valorización de stock
**Documento dice**: "Valorización" como funcionalidad de stock.
**Falta**: No se especifica si se usa PEPS (FIFO), UEPS (LIFO), promedio ponderado o costo identificado.
**Impacto**: Cálculo de costo de goods sold, rentabilidad y reportes financieros.
**Resolución propuesta**: Definir método de valorización por defecto. Recomendado: costo promedio ponderado por su simplicidad en carnicería.

---

## Preguntas abiertas (priorizadas)

| Prioridad | Pregunta | Bloquea | Decisor |
|-----------|----------|---------|---------|
| Alta | ¿Cuál es el stack tecnológico aprobado para BASILE? | Sprint 0 / estimación | Tech Lead + Product Owner |
| Alta | ¿El sistema requiere facturación electrónica / impresora fiscal AFIP en v1.0? | Diseño de caja y ventas | Product Owner + Asesor fiscal |
| Alta | ¿Una venta puede dividirse entre múltiples medios de pago (split)? | Modelo de PagoVenta y caja | Product Owner |
| Alta | ¿Qué precio aplica para clientes tipo "Especial" y cómo se configura? | Lógica de ventas | Product Owner |
| Media | ¿El negocio permite múltiples cajas abiertas simultáneamente por empresa? | Modelo de Caja | Product Owner |
| Media | ¿Cuáles son los umbrales exactos para alertas de stock crítico, gastos elevados y deudas vencidas? | Configuración de empresa y notificaciones | Product Owner |
| Media | ¿Se requiere envío de alertas por email o solo notificaciones en la UI? | Integraciones y costo operativo | Product Owner |
| Media | ¿Cuál es el formato exacto de etiquetas de la balanza SYSTEL (modelo, protocolo)? | Integración de hardware | Tech Lead + Cliente |
| Media | ¿Se puede obtener un archivo Excel de muestra exportado por QUENDRA? | Módulo de importación | Cliente / Product Owner |
| Baja | ¿Existe necesidad de modo offline o sincronización para cortes de internet? | Arquitectura y stack | Product Owner |
| Baja | ¿Se planea operación en moneda extranjera o múltiples monedas? | Modelo de datos financiero | Product Owner |
| Baja | ¿El tipo de cliente "Especial" permite descuentos porcentuales fijos o precios unitarios personalizados por producto? | Modelo de precios | Product Owner |
