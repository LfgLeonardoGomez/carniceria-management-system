# Proposal: usuarios-rbac (C-04)

## Why

Con el núcleo de autenticación (C-02) y la configuración de empresa (C-03) operativos, el siguiente paso crítico es permitir que los **Administradores** gestionen usuarios dentro de su empresa y que el sistema **imponga restricciones de acceso** según el rol asignado. Sin RBAC, todo usuario autenticado tiene visibilidad total del tenant, violando RN-SEG-02 y RN-AU-03. Este change habilita la gobernanza de permisos que el resto de los módulos (ventas, stock, desposte, caja) necesitarán para operar de forma segura.

## What Changes

- **CRUD de usuarios** bajo `/usuarios`: alta, listado filtrado por empresa, edición de datos básicos, soft-delete (`activo = false`) y reactivación. Solo Administrador puede ejecutar estas operaciones.
- **Asignación de rol**: al crear o editar un usuario, el Administrador le asigna uno de los 4 roles del sistema (Administrador, Encargado, Cajero, Vendedor). Se valida que un Administrador no pueda auto-degradarse si es el único admin de la empresa.
- **Middleware de autorización RBAC**: dependency `require_role(permiso)` que verifica si el rol del usuario autenticado tiene permiso sobre el recurso solicitado, basado en la matriz de permisos del KB.
- **Perfil de usuario**: endpoint `GET /usuarios/me` para que cualquier usuario autenticado consulte y actualice sus propios datos (nombre, apellido, email) sin permisos de admin.
- **Seed de usuario admin por defecto**: al crear la primera empresa (o en seed data), se genera automáticamente un usuario Administrador para que el sistema sea usable inmediatamente.
- **Frontend**: pantalla de gestión de usuarios accesible solo para Administrador, con tabla de usuarios, formulario de alta/edición, selector de rol y diálogo de confirmación para desactivar/reactivar.
- **Tests**: TDD obligatorio — tests de CRUD con permisos, middleware RBAC, validación de reglas de negocio (único admin, no auto-eliminación) y seed de admin.

## Capabilities

### New Capabilities
- `user-management`: CRUD de usuarios dentro de una empresa, asignación de roles, soft-delete y reactivación. Reglas de negocio: protección del último admin activo.
- `rbac-middleware`: enforcement de permisos en endpoints. Dependency `require_role(permiso)` que consulta la matriz RBAC y responde 403 si el rol no tiene acceso al recurso.
- `user-profile`: consulta y edición del perfil propio del usuario autenticado (`/usuarios/me`), independiente del CRUD de administración.

### Modified Capabilities
- `seed-data`: agregar requisito de creación automática de un usuario Administrador por defecto asociado a la empresa creada en el seed, para que el sistema tenga credenciales de acceso inmediatas.
- `security-baseline`: extender los requisitos para incluir protección de rutas basada en rol (RBAC) además de autenticación JWT, asegurando que endpoints sensibles requieran no solo token válido sino también permiso de rol.

## Impact

- **Backend**: nuevo módulo `backend/src/modules/usuario/` con router, modelos, schemas y servicio. Nuevo módulo `backend/src/common/rbac.py` con la matriz de permisos y dependency `require_role`. Modificación del middleware de auth existente (C-02) para inyectar `current_user.rol` en `request.state`.
- **Frontend**: nueva ruta `/usuarios` con grid de usuarios y formulario de alta/edición. Uso de Zustand para estado de usuarios.
- **Base de datos**: tabla `usuario` ya existe desde C-01, pero se extiende con índice en `(empresa_id, activo)` y se asegura FK a `rol`. Seed data actualizado.
- **Dependencias**: C-02 (auth core — JWT, middleware, dependencias), C-03 (empresa config — aislamiento por `empresa_id`).
