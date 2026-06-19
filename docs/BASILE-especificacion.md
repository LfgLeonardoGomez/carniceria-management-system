# BASILE - Especificación Funcional del Sistema

## 1. Descripción General

### Objetivo

Desarrollar una aplicación web SaaS denominada **BASILE**, especializada en la gestión integral de carnicerías.

La plataforma deberá permitir administrar:

* Ventas
* Stock
* Compras
* Desposte
* Clientes
* Proveedores
* Cuentas corrientes
* Caja
* Gastos
* Reportes
* Rentabilidad

Todo dentro de una única plataforma moderna, multiempresa y multiusuario.

---

## 2. Características Generales

### Tipo de aplicación

* SaaS
* Multiempresa
* Multiusuario
* Responsive

### Dispositivos soportados

* Desktop
* Tablet
* Mobile

### Requisitos de UX

* Interfaz moderna
* Navegación intuitiva
* Carga rápida
* Diseño ERP profesional

### Restricciones

No mostrar:

* Base44
* Frameworks utilizados
* Herramientas de desarrollo
* Branding de terceros

---

# 3. Arquitectura Multiempresa

Cada empresa debe tener información aislada.

## Entidades independientes por empresa

* Productos
* Clientes
* Proveedores
* Compras
* Desposte
* Stock
* Ventas
* Caja
* Gastos
* Reportes
* Usuarios

### Regla de negocio

Una empresa nunca debe visualizar información perteneciente a otra empresa.

---

# 4. Autenticación y Seguridad

## Login

Campos:

* Email
* Contraseña

## Recuperación de contraseña

* Recuperación mediante correo electrónico.

---

## Roles

### Administrador

Permisos:

* Acceso total.

### Encargado

Permisos:

* Operación diaria.
* Reportes.

### Cajero

Permisos:

* Ventas.
* Clientes.

### Vendedor

Permisos:

* Ventas únicamente.

---

# 5. Gestión de Empresas

## Datos de Empresa

### Información General

* Nombre comercial
* Razón social
* CUIT
* Domicilio
* Teléfono
* Email
* Logo

### Configuración

* Datos fiscales
* Configuración general
* Parámetros operativos

---

# 6. Dashboard Principal

## Indicadores

Mostrar:

* Ventas del día
* Ventas del mes
* Kilos vendidos
* Clientes atendidos
* Stock crítico
* Ganancia bruta
* Ganancia neta
* Gastos del mes

---

## Rankings

Mostrar:

* Productos más vendidos
* Cortes más vendidos

---

## Gráficos

Mostrar:

* Ventas diarias
* Ventas mensuales
* Evolución de ganancias
* Distribución de ventas

---

# 7. Gestión de Productos

## Datos del Producto

* PLU
* Nombre
* Categoría
* Precio público
* Precio mayorista
* Costo por kilo
* Margen
* Stock actual
* Activo

---

## Funcionalidades

* Alta
* Baja
* Modificación
* Búsqueda rápida

---

## Importación

Permitir importar productos desde archivos Excel exportados por QUENDRA.

---

# 8. Gestión de Clientes

## Datos

* Nombre
* Apellido
* Razón social
* CUIT
* Teléfono
* Email
* Dirección
* Tipo de cliente
* Límite de cuenta corriente
* Saldo actual

---

## Tipos de Cliente

### Público General

Utiliza precio público.

### Mayorista

Utiliza precio mayorista.

### Especial

Permite reglas personalizadas.

---

## Funcionalidades

* Historial completo de compras.
* Gestión de cuenta corriente.

---

# 9. Gestión de Proveedores

## Datos

* Nombre
* CUIT
* Teléfono
* Email
* Dirección

---

## Funcionalidades

* Historial completo de compras.

---

# 10. Compras de Media Res

## Datos

* Fecha
* Proveedor
* Cantidad de medias reses
* Peso total
* Costo total
* Observaciones

---

## Cálculos Automáticos

### Costo por kilo

Costo total / Peso total

### Costo promedio

Promedio histórico actualizado.

---

# 11. Gestión de Desposte

## Datos Generales

* Media res utilizada
* Fecha
* Operador

---

## Cortes Soportados

* Asado
* Vacío
* Nalga
* Cuadril
* Peceto
* Bola de lomo
* Lomo
* Matambre
* Costilla
* Osobuco
* Molida
* Otros

---

## Datos por Corte

* Kilos obtenidos
* Porcentaje de rendimiento
* Costo asignado

---

## Cálculos

### Rendimiento total

Suma de kilos obtenidos.

### Merma

Peso original - kilos obtenidos.

### Costo final por kilo

Costo asignado / kilos obtenidos.

---

## Resultado

Generar stock automáticamente.

---

# 12. Gestión de Stock

## Unidad de Medida

Todo el stock debe administrarse por kilos.

---

## Entradas

* Compras
* Desposte

---

## Salidas

* Ventas
* Ajustes

---

## Funcionalidades

* Kardex
* Historial de movimientos
* Valorización
* Alertas de stock mínimo

---

# 13. Gestión de Ventas

## Integración con Balanzas SYSTEL

La aplicación debe interpretar etiquetas emitidas por balanzas SYSTEL.

Ejemplo:

2000270048052

---

## Funcionalidad

Debe:

1. Detectar PLU.
2. Detectar peso.
3. Buscar producto.
4. Calcular importe.
5. Agregar automáticamente al carrito.

---

## Compatibilidad

Compatible con:

* Lectores USB
* Lectores HID
* Dispositivos que funcionan como teclado

---

## Captura

Debe existir un campo oculto para lectura rápida de códigos.

---

# 14. Pantalla de Caja

## Información Visible

* Estado del lector
* Cliente
* Tipo de cliente
* Carrito
* Subtotal
* Descuentos
* Total

---

## Medios de Pago

* Efectivo
* Transferencia
* Débito
* Crédito
* Cuenta corriente

---

## Acciones

* Suspender venta
* Imprimir ticket
* Cobrar
* Finalizar venta

---

# 15. Gestión de Precios

## Precio Público

Utilizado para consumidores finales.

---

## Precio Mayorista

Utilizado para clientes mayoristas.

---

## Regla de Negocio

Seleccionar automáticamente el precio según el tipo de cliente.

---

# 16. Cuentas Corrientes

## Funcionalidades

* Generar deuda
* Registrar pagos
* Consultar historial
* Consultar saldo

---

## Reportes

* Estado de cuenta por cliente.

---

# 17. Gestión de Gastos

## Categorías

* Alquiler
* Empleados
* Luz
* Agua
* Gas
* Internet
* Combustible
* Impuestos
* Mantenimiento
* Insumos
* Otros

---

## Datos

* Fecha
* Categoría
* Descripción
* Importe
* Medio de pago

---

# 18. Gestión de Caja

## Operaciones

* Apertura
* Cierre
* Movimientos

---

## Control

* Efectivo
* Transferencias
* Tarjetas

---

## Validaciones

Mostrar diferencias entre:

* Caja esperada
* Caja real

---

# 19. Reportes

## Exportación de Ventas

### Filtros

* Rango de fechas
* Cliente

### Formatos

* Excel
* PDF
* CSV

### Datos incluidos

* Fecha
* Cliente
* Productos
* Kilos vendidos
* Subtotal
* Total
* Medio de pago
* Ganancia estimada

---

# 20. Reportes Financieros

## Indicadores

* Ventas
* Costos
* Gastos
* Utilidad bruta
* Utilidad neta

---

## Agrupaciones

* Día
* Semana
* Mes
* Año

---

# 21. Rentabilidad

## Cálculos

* Margen por producto
* Margen por corte
* Rentabilidad general

---

## Rankings

### Más rentables

Mostrar productos con mayor margen.

### Menos rentables

Mostrar productos con menor margen.

---

# 22. Auditoría

## Registrar

* Usuario
* Acción
* Fecha
* Hora

---

# 23. Notificaciones

## Alertas

### Stock

* Stock bajo
* Stock crítico

### Cuenta Corriente

* Deudas vencidas

### Gastos

* Gastos elevados

### Caja

* Diferencias detectadas

---

# 24. Diseño e Identidad Visual

## Nombre Comercial

**CARNICERÍA BASILE**

---

## Colores

* Rojo
* Negro
* Blanco

---

## Sensación Deseada

La plataforma debe transmitir:

* Profesionalismo
* Rapidez
* Simplicidad
* Control financiero
* Confianza

---

# 25. Objetivo Final del Producto

Permitir que una carnicería controle en tiempo real:

* Ventas
* Stock
* Compras
* Desposte
* Clientes
* Cuentas corrientes
* Caja
* Gastos
* Rentabilidad
* Reportes

Desde una única plataforma web moderna, multiempresa y multiusuario, orientada a la toma de decisiones basada en información financiera confiable.
