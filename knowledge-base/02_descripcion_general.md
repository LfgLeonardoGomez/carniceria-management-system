# Descripción General

## Stack tecnológico

> **⚠️ No especificado en la fuente.** El documento de especificación funcional no define stack tecnológico, arquitectura de software ni frameworks. Lo siguiente debe ser confirmado o definido por el equipo técnico.

| Capa | Tecnologías | Versión mínima | Estado |
|------|------------|----------------|--------|
| Frontend | *Por definir* | — | Pendiente |
| Backend | *Por definir* | — | Pendiente |
| Base de datos | *Por definir* | — | Pendiente |
| ORM/ODM | *Por definir* | — | Pendiente |
| Auth | *Por definir* | — | Pendiente |
| Hosting/Infra | *Por definir* | — | Pendiente |

**Recomendación técnica dada la naturaleza del sistema**:
- **Frontend**: SPA responsive (React/Vue/Svelte) o framework full-stack con SSR.
- **Backend**: REST API con framework robusto (Node.js/Express, Python/FastAPI, Java/Spring, etc.).
- **Base de datos**: SQL relacional (PostgreSQL/MySQL) recomendado por la fuerte relación entre entidades y la necesidad de transacciones ACID en ventas, caja y stock.
- **Auth**: JWT con refresh tokens o sesiones seguras.
- **File storage**: para logos de empresa y exportaciones (S3, Cloudinary, etc.).

## Arquitectura general

```
┌─────────────────────────────────────────────┐
│              Cliente (Browser)               │
│        Desktop / Tablet / Mobile             │
└──────────────┬──────────────────────────────┘
               │ HTTPS
┌──────────────▼──────────────────────────────┐
│           CDN / Static Hosting              │
│         (Frontend SPA / SSR)               │
└──────────────┬──────────────────────────────┘
               │ JSON / REST
┌──────────────▼──────────────────────────────┐
│               API Gateway                   │
│         Auth / Rate Limit / TLS            │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│         Backend Application                 │
│  ┌────────────┐  ┌────────────┐            │
│  │   Auth     │  │  Business  │            │
│  │  Module    │  │  Modules   │            │
│  │            │  │ (Ventas,   │            │
│  │ Login,     │  │  Stock,    │            │
│  │ Recovery   │  │  Desposte, │            │
│  │ Roles      │  │  Caja...)  │            │
│  └────────────┘  └────────────┘            │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│         Base de Datos (SQL)                │
│   Multi-tenancy por empresa (tenant_id)  │
└─────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│      Servicios externos                   │
│  Email (recuperación de contraseña)       │
│  SYSTEL (lectura de balanzas)            │
│  Exportación Excel/PDF/CSV                │
└─────────────────────────────────────────────┘
```

**Decisiones de alto nivel (a confirmar)**:
- **Multi-tenancia**: Aislamiento lógico por `empresa_id` en todas las tablas. Esto simplifica operaciones y backups.
- **Stateful vs Stateless**: El sistema es stateless en el backend (sesiones en token o DB), lo que facilita escalado horizontal.
- **Responsive**: Diseño mobile-first para soportar tablets en la caja (punto de venta móvil).

## Integraciones externas

| Servicio | Propósito | Tipo | Estado |
|----------|-----------|------|--------|
| Balanzas SYSTEL | Lectura de etiquetas (PLU + peso) para agregar productos al carrito automáticamente | Hardware / HID (teclado emulado) | Especificado |
| Servicio de email | Recuperación de contraseña por correo electrónico | SMTP / API REST (SendGrid, AWS SES, etc.) | Requerido, no especificado proveedor |
| Importador Excel (QUENDRA) | Importación masiva de productos desde archivos Excel exportados por QUENDRA | File upload + parser (xlsx) | Especificado |
| Generador de reportes | Exportación de ventas y reportes financieros a Excel, PDF y CSV | Librería interna (SheetJS, PDFKit, etc.) | Requerido |

## API REST (propuesta a confirmar)

> **Nota**: Los endpoints siguientes son una propuesta funcional basada en los módulos del documento. Deben ser validados y detallados en una especificación de API.

| Recurso | Endpoints principales | Métodos |
|---------|----------------------|---------|
| Auth | `/auth/login`, `/auth/recover` | POST |
| Empresas | `/empresas`, `/empresas/:id` | CRUD |
| Usuarios | `/usuarios` | CRUD |
| Productos | `/productos`, `/productos/import` | CRUD + POST |
| Clientes | `/clientes` | CRUD |
| Proveedores | `/proveedores` | CRUD |
| Compras | `/compras` | CRUD |
| Despostes | `/despostes` | CRUD |
| Stock | `/stock`, `/stock/movimientos`, `/stock/alertas` | GET, POST, PATCH |
| Ventas | `/ventas`, `/ventas/:id/ticket` | CRUD + POST |
| Caja | `/caja/apertura`, `/caja/cierre`, `/caja/movimientos` | POST, GET |
| Gastos | `/gastos` | CRUD |
| Cuentas corrientes | `/cuentas-corrientes`, `/cuentas-corrientes/:id/pagos` | GET, POST |
| Reportes | `/reportes/ventas`, `/reportes/financieros` | GET |
| Dashboard | `/dashboard/indicadores` | GET |
| Auditoría | `/auditoria` | GET |

**Patrón común para multi-tenancia**: Todos los endpoints deben filtrar implícitamente por `empresa_id` del usuario autenticado.
