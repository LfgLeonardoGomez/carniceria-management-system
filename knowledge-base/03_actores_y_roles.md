# Actores y Roles

## Actores del sistema

| Actor | Descripción | Cómo interactúa |
|-------|-------------|-----------------|
| Administrador | Dueño o gerente de la carnicería. Requiere visión global y control total. | Panel admin, configuración de empresa, gestión de usuarios, todos los reportes, auditoría. |
| Encargado | Responsable de la operación diaria. Gestiona stock, compras y desposte. | Dashboard, módulos de stock, compras, desposte, reportes operativos y financieros. |
| Cajero | Atiende la caja y cobra. Accede a ventas y clientes. | Pantalla de caja, lectura de balanza SYSTEL, carrito, cobro, gestión de clientes. |
| Vendedor | Solo realiza ventas. Rol más restrictivo. | Pantalla de caja, lectura de balanza, cobro (sin acceso a clientes ni configuración). |
| Sistema (automatizado) | Procesos automáticos: cálculos, alertas, generación de stock. | Ejecuta reglas de negocio, genera notificaciones, actualiza costos promedio, calcula rentabilidad. |

## RBAC — Matriz de permisos

> **Convención**: C = Crear, R = Leer, U = Actualizar, D = Eliminar

| Rol | Productos | Clientes | Proveedores | Compras | Desposte | Stock | Ventas | Caja | Gastos | Cuentas Corrientes | Reportes | Dashboard | Empresa / Usuarios | Auditoría |
|-----|-----------|----------|-------------|---------|----------|-------|--------|------|--------|-------------------|----------|-----------|-------------------|-----------|
| Administrador | CRUD | CRUD | CRUD | CRUD | CRUD | CRUD | CRUD | CRUD | CRUD | CRUD | R | R | CRUD | R |
| Encargado | CRUD | CRU | CRU | CRUD | CRUD | CRUD | RU | RU | CRUD | RU | R | R | — | — |
| Cajero | R | CRU | — | — | — | R | CRUD | CRUD | — | R | — | R | — | — |
| Vendedor | R | — | — | — | — | R | CRUD | R | — | — | — | R | — | — |

**Aclaraciones**:
- **Vendedor**: Según la especificación, solo tiene permisos de "Ventas únicamente". Se interpreta como: puede crear y cobrar ventas, pero no gestionar clientes, caja completa (apertura/cierre) ni reportes.
- **Cajero**: Puede gestionar clientes y ventas, pero no compras, desposte, proveedores ni gastos.
- **Encargado**: Puede gestionar todo lo operativo pero no la configuración de empresa ni la creación de usuarios.
- **Administrador**: Único rol con acceso a configuración de empresa, gestión de usuarios y auditoría completa.

## Rutas públicas

Las siguientes rutas deben ser accesibles **sin autenticación**:

- `/login` — Pantalla de inicio de sesión.
- `/recuperar-contrasena` — Solicitud de recuperación de contraseña.
- `/restablecer-contrasena` — Enlace desde el email de recuperación (token único).

**Nota**: Todo el resto de la aplicación requiere autenticación y autorización basada en rol.
