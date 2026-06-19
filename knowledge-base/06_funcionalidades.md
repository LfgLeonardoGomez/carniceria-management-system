# Funcionalidades

Organizadas por **épica** y luego por **historia de usuario** (formato US-NNN).

---

## Épica 1: Autenticación y Seguridad

### US-001 — Iniciar sesión
**Como** usuario registrado  
**Quiero** iniciar sesión con email y contraseña  
**Para** acceder a las funcionalidades de BASILE correspondientes a mi rol.

**Criterios de aceptación**:
- [ ] CA-1: El sistema valida email y contraseña.
- [ ] CA-2: Si las credenciales son inválidas, se muestra un mensaje de error genérico (sin revelar cuál campo falló).
- [ ] CA-3: Tras login exitoso, el usuario accede solo a los datos de su empresa.
- [ ] CA-4: El sistema redirige al Dashboard o a la pantalla principal según el rol.

**Reglas relacionadas**: RN-AU-01, RN-SEG-01

### US-002 — Recuperar contraseña
**Como** usuario  
**Quiero** solicitar recuperación de contraseña por email  
**Para** restablecer mi acceso sin intervención de un administrador.

**Criterios de aceptación**:
- [ ] CA-1: El usuario ingresa su email registrado.
- [ ] CA-2: El sistema envía un email con enlace seguro de un solo uso.
- [ ] CA-3: El enlace expira después de un tiempo configurable (ej: 1 hora).
- [ ] CA-4: El usuario puede ingresar una nueva contraseña válida.

**Reglas relacionadas**: RN-AU-02

---

## Épica 2: Gestión de Empresa

### US-003 — Configurar datos de empresa
**Como** Administrador  
**Quiero** registrar y editar los datos de mi carnicería  
**Para** personalizar la plataforma y cumplir con requisitos fiscales.

**Criterios de aceptación**:
- [ ] CA-1: Campos obligatorios: nombre comercial, razón social, CUIT, domicilio, teléfono, email.
- [ ] CA-2: Puedo subir un logo.
- [ ] CA-3: Puedo configurar datos fiscales y parámetros operativos.
- [ ] CA-4: Los datos son visibles en reportes y tickets.

**Reglas relacionadas**: RN-SEG-01

---

## Épica 3: Dashboard

### US-004 — Visualizar indicadores clave
**Como** cualquier usuario autenticado  
**Quiero** ver un dashboard con indicadores clave  
**Para** tomar decisiones rápidas basadas en datos actualizados.

**Criterios de aceptación**:
- [ ] CA-1: Muestra: ventas del día, ventas del mes, kilos vendidos, clientes atendidos, stock crítico, ganancia bruta, ganancia neta, gastos del mes.
- [ ] CA-2: Muestra rankings: productos más vendidos, cortes más vendidos.
- [ ] CA-3: Muestra gráficos: ventas diarias, ventas mensuales, evolución de ganancias, distribución de ventas.
- [ ] CA-4: Los datos se filtran automáticamente por la empresa del usuario.

**Reglas relacionadas**: RN-SEG-01

---

## Épica 4: Productos

### US-005 — Administrar productos
**Como** Administrador o Encargado  
**Quiero** dar de alta, modificar, dar de baja y buscar productos  
**Para** mantener el catálogo actualizado.

**Criterios de aceptación**:
- [ ] CA-1: Campos: PLU, nombre, categoría, precio público, precio mayorista, costo por kilo, margen, stock actual, activo.
- [ ] CA-2: Búsqueda rápida por PLU o nombre.
- [ ] CA-3: No se permite PLU duplicado dentro de la empresa.
- [ ] CA-4: El margen puede calcularse automáticamente.

**Reglas relacionadas**: RN-PROD-01, RN-PROD-02, RN-PROD-03, RN-PROD-05

### US-006 — Importar productos desde Excel
**Como** Administrador  
**Quiero** importar productos desde un archivo Excel exportado por QUENDRA  
**Para** migrar mi catálogo existente sin carga manual.

**Criterios de aceptación**:
- [ ] CA-1: El sistema acepta archivos `.xlsx`.
- [ ] CA-2: Mapea correctamente PLU, nombre, categoría y precios.
- [ ] CA-3: Muestra vista previa antes de confirmar la importación.
- [ ] CA-4: Detecta y reporta duplicados o errores de formato.

**Reglas relacionadas**: RN-PROD-04

---

## Épica 5: Clientes

### US-007 — Administrar clientes
**Como** Cajero o Administrador  
**Quiero** registrar y gestionar clientes  
**Para** fidelizar, ofrecer precios diferenciados y controlar cuentas corrientes.

**Criterios de aceptación**:
- [ ] CA-1: Campos: nombre, apellido, razón social, CUIT, teléfono, email, dirección, tipo de cliente, límite de cuenta corriente.
- [ ] CA-2: Tipos: Público General, Mayorista, Especial.
- [ ] CA-3: Muestra historial completo de compras.
- [ ] CA-4: Muestra saldo actual de cuenta corriente.

**Reglas relacionadas**: RN-CLI-01, RN-CLI-02

---

## Épica 6: Proveedores

### US-008 — Administrar proveedores
**Como** Administrador o Encargado  
**Quiero** registrar proveedores y ver su historial de compras  
**Para** controlar la cadena de abastecimiento.

**Criterios de aceptación**:
- [ ] CA-1: Campos: nombre, CUIT, teléfono, email, dirección.
- [ ] CA-2: Muestra historial completo de compras asociadas.
- [ ] CA-3: Los proveedores son independientes por empresa.

**Reglas relacionadas**: RN-PROV-01, RN-PROV-02

---

## Épica 7: Compras y Desposte

### US-009 — Registrar compra de media res
**Como** Encargado o Administrador  
**Quiero** registrar compras de media res  
**Para** controlar costos y habilitar el desposte.

**Criterios de aceptación**:
- [ ] CA-1: Campos: fecha, proveedor, cantidad de medias reses, peso total, costo total, observaciones.
- [ ] CA-2: Calcula automáticamente costo por kilo.
- [ ] CA-3: Actualiza costo promedio histórico.
- [ ] CA-4: Genera entrada de stock de media res (si aplica) o queda disponible para desposte.

**Reglas relacionadas**: RN-COMP-01, RN-COMP-02, RN-COMP-03

### US-010 — Realizar desposte
**Como** Encargado o Administrador  
**Quiero** despostar una media res en cortes  
**Para** generar stock de productos vendibles con costos asignados.

**Criterios de aceptación**:
- [ ] CA-1: Selecciona compra de media res origen.
- [ ] CA-2: Registra fecha y operador.
- [ ] CA-3: Soporta 12 cortes: Asado, Vacío, Nalga, Cuadril, Peceto, Bola de lomo, Lomo, Matambre, Costilla, Osobuco, Molida, Otros.
- [ ] CA-4: Por corte: kilos obtenidos, porcentaje de rendimiento, costo asignado, costo final por kilo.
- [ ] CA-5: Calcula automáticamente rendimiento total y merma.
- [ ] CA-6: Al finalizar, genera stock automáticamente para cada corte.

**Reglas relacionadas**: RN-DESP-01 a RN-DESP-07

---

## Épica 8: Stock

### US-011 — Consultar stock y movimientos
**Como** Encargado o Administrador  
**Quiero** ver el stock actual, historial de movimientos (kardex) y valorización  
**Para** evitar faltantes y tomar decisiones de compra.

**Criterios de aceptación**:
- [ ] CA-1: Todo en kilos.
- [ ] CA-2: Entradas por compra y desposte. Salidas por venta y ajustes.
- [ ] CA-3: Kardex con fecha, tipo, cantidad y stock resultante.
- [ ] CA-4: Alertas de stock mínimo.
- [ ] CA-5: No permite stock negativo.

**Reglas relacionadas**: RN-STOCK-01 a RN-STOCK-07

---

## Épica 9: Ventas y Caja

### US-012 — Leer balanza SYSTEL
**Como** Cajero o Vendedor  
**Quiero** que el sistema lea automáticamente las etiquetas de la balanza SYSTEL  
**Para** agregar productos al carrito sin tipear manualmente.

**Criterios de aceptación**:
- [ ] CA-1: Compatible con lectores USB, HID y dispositivos tipo teclado.
- [ ] CA-2: Interpreta código de etiqueta (ej: `2000270048052`), detecta PLU y peso.
- [ ] CA-3: Busca producto por PLU y calcula importe.
- [ ] CA-4: Agrega automáticamente al carrito.
- [ ] CA-5: Existe campo oculto para lectura rápida sin perder foco de la UI.

**Reglas relacionadas**: RN-VENT-01 a RN-VENT-04

### US-013 — Cobrar venta
**Como** Cajero o Vendedor  
**Quiero** cobrar una venta con múltiples medios de pago, descuentos e impresión de ticket  
**Para** completar la transacción y entregar comprobante al cliente.

**Criterios de aceptación**:
- [ ] CA-1: Muestra estado del lector, cliente, tipo de cliente, carrito, subtotal, descuentos y total.
- [ ] CA-2: Medios de pago: Efectivo, Transferencia, Débito, Crédito, Cuenta Corriente.
- [ ] CA-3: Selecciona precio automáticamente según tipo de cliente.
- [ ] CA-4: Permite suspender venta y recuperarla.
- [ ] CA-5: Permite imprimir ticket.
- [ ] CA-6: Al cobrar, actualiza stock, caja y cuenta corriente (si aplica).

**Reglas relacionadas**: RN-VENT-05 a RN-VENT-08, RN-PAGO-01, RN-PAGO-02

### US-014 — Operar caja (apertura y cierre)
**Como** Cajero, Encargado o Administrador  
**Quiero** abrir y cerrar caja, registrando movimientos  
**Para** controlar el efectivo y otros medios de pago.

**Criterios de aceptación**:
- [ ] CA-1: Apertura con monto inicial.
- [ ] CA-2: Registro de movimientos: entradas por venta, retiros, ingresos manuales.
- [ ] CA-3: Control de efectivo, transferencias y tarjetas.
- [ ] CA-4: Al cierre, muestra diferencias entre esperado y real.
- [ ] CA-5: Solo una caja abierta por empresa al mismo tiempo (a definir).

**Reglas relacionadas**: RN-CAJA-01 a RN-CAJA-04

---

## Épica 10: Cuentas Corrientes

### US-015 — Gestionar cuenta corriente de cliente
**Como** Administrador o Cajero  
**Quiero** generar deudas, registrar pagos y consultar historial/saldo  
**Para** controlar la financiación que ofrezco a mis clientes.

**Criterios de aceptación**:
- [ ] CA-1: Una venta con pago "Cuenta Corriente" genera deuda automáticamente.
- [ ] CA-2: Puedo registrar pagos parciales o totales.
- [ ] CA-3: Consultar historial completo y saldo actual.
- [ ] CA-4: Estado de cuenta por cliente exportable/imprimible.
- [ ] CA-5: Alertas de deudas vencidas.

**Reglas relacionadas**: RN-CC-01, RN-CC-02, RN-CC-03

---

## Épica 11: Gastos

### US-016 — Registrar gastos
**Como** Administrador o Encargado  
**Quiero** registrar los gastos operativos categorizados  
**Para** controlar la utilidad neta del negocio.

**Criterios de aceptación**:
- [ ] CA-1: Campos: fecha, categoría (Alquiler, Empleados, Luz, Agua, Gas, Internet, Combustible, Impuestos, Mantenimiento, Insumos, Otros), descripción, importe, medio de pago.
- [ ] CA-2: Los gastos son independientes por empresa.
- [ ] CA-3: Alertas de gastos elevados (umbral a definir).

**Reglas relacionadas**: RN-GAST-01, RN-GAST-02, RN-GAST-03

---

## Épica 12: Reportes y Rentabilidad

### US-017 — Exportar reportes de ventas
**Como** Administrador o Encargado  
**Quiero** exportar reportes de ventas filtrados  
**Para** análisis externo o presentación contable.

**Criterios de aceptación**:
- [ ] CA-1: Filtros: rango de fechas, cliente.
- [ ] CA-2: Formatos: Excel, PDF, CSV.
- [ ] CA-3: Columnas: fecha, cliente, productos, kilos vendidos, subtotal, total, medio de pago, ganancia estimada.
- [ ] CA-4: Datos filtrados por empresa.

**Reglas relacionadas**: RN-REP-01, RN-REP-02, RN-REP-03

### US-018 — Visualizar reportes financieros
**Como** Administrador  
**Quiero** ver indicadores financieros agrupados temporalmente  
**Para** evaluar la salud económica del negocio.

**Criterios de aceptación**:
- [ ] CA-1: Indicadores: ventas, costos, gastos, utilidad bruta, utilidad neta.
- [ ] CA-2: Agrupaciones: día, semana, mes, año.
- [ ] CA-3: Gráficos y tablas comparativas.
- [ ] CA-4: Datos filtrados por empresa.

**Reglas relacionadas**: RN-REP-04, RN-REP-05

### US-019 — Analizar rentabilidad
**Como** Administrador  
**Quiero** ver rentabilidad por producto, por corte y general  
**Para** ajustar precios y enfocarme en lo más rentable.

**Criterios de aceptación**:
- [ ] CA-1: Ranking de productos más rentables (mayor margen).
- [ ] CA-2: Ranking de productos menos rentables.
- [ ] CA-3: Margen por corte de desposte.
- [ ] CA-4: Rentabilidad general del período.

**Reglas relacionadas**: RN-RENT-01, RN-RENT-02, RN-RENT-03

---

## Épica 13: Auditoría y Notificaciones

### US-020 — Consultar auditoría
**Como** Administrador  
**Quiero** ver un registro de todas las acciones realizadas por los usuarios  
**Para** detectar errores o fraudes.

**Criterios de aceptación**:
- [ ] CA-1: Registra: usuario, acción, fecha, hora.
- [ ] CA-2: Registros inmutables.
- [ ] CA-3: Filtros por usuario, fecha y tipo de acción.

**Reglas relacionadas**: RN-AUD-01, RN-AUD-02

### US-021 — Recibir notificaciones
**Como** cualquier usuario  
**Quiero** recibir alertas del sistema  
**Para** reaccionar ante situaciones que requieren atención.

**Criterios de aceptación**:
- [ ] CA-1: Alertas de stock bajo y crítico.
- [ ] CA-2: Alertas de deudas vencidas en cuenta corriente.
- [ ] CA-3: Alertas de gastos elevados.
- [ ] CA-4: Alertas de diferencias en caja.
- [ ] CA-5: Las notificaciones se visualizan en la UI y pueden marcarse como leídas.

**Reglas relacionadas**: RN-NOTIF-01 a RN-NOTIF-05
