# Arquitectura Propuesta

## Patrones aplicados

| Patrón | Dónde se usa | Por qué |
|--------|-------------|---------|
| Multi-tenancy (aislamiento lógico) | Capa de datos y API | El sistema es SaaS multiempresa; cada empresa debe tener datos aislados sin infraestructura separada. |
| Repository / Data Access | Backend | Abstrae el acceso a datos y facilita testing y cambios de motor de base de datos. |
| Domain-Driven Design (DDD) ligero | Backend (módulos por dominio) | Cada dominio (Ventas, Stock, Desposte) tiene su propia lógica, entidades y reglas. Evita monolitos spaghetti. |
| CQRS (opcional, a evaluar) | Lecturas de reportes y dashboard | Los reportes financieros y el dashboard requieren agregaciones pesadas; separar lecturas de escrituras mejora performance. |
| API RESTful | Comunicación Frontend-Backend | Estándar, cacheable, fácil de documentar y consumir desde múltiples clientes. |
| JWT / Token-based auth | Autenticación | Stateless, escala horizontalmente, compatible con SPAs. |
| Soft Delete + Auditoría | Todas las entidades transaccionales | RN-GLOBAL-02: prohibe eliminación física; garantiza trazabilidad. |
| Mobile-first Responsive | Frontend | La caja puede operarse desde tablet; el diseño debe adaptarse a desktop, tablet y mobile. |

## Estructura de directorios (propuesta)

> **Nota**: Esta estructura es una propuesta de alto nivel. Debe ajustarse al stack tecnológico final.

```
basile/
├── frontend/                    # Aplicación web (SPA o SSR)
│   ├── public/
│   ├── src/
│   │   ├── features/            # Módulos por dominio (ventas, stock, desposte...)
│   │   │   ├── auth/
│   │   │   ├── dashboard/
│   │   │   ├── productos/
│   │   │   ├── clientes/
│   │   │   ├── proveedores/
│   │   │   ├── compras/
│   │   │   ├── desposte/
│   │   │   ├── stock/
│   │   │   ├── ventas/
│   │   │   ├── caja/
│   │   │   ├── gastos/
│   │   │   ├── cuentas-corrientes/
│   │   │   ├── reportes/
│   │   │   └── notifications/
│   │   ├── shared/              # Componentes, hooks, utils, servicios reutilizables
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── utils/
│   │   │   ├── services/
│   │   │   └── types/
│   │   ├── pages/               # Rutas / páginas (si aplica routing por archivos)
│   │   ├── store/               # Estado global (Redux, Zustand, Signals, etc.)
│   │   ├── styles/
│   │   └── App.tsx / main.tsx
│   ├── package.json
│   └── ...
│
├── backend/                     # API REST
│   ├── src/
│   │   ├── modules/             # Uno por dominio
│   │   │   ├── auth/
│   │   │   ├── empresa/
│   │   │   ├── usuario/
│   │   │   ├── producto/
│   │   │   ├── cliente/
│   │   │   ├── proveedor/
│   │   │   ├── compra/
│   │   │   ├── desposte/
│   │   │   ├── stock/
│   │   │   ├── venta/
│   │   │   ├── caja/
│   │   │   ├── gasto/
│   │   │   ├── cuenta-corriente/
│   │   │   ├── reporte/
│   │   │   ├── auditoria/
│   │   │   └── notificacion/
│   │   ├── common/              # Utils, interceptores, pipes, decorators, excepciones
│   │   ├── config/              # Configuración de entorno, DB, etc.
│   │   ├── database/            # Migrations, seeds, conexión
│   │   └── main.ts              # Punto de entrada
│   ├── package.json
│   └── ...
│
├── docs/                        # Documentación fuente (especificación funcional, etc.)
├── knowledge-base/              # Base de conocimiento generada (esta carpeta)
├── openspec/                    # Documentación de cambios (si aplica OPSX)
└── README.md
```

## Seguridad

- **Autenticación**: Esquema de token (JWT o sesiones seguras). Login con email + contraseña. Recuperación por email con token de un solo uso.
- **Autorización**: RBAC basado en 4 roles (Administrador, Encargado, Cajero, Vendedor). Middleware en API que verifica rol contra recurso solicitado.
- **Validación de input**: Validación estricta en Frontend (UX) y Backend (seguridad). Sanitización de todo input de usuario, especialmente el campo oculto de balanza (puede recibir cualquier string).
- **Secrets management**: Variables de entorno para contraseñas de DB, claves JWT, credenciales de servicio de email. Nunca hardcodeadas.
- **CORS**: Configurado solo para el dominio del Frontend.
- **HTTPS**: Obligatorio en producción.
- **Rate limiting**: En endpoints de autenticación para prevenir fuerza bruta.

## Variables de entorno

| Variable | Descripción | Ejemplo | Sensible |
|----------|-------------|---------|----------|
| `DATABASE_URL` | Conexión a base de datos | `postgres://user:pass@host:5432/basile` | Sí |
| `JWT_SECRET` | Clave para firmar tokens | `super-secret-key-change-in-prod` | Sí |
| `JWT_EXPIRES_IN` | Tiempo de expiración del token | `24h` | No |
| `REFRESH_TOKEN_SECRET` | Clave para refresh tokens | `another-secret-key` | Sí |
| `EMAIL_HOST` | Servidor SMTP o API de email | `smtp.sendgrid.net` | No |
| `EMAIL_PORT` | Puerto SMTP | `587` | No |
| `EMAIL_USER` | Usuario/API key del servicio de email | `apikey` | Sí |
| `EMAIL_PASS` | Contraseña/API secret del servicio de email | `SG.xxx` | Sí |
| `EMAIL_FROM` | Remitente de emails del sistema | `no-reply@basile.app` | No |
| `FRONTEND_URL` | URL base del frontend (para links de recuperación) | `https://basile.app` | No |
| `PORT` | Puerto del servidor backend | `3000` | No |
| `NODE_ENV` | Entorno de ejecución | `production` | No |
| `UPLOAD_PATH` | Ruta para almacenar logos/exportaciones | `./uploads` | No |
| `CORS_ORIGIN` | Origen permitido para CORS | `https://basile.app` | No |

> **Nota**: El stack tecnológico no está definido en la fuente. Las variables anteriores usan nombres genéricos que se adaptan a Node.js, Python, Java u otros.
