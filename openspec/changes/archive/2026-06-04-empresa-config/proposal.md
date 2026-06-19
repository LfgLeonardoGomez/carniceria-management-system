# Proposal: empresa-config (C-03)

## Qué
Implementar la gestión completa de datos de empresa para el SaaS multi-tenant BASILE, incluyendo:
- CRUD de datos fiscales y de contacto (nombre comercial, razón social, CUIT, domicilio, teléfono, email).
- Upload y servicio de logo de empresa (jpg, png, svg) con validación de formato y tamaño (2MB máx).
- Estructuración de `configuracion_general` y `parametros_operativos` como JSON validado vía Pydantic.
- Soft delete (`activa = false`) sin eliminación física, preservando historial (RN-GLOBAL-02).
- Pantalla de configuración de empresa en el frontend, accesible únicamente para Administrador.
- Aislamiento multi-tenant estricto: cada usuario solo ve y modifica los datos de su empresa.

## Por qué
- **Bloqueante para personalización de la plataforma**: Sin datos de empresa no se pueden generar tickets, reportes ni comprobantes fiscales.
- **Requisito legal argentino**: El CUIT es obligatorio para operaciones fiscales y debe tener formato válido.
- **Branding**: El logo aparece en tickets, reportes y la interfaz de usuario.
- **Configuración operativa**: `parametros_operativos` habilita futuras alertas (stock, gastos) y `configuracion_general` define comportamientos por empresa.
- **Seguridad**: Los datos fiscales son sensibles; el aislamiento entre tenants es crítico (RN-SEG-01).

## Alcance
- Endpoints REST bajo `/empresas`: GET, PUT/PATCH (update), POST `/:id/logo`, PATCH `/:id/desactivar`.
- Validación estricta del CUIT argentino (11 dígitos + dígito verificador).
- Almacenamiento de logos en filesystem local (`UPLOAD_PATH`) con path por tenant.
- Schemas Pydantic para `datos_fiscales`, `configuracion_general`, `parametros_operativos`.
- Middleware `require_auth` ya protege endpoints; se añade verificación de rol `Administrador`.
- Frontend: formulario de configuración con previsualización de logo.
- Tests de integración con PostgreSQL real (testcontainers): CRUD, validación CUIT, upload, aislamiento.

## Fuera de alcance
- Envío de emails con branding (ya cubierto en C-02, se reutiliza infraestructura).
- Gestión de múltiples empresas por usuario (v1.0 asume 1:1).
- Almacenamiento de logos en S3/Cloudinary (se define path local ahora; migración transparente en fase DevOps).
- RLS en PostgreSQL (se mantiene como capa de seguridad adicional pero no se modifica schema en este change).

## Dependencias
- C-01-foundation-setup (modelo `Empresa`, DB, seed data).
- C-02-auth-core (middleware `require_auth`, inyección de `empresa_id` y `current_user` en `request.state`).

## Riesgos y mitigaciones
| Riesgo | Mitigación |
|--------|------------|
| Filtración de datos fiscales entre tenants | Middleware obligatorio `require_auth` + filtrado por `request.state.empresa_id` en cada query; no se expone `id` de empresa en URL sin validación cruzada. |
| CUIT inválido ingresado | Validador Pydantic custom con algoritmo de dígito verificador argentino; error 422 antes de tocar DB. |
| Upload de archivo malicioso | Validación estricta de MIME type (python-magic), extensión permitida (jpg/png/svg) y tamaño máximo 2MB; almacenamiento fuera de webroot. |
| Sobrescritura de logo de otro tenant | Path de almacenamiento incluye `empresa_id` como prefijo de directorio; el endpoint usa `request.state.empresa_id`, no el `:id` de la URL para determinar el destino. |
