## Context

El change `C-04` se ejecuta sobre una base ya establecida: `C-01` (foundation), `C-02` (auth-core) y `C-03` (empresa-config) están implementados y archivados. El backend tiene el módulo `auth` con login JWT, `empresa` con CRUD, pero el módulo `usuario` (`backend/src/modules/usuario/`) solo contiene archivos placeholder sin lógica de negocio. El frontend tiene el shell de la SPA React con router y store de autenticación, pero no existe la pantalla de gestión de usuarios.

La base de conocimiento define una matriz RBAC con 4 roles fijos (Administrador, Encargado, Cajero, Vendedor) y 4 niveles de permisos (CRUD) sobre 14 dominios funcionales. La regla RN-AU-03 establece que los permisos son fijos y no configurables por empresa en v1.0.

## Goals / Non-Goals

**Goals:**
1. Implementar CRUD completo de usuarios dentro del ámbito de una empresa, con soft-delete (`activo = false`) y reactivación.
2. Construir el sistema de autorización RBAC con matriz de permisos inmutable en código Python, exponible como dependency FastAPI `require_role(permiso: str)`.
3. Permitir a cualquier usuario autenticado consultar y editar su propio perfil (`GET /usuarios/me`).
4. Generar una contraseña temporal al crear un usuario, visible una sola vez en la respuesta POST.
5. Proteger la existencia de al menos un Administrador activo por empresa (no permitir desactivación o cambio de rol del último admin).
6. Crear la pantalla de gestión de usuarios en el frontend y proteger las rutas por rol.
7. Aplicar TDD: tests de integración con PostgreSQL real (testcontainers) antes del código productivo.

**Non-Goals:**
1. Recuperación de contraseña por email (ya implementado en `C-02 auth-core`).
2. Tabla de roles configurable por empresa o UI para editar permisos (v1.0 hardcodeado según RN-AU-03).
3. Auditoría completa de acciones (scope de `C-20 auditoria-notificaciones`).
4. Notificaciones al crear/modificar usuarios.
5. Rate limiting (ya presente en `C-02` en endpoints de auth; se podría extender pero no es objetivo de este change).

## Decisions

1. **RBAC matriz en código Python (`common/rbac.py`) como diccionario inmutable**
   - *Rationale*: Los roles y permisos son fijos en v1.0 (RN-AU-03). No justifica una tabla de permisos en DB con joins adicionales en cada request. Un dict inmutable en Python es performante, testeable y versionable con el código.
   - *Alternativa considerada*: Tabla `permiso` + tabla intermedia `rol_permiso`. Rechazada: complejidad innecesaria para v1.0, más queries por request, más código de mantenimiento.

2. **Dependency `require_role(permiso: str)` de FastAPI**
   - *Rationale*: FastAPI soporta dependencies nativas. `require_role` se combina con `get_current_user` para obtener el rol del usuario y verificar contra la matriz. Permite decorar cada endpoint de forma declarativa: `dependencies=[Depends(require_role("usuarios:crear"))]`.
   - *Alternativa considerada*: Middleware global que parsea la ruta. Rechazada: menos explícito, más difícil de mantener, y no se integra bien con la documentación OpenAPI de FastAPI.

3. **Protección del último Administrador → HTTP 409 Conflict**
   - *Rationale*: Si un Administrador intenta desactivarse a sí mismo o cambiar su rol siendo el único admin activo de la empresa, el sistema debe rechazar la operación. 409 Conflict es el código semántico correcto para un estado de recurso que impediría la operación.
   - *Alternativa considerada*: 403 Forbidden. Rechazada: 403 implica que el usuario no tiene permiso; acá el problema es el estado del sistema, no los permisos del actor.

4. **Contraseña temporal visible una sola vez en respuesta POST `
/usuarios`**
   - *Rationale*: Al crear un usuario, el administrador no debe conocer la contraseña permanente. Generar una temporal aleatoria y devolverla en la respuesta de creación permite al admin comunicarla al nuevo usuario (fuera de banda). El hash se almacena en DB; la contraseña en texto plano nunca se almacena y nunca se vuelve a exponer.
   - *Riesgo*: La respuesta POST viaja por la red. *Mitigación*: TLS obligatorio en producción (ya definido en `C-01`).
   - *Alternativa considerada*: Enviar contraseña por email. Rechazada: complejidad adicional (SMTP, templates, colas), no prioridad para v1.0.

5. **Índices en `usuario(empresa_id, activo)` y `usuario(email)` único global**
   - *Rationale*: El listado de usuarios por empresa filtra por `empresa_id` y `activo`. El email es el identificador de login global y debe ser único. El índice compuesto acelera el listado más común.
   - *Nota*: Un usuario desactivado (`activo = false`) conserva su email. No se permite crear un nuevo usuario con el mismo email activo. Esto evita conflictos de login y mantiene trazabilidad.

6. **Pydantic `extra='forbid'` en todos los request/response schemas**
   - *Rationale*: Regla dura del proyecto. Evita que el cliente envíe campos no esperados, reduciendo vectores de ataque y errores silenciosos.

7. **Servicio de usuarios (`service.py`) con lógica de negocio; router delgado (`router.py`)**
   - *Rationale*: Separa la lógica de negocio (protección del último admin, generación de contraseña) del transporte HTTP. Facilita testing unitario del servicio sin levantar el servidor.

8. **Soft-delete con campo `activo` (boolean)**
   - *Rationale*: Regla dura RN-GLOBAL-02. Nunca eliminación física. Un usuario desactivado no puede loguearse (validación en login) pero preserva historial en tablas relacionadas (ventas, auditoría, caja).

## Risks / Trade-offs

1. **[Riesgo] RBAC hardcoded limita la venta a empresas con necesidades de permisos custom.**
   - *Mitigación*: Es un trade-off aceptado para v1.0 (RN-AU-03). Si surge demanda, se migra a tabla `rol_permiso` en v2.0 sin cambiar la interfaz de `require_role`.

2. **[Riesgo] Contraseña temporal en respuesta HTTP expone texto plano transitoriamente.**
   - *Mitigación*: TLS obligatorio. El admin debe copiar la contraseña y comunicarla de forma segura. El usuario debe cambiarla en su primer login (feature a agregar en v1.1 o v2.0; por ahora es responsabilidad del admin informar).

3. **[Riesgo] Soft-delete con email único global puede bloquear la creación de un usuario con email de un empleado anterior desactivado.**
   - *Mitigación*: Aceptado por diseño. El email es identidad de login. Si un empleado se va, su cuenta se desactiva. Si vuelve, se reactiva. Si otro empleado nuevo usa el mismo email (improbable), el admin debe usar un email diferente o contactar a soporte. En v2.0 se puede evaluar soft-delete con email + timestamp.

4. **[Riesgo] Aplicar `require_role` a todos los endpoints existentes (`/empresas`) puede generar regressions si no se cubren con tests.**
   - *Mitigación*: Los tests de integración de `C-03` se extenderán para verificar que `/empresas` sigue accesible solo para Administradores. No se modificará la lógica de negocio de `/empresas`, solo se agrega la dependency.

5. **[Trade-off] No se implementa rate limiting en `/usuarios`**
   - *Mitigación*: Rate limiting ya existe en `/auth/*`. Los endpoints de `/usuarios` requieren autenticación, lo que reduce el riesgo de abuso masivo. Se puede agregar en v1.1 si el monitoreo lo indica.

## Migration Plan

- No hay migración de datos compleja: el módulo `usuario` está vacío (placeholders). El change es netamente aditivo.
- Rollback: eliminar los archivos creados en `backend/src/modules/usuario/` y revertir los cambios en `auth/`. Los datos en DB son compatibles con versiones anteriores (mismo schema).

## Open Questions

- ¿El frontend debe redirigir al perfil de usuario cuando un usuario no-admin intenta acceder a `/usuarios`? → Sí, protección de ruta en router React.
- ¿Se debe enviar un email de bienvenida al crear usuario? → No, fuera de scope de v1.0. El admin comunica la contraseña temporal.
- ¿Se permite que un Administrador edite su propio rol? → No, si es el último admin. Sí, si hay otro admin activo.
