# Modelo de Datos

## Dominios

| Dominio | Descripción |
|---------|-------------|
| Autenticación | Usuarios, roles, sesiones, recuperación de contraseña. |
| Empresa | Datos de la empresa carnicería, configuración fiscal y parámetros operativos. |
| Producto | Catálogo de productos con PLU, precios, stock y categorías. |
| Cliente | Clientes finales y mayoristas con cuenta corriente. |
| Proveedor | Proveedores de media res y otros insumos. |
| Compra | Registro de compras de media res con costos y pesos. |
| Desposte | Proceso de desposte de media res en cortes con rendimiento y merma. |
| Stock | Inventario por kilos, entradas, salidas, ajustes y kardex. |
| Venta | Ventas con carrito, medios de pago, descuentos y tickets. |
| Caja | Apertura, cierre y movimientos de caja con control de efectivo y tarjetas. |
| Gasto | Registro de gastos categorizados de la operación. |
| Cuenta Corriente | Deuda, pagos y estado de cuenta de clientes. |
| Reporte | Datos agregados para exportación y reportes financieros. |
| Auditoría | Registro de acciones de usuarios con timestamp. |
| Notificación | Alertas del sistema (stock, deudas, gastos, caja). |

## ERD (Entity Relationship Diagram)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Empresa    │1    *│   Usuario    │     │    Rol       │
│              │◄─────│  (por emp)   │*───*│              │
└──────┬───────┘      └──────────────┘     └──────────────┘
       │
       │ 1
       │
       ▼ *
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Producto   │*────*│   Cliente    │     │  Proveedor   │
│              │      │              │     │              │
└──────┬───────┘      └──────┬───────┘     └──────┬───────┘
       │                     │                    │
       │                     │                    │
       ▼                     ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│MovimientoStock│     │CuentaCorriente│    │   Compra     │
│   (Kardex)   │      │              │     │              │
└──────────────┘      └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
                                           ┌──────────────┐
                                           │   Desposte   │
                                           │              │
                                           └──────┬───────┘
                                                  │
                                                  ▼
                                           ┌──────────────┐
                                           │ CorteDesposte│
                                           │              │
                                           └──────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Venta     │*────*│ DetalleVenta │*────│   Producto   │
│              │      │              │     │              │
└──────┬───────┘      └──────────────┘     └──────────────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│   PagoVenta  │     │     Caja     │
│              │     │  (por emp)   │
└──────────────┘     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ MovimientoCaja│
                     │              │
                     └──────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Gasto     │     │   Reporte    │     │  Auditoría   │
│              │     │   (virtual)  │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
```

> **Nota**: Todas las entidades (excepto posiblemente Usuario y Rol en un schema compartido) deben incluir `empresa_id` para garantizar el aislamiento multi-tenant.

## Entidades

### Empresa
- `id` (UUID / bigint PK)
- `nombre_comercial` (string, obligatorio)
- `razon_social` (string)
- `cuit` (string, único por tenant o global)
- `domicilio` (string)
- `telefono` (string)
- `email` (string)
- `logo_url` (string, nullable)
- `datos_fiscales` (JSON / campos estructurados)
- `configuracion_general` (JSON)
- `parametros_operativos` (JSON)
- `activa` (boolean, default true)
- `created_at`, `updated_at` (timestamps)

**Relaciones**:
- 1:N con Usuario
- 1:N con Producto, Cliente, Proveedor, Compra, Desposte, Venta, Caja, Gasto, MovimientoStock

**Constraints**:
- `cuit` debe tener formato válido argentino (11 dígitos).
- Aislamiento total: queries SIEMPRE filtradas por `empresa_id`.

---

### Usuario
- `id` (PK)
- `empresa_id` (FK → Empresa, nullable si es superadmin de plataforma)
- `email` (string, único global para login)
- `contrasena_hash` (string)
- `nombre` (string)
- `apellido` (string)
- `rol_id` (FK → Rol)
- `activo` (boolean, default true)
- `ultimo_acceso` (timestamp, nullable)
- `created_at`, `updated_at` (timestamps)

**Relaciones**:
- N:1 con Empresa
- N:1 con Rol
- 1:N con Venta (como vendedor/cajero)
- 1:N con Auditoría

---

### Rol
- `id` (PK)
- `nombre` (enum/string: Administrador, Encargado, Cajero, Vendedor)
- `permisos` (JSON o tabla intermedia Permiso)
- `created_at`, `updated_at`

**Relaciones**:
- 1:N con Usuario

---

### Producto
- `id` (PK)
- `empresa_id` (FK)
- `plu` (string, único por empresa)
- `nombre` (string, obligatorio)
- `categoria_id` (FK → CategoriaProducto)
- `precio_publico` (decimal, >= 0)
- `precio_mayorista` (decimal, >= 0)
- `costo_por_kilo` (decimal, >= 0)
- `margen` (decimal, calculado o almacenado)
- `stock_actual` (decimal, kilos, >= 0)
- `stock_minimo` (decimal, nullable — para alertas)
- `activo` (boolean, default true)
- `created_at`, `updated_at`

**Relaciones**:
- N:1 con Empresa
- N:1 con CategoriaProducto
- 1:N con MovimientoStock
- 1:N con DetalleVenta

**Constraints**:
- `plu` único por `empresa_id`.
- `margen` debe poder calcularse como `(precio - costo) / precio` o similar.
- Todo stock en kilos (RN-STOCK-01).

---

### CategoriaProducto (seed data)
- `id` (PK)
- `empresa_id` (FK, nullable si son categorías globales o por empresa)
- `nombre` (string)
- `created_at`, `updated_at`

**Relaciones**:
- 1:N con Producto

---

### Cliente
- `id` (PK)
- `empresa_id` (FK)
- `nombre` (string)
- `apellido` (string)
- `razon_social` (string, nullable)
- `cuit` (string, nullable)
- `telefono` (string)
- `email` (string, nullable)
- `direccion` (string, nullable)
- `tipo_cliente` (enum: publico_general, mayorista, especial)
- `limite_cuenta_corriente` (decimal, nullable)
- `saldo_actual` (decimal, default 0)
- `created_at`, `updated_at`

**Relaciones**:
- N:1 con Empresa
- 1:N con Venta
- 1:N con CuentaCorriente

---

### Proveedor
- `id` (PK)
- `empresa_id` (FK)
- `nombre` (string, obligatorio)
- `cuit` (string, nullable)
- `telefono` (string)
- `email` (string, nullable)
- `direccion` (string, nullable)
- `created_at`, `updated_at`

**Relaciones**:
- N:1 con Empresa
- 1:N con Compra

---

### Compra (Media Res)
- `id` (PK)
- `empresa_id` (FK)
- `proveedor_id` (FK)
- `fecha` (date)
- `cantidad_medias_reses` (integer, >= 1)
- `peso_total` (decimal, kilos, > 0)
- `costo_total` (decimal, > 0)
- `costo_por_kilo` (decimal, calculado: costo_total / peso_total)
- `costo_promedio_historico` (decimal, calculado o snapshot)
- `observaciones` (text, nullable)
- `created_at`, `updated_at`

**Relaciones**:
- N:1 con Empresa
- N:1 con Proveedor
- 1:N con Desposte (opcional, una compra puede despostarse una o más veces)
- 1:N con MovimientoStock (entrada)

---

### Desposte
- `id` (PK)
- `empresa_id` (FK)
- `compra_id` (FK)
- `fecha` (date)
- `operador_id` (FK → Usuario)
- `rendimiento_total` (decimal, kilos, calculado)
- `merma` (decimal, kilos, calculado: peso_total_compra - rendimiento_total)
- `created_at`, `updated_at`

**Relaciones**:
- N:1 con Empresa
- N:1 con Compra
- N:1 con Usuario (operador)
- 1:N con CorteDesposte
- 1:N con MovimientoStock (entradas de stock generadas automáticamente)

---

### CorteDesposte
- `id` (PK)
- `desposte_id` (FK)
- `tipo_corte` (enum: asado, vacio, nalga, cuadril, peceto, bola_de_lomo, lomo, matambre, costilla, osobuco, molida, otros)
- `kilos_obtenidos` (decimal, >= 0)
- `porcentaje_rendimiento` (decimal, calculado)
- `costo_asignado` (decimal)
- `costo_final_por_kilo` (decimal, calculado: costo_asignado / kilos_obtenidos)
- `producto_id` (FK → Producto generado, nullable si se linkea a posteriori)
- `created_at`, `updated_at`

**Relaciones**:
- N:1 con Desposte
- N:1 con Producto

---

### MovimientoStock (Kardex)
- `id` (PK)
- `empresa_id` (FK)
- `producto_id` (FK)
- `tipo` (enum: entrada_compra, entrada_desposte, salida_venta, ajuste)
- `cantidad_kilos` (decimal, > 0 para entrada, < 0 para salida)
- `stock_resultante` (decimal, snapshot post-movimiento)
- `referencia_id` (string, polymorphic: ID de compra, desposte, venta o ajuste)
- `referencia_tipo` (string, tipo de entidad origen)
- `fecha` (timestamp)
- `created_at`

**Relaciones**:
- N:1 con Empresa
- N:1 con Producto

**Constraints**:
- `stock_resultante` nunca negativo (para ventas/ajustes).
- Índice compuesto en `(empresa_id, producto_id, fecha)` para consultas de kardex.

---

### Venta
- `id` (PK)
- `empresa_id` (FK)
- `cliente_id` (FK, nullable para público general)
- `usuario_id` (FK → Usuario que cobra)
- `fecha` (timestamp)
- `subtotal` (decimal)
- `descuentos` (decimal, default 0)
- `total` (decimal, subtotal - descuentos)
- `estado` (enum: en_curso, suspendida, cobrada, anulada)
- `tipo_cliente_al_momento` (enum snapshot)
- `ganancia_estimada` (decimal, calculado)
- `created_at`, `updated_at`

**Relaciones**:
- N:1 con Empresa
- N:1 con Cliente
- N:1 con Usuario
- 1:N con DetalleVenta
- 1:N con PagoVenta
- 1:1 con CuentaCorriente (si hay pago a cuenta corriente)

---

### DetalleVenta
- `id` (PK)
- `venta_id` (FK)
- `producto_id` (FK)
- `cantidad_kilos` (decimal, > 0)
- `precio_unitario` (decimal)
- `importe` (decimal, cantidad * precio_unitario)
- `costo_unitario_estimado` (decimal, para cálculo de rentabilidad)
- `created_at`

**Relaciones**:
- N:1 con Venta
- N:1 con Producto

---

### PagoVenta
- `id` (PK)
- `venta_id` (FK)
- `medio_pago` (enum: efectivo, transferencia, debito, credito, cuenta_corriente)
- `importe` (decimal)
- `created_at`

**Relaciones**:
- N:1 con Venta

---

### Caja
- `id` (PK)
- `empresa_id` (FK)
- `fecha_apertura` (timestamp)
- `fecha_cierre` (timestamp, nullable)
- `efectivo_inicial` (decimal)
- `efectivo_esperado` (decimal, calculado)
- `efectivo_real` (decimal, ingresado al cerrar)
- `transferencias_esperadas` (decimal)
- `transferencias_reales` (decimal)
- `tarjetas_esperadas` (decimal)
- `tarjetas_reales` (decimal)
- `diferencia_total` (decimal, calculado)
- `estado` (enum: abierta, cerrada)
- `usuario_apertura_id` (FK)
- `usuario_cierre_id` (FK, nullable)
- `created_at`, `updated_at`

**Relaciones**:
- N:1 con Empresa
- N:1 con Usuario (apertura)
- N:1 con Usuario (cierre)
- 1:N con MovimientoCaja

---

### MovimientoCaja
- `id` (PK)
- `caja_id` (FK)
- `tipo` (enum: entrada_venta, retiro, ingreso_manual)
- `medio_pago` (enum: efectivo, transferencia, debito, credito)
- `importe` (decimal)
- `descripcion` (string, nullable)
- `created_at`

**Relaciones**:
- N:1 con Caja

---

### Gasto
- `id` (PK)
- `empresa_id` (FK)
- `fecha` (date)
- `categoria` (enum: alquiler, empleados, luz, agua, gas, internet, combustible, impuestos, mantenimiento, insumos, otros)
- `descripcion` (text)
- `importe` (decimal, > 0)
- `medio_pago` (enum: efectivo, transferencia, debito, credito)
- `created_at`, `updated_at`

**Relaciones**:
- N:1 con Empresa

---

### CuentaCorriente (Movimiento)
- `id` (PK)
- `empresa_id` (FK)
- `cliente_id` (FK)
- `tipo` (enum: deuda, pago)
- `importe` (decimal)
- `saldo_resultante` (decimal, snapshot)
- `venta_id` (FK, nullable — para deudas originadas en venta)
- `fecha` (timestamp)
- `created_at`

**Relaciones**:
- N:1 con Empresa
- N:1 con Cliente
- N:1 con Venta

---

### Auditoría
- `id` (PK)
- `empresa_id` (FK)
- `usuario_id` (FK)
- `accion` (string, ej: "CREAR_VENTA", "ELIMINAR_PRODUCTO")
- `entidad_tipo` (string)
- `entidad_id` (string)
- `payload` (JSON, nullable — snapshot del cambio)
- `fecha` (date)
- `hora` (time)
- `created_at`

**Relaciones**:
- N:1 con Empresa
- N:1 con Usuario

---

### Notificación
- `id` (PK)
- `empresa_id` (FK)
- `tipo` (enum: stock_bajo, stock_critico, deuda_vencida, gasto_elevado, diferencia_caja)
- `mensaje` (text)
- `leida` (boolean, default false)
- `entidad_tipo` (string, nullable)
- `entidad_id` (string, nullable)
- `created_at`

**Relaciones**:
- N:1 con Empresa

## Seed data inicial

**Roles** (obligatorios):
- Administrador
- Encargado
- Cajero
- Vendedor

**Categorías de producto** (sugeridas, configurables por empresa):
- Carne vacuna
- Carne de cerdo
- Pollo
- Embutidos
- Otros

**Tipos de corte** (para desposte, fijos por sistema):
- Asado, Vacío, Nalga, Cuadril, Peceto, Bola de lomo, Lomo, Matambre, Costilla, Osobuco, Molida, Otros

**Categorías de gasto** (fijas por sistema):
- Alquiler, Empleados, Luz, Agua, Gas, Internet, Combustible, Impuestos, Mantenimiento, Insumos, Otros

**Tipos de cliente** (fijos por sistema):
- Público General, Mayorista, Especial
