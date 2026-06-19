# Visión y Objetivos

## Propósito del sistema

Desarrollar una aplicación web SaaS denominada **BASILE**, especializada en la gestión integral de carnicerías. La plataforma permite administrar ventas, stock, compras, desposte, clientes, proveedores, cuentas corrientes, caja, gastos, reportes y rentabilidad, todo dentro de una única plataforma moderna, multiempresa y multiusuario.

## Objetivos por actor

| Actor | Objetivo principal | Objetivos secundarios |
|-------|-------------------|----------------------|
| Administrador | Control total del negocio | Configuración de empresa, gestión de usuarios, reportes financieros, auditoría |
| Encargado | Operación diaria + reportes | Gestión de stock, compras, desposte, visualización de reportes |
| Cajero | Cobro y atención al cliente | Registro de ventas, gestión de clientes, operaciones de caja |
| Vendedor | Realizar ventas únicamente | Uso de balanza SYSTEL, cobro con medios de pago |
| Cliente (implícito) | Compra rápida y transparente | Consulta de cuenta corriente, historial de compras |
| Proveedor (implícito) | Registrar compras de media res | Historial de compras, trazabilidad de pagos |

## Alcance v1.0

El sistema **SÍ** incluye en esta versión:

- SaaS multiempresa y multiusuario con aislamiento total de datos por empresa.
- Autenticación por email/contraseña con recuperación por correo.
- Dashboard principal con indicadores de ventas, stock, ganancias y rankings.
- Gestión completa de productos (PLU, categorías, precios público/mayorista, stock, importación desde Excel de QUENDRA).
- Gestión de clientes con tipificación (público general, mayorista, especial) y control de cuenta corriente.
- Gestión de proveedores e historial de compras.
- Compras de media res con cálculo automático de costo por kilo y costo promedio histórico.
- Gestión de desposte con soporte para 12 cortes, cálculo de rendimiento, merma y costo final.
- Stock administrado exclusivamente por kilos, con entradas (compras/desposte), salidas (ventas/ajustes), kardex, historial y alertas de stock mínimo.
- Ventas integradas con balanzas SYSTEL (lectura de etiquetas por USB/HID/teclado), carrito, descuentos, múltiples medios de pago.
- Pantalla de caja con apertura, cierre, movimientos y validación de diferencias.
- Gestión de gastos categorizados.
- Cuentas corrientes con generación de deuda, registro de pagos y estado de cuenta.
- Reportes de ventas exportables a Excel, PDF y CSV.
- Reportes financieros con indicadores de utilidad bruta y neta agrupados por día, semana, mes y año.
- Rentabilidad por producto, por corte y general.
- Auditoría de usuario, acción, fecha y hora.
- Notificaciones de stock bajo/crítico, deudas vencidas, gastos elevados y diferencias de caja.
- Diseño responsive para desktop, tablet y mobile.

## Fuera de alcance

El sistema **NO** incluye:

- Aplicación móvil nativa (iOS/Android).
- E-commerce público o tienda online para consumidores finales.
- Facturación electrónica / integración con AFIP (Argentina).
- Gestión de nómina/sueldos de empleados.
- Integración con otras balanzas que no sean SYSTEL.
- Conectividad en modo offline.
- Multimoneda (asume moneda local única).
- Gestión de sucursales físicas (aunque es multiempresa, no se menciona sucursal por empresa).

## Métricas de éxito

- Reducción del tiempo de cobro en caja (gracias a integración con balanza).
- Visibilidad en tiempo real de stock crítico y rentabilidad.
- Control financiero centralizado: ventas, costos, gastos y utilidad neta en un solo lugar.
- Adopción del 100% de los usuarios asignados por empresa.

> **Nota**: Las métricas específicas cuantitativas no fueron definidas en la fuente. Recomendamos acordar KPIs con el Product Owner.
