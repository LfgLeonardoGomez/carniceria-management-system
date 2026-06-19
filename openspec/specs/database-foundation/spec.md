# database-foundation Specification

## Purpose
TBD - created by archiving change c-01-foundation-setup. Update Purpose after archive.
## Requirements
### Requirement: Conexión PostgreSQL con SQLModel/SQLAlchemy 2.0 async
El sistema SHALL conectarse a PostgreSQL 14+ usando SQLModel/SQLAlchemy 2.0 con `AsyncSession` y pool de conexiones.

#### Scenario: Backend conecta a PostgreSQL de forma async
- **WHEN** el backend inicia con `DATABASE_URL` válida
- **THEN** se crea un engine async con `create_async_engine`
- **AND** se provee `AsyncSession` vía `async_sessionmaker`
- **AND** las queries a la base de datos usan `await session.execute(...)`

### Requirement: Tablas iniciales del schema
El sistema SHALL crear las tablas `empresa`, `rol` y `usuario` con sus campos, tipos y constraints definidos en `knowledge-base/04_modelo_de_datos.md`.

#### Scenario: Schema inicial está presente
- **WHEN** se ejecutan las migraciones de Alembic (o `create_all` en tests)
- **THEN** existen las tablas `empresa`, `rol` y `usuario`
- **AND** `empresa` tiene los campos: `id`, `nombre_comercial`, `razon_social`, `cuit`, `domicilio`, `telefono`, `email`, `logo_url`, `datos_fiscales`, `configuracion_general`, `parametros_operativos`, `activa`, `created_at`, `updated_at`
- **AND** `rol` tiene los campos: `id`, `nombre`, `permisos`, `created_at`, `updated_at`
- **AND** `usuario` tiene los campos: `id`, `empresa_id`, `email`, `contrasena_hash`, `nombre`, `apellido`, `rol_id`, `activo`, `ultimo_acceso`, `created_at`, `updated_at`
- **AND** `usuario.email` es único globalmente
- **AND** `usuario.empresa_id` es nullable (preparado para superadmin de plataforma)

### Requirement: Alembic configurado para migraciones
El sistema SHALL tener Alembic configurado con `alembic.ini` y scripts de migración en `backend/src/database/migrations/`.

#### Scenario: Crear y aplicar migraciones
- **WHEN** un desarrollador ejecuta `alembic revision --autogenerate -m "initial schema"`
- **THEN** se genera un archivo de migración válido en `database/migrations/versions/`
- **AND** `alembic upgrade head` aplica la migración sin errores
- **AND** `alembic downgrade -1` revierte la última migración correctamente

### Requirement: Aislamiento multi-tenant preparado
El sistema SHALL incluir `empresa_id` en todas las tablas de negocio y preparar el mecanismo para filtrado automático.

#### Scenario: Tablas de negocio tienen empresa_id
- **WHEN** se inspeccionan los modelos de `empresa`, `rol` y `usuario`
- **THEN** `empresa` NO requiere `empresa_id` (es el tenant raíz)
- **AND** `rol` tiene `empresa_id` nullable (roles globales vs por empresa)
- **AND** `usuario` tiene `empresa_id` nullable
- **AND** el código tiene comentario o decorator que indica dónde se implementará el filtro automático por tenant (middleware o scope en ORM)

