# Design: usuarios-rbac (C-04)

## Context

C-02 (auth-core) entregó login JWT con claims `sub`, `empresa_id`, `rol`, middleware de autenticación y rate limiting. C-03 (empresa-config) entregó CRUD de empresa con validación CUIT, upload de logo y soft-delete. Sin embargo, **todavía no existe gestión de usuarios ni autorización por recurso**: cualquier usuario autenticado podría, en teoría, acceder a cualquier endpoint de su empresa. Este change cierra ese gap implementando RBAC sobre el middleware existente.

## Goals / Non-Goals

**Goals:**
- Permitir a un Administrador gestionar usuarios dentro de su empresa (CRUD + soft-delete + reactivación).
- Asignar roles con validación de negocio (protección del último admin).
- Exponer endpoint de perfil propio (`/usuarios/me`).
- Implementar middleware RBAC que verifique permisos por recurso antes de ejecutar el handler.
- Integrar con auth existente: reutilizar `get_current_user`, extender `request.state` con `current_user.rol`.
- Frontend: pantalla de gestión de usuarios protegida por rol admin.

**Non-Goals:**
- Gestión de permisos a nivel de granularidad menor que "recurso × rol" (no permisos individuales por usuario).
- Frontend de perfil propio con cambio de contraseña (se puede hacer, pero no es el foco; el cambio de contraseña vía "recuperar" ya existe en C-02).
- Auditoría detallada de acciones de usuario (C-20).
- Invitaciones por email con link de activación (se crea usuario con contraseña temporal generada por el admin; el usuario la cambia vía recuperar).

## Decisions

### 1. RBAC: matriz en código (Python dict) vs tabla en DB
**Elección**: Matriz de permisos en un módulo Python (`common/rbac.py`) como diccionario inmutable, mapeando `rol → {recurso: permisos}`.
**Racional**: Los 4 roles y ~14 recursos son estáticos por diseño del negocio (KB 03). No hay requisito de que el admin cree roles custom ni edite permisos. Una tabla en DB añadiría joins innecesarios en cada request y complejidad de schema sin beneficio.
**Alternativa descartada**: tabla `permiso` con relación N:M `rol-permiso` → overkill para requisitos fijos.

### 2. Dependency `require_role(permiso: str)` como mecanismo de enforcement
**Elección**: Dependency de FastAPI que recibe un string tipo `"productos:read"` y lanza 403 si el rol del `current_user` no lo tiene.
**Racional**: Reutiliza el sistema de inyección de dependencias de FastAPI. Es declarativa y legible en cada router:
```python
@router.post("/productos", dependencies=[Depends(require_role("productos:create"))])
```
**Alternativa descartada**: Decorador custom → menos compatible con OpenAPI / FastAPI dependency system.

### 3. Protección del último Administrador
**Elección**: Regla de negocio en el servicio de usuarios: antes de desactivar o cambiar de rol a un usuario con `rol == Administrador`, se verifica que quede al menos 1 admin activo en la empresa. Si viola la regla → `409 Conflict` con mensaje claro.
**Racional**: Previene que una empresa quede sin administrador y requiera intervención de soporte. Es un invariante de negocio, no de DB.

### 4. Contraseña temporal al crear usuario
**Elección**: Al crear un usuario nuevo, el backend genera una contraseña temporal aleatoria, la hashea con bcrypt y la guarda. El admin la ve una sola vez en la respuesta del POST. El usuario debe cambiarla en su primer login o usar "recuperar contraseña".
**Racional**: El admin no debe conocer la contraseña final del usuario. El flujo es estándar en SaaS B2B. Se reutiliza el servicio de email de C-02 para enviar un email de bienvenida con el link de recuperación.
**Alternativa descartada**: Enviar email con contraseña en texto plano → inseguro. Invitación con token de activación → más complejo, se aplaza a v2.

### 5. Índices de DB
**Elección**: índice compuesto en `usuario(empresa_id, activo)` e índice único en `usuario(email)` (ya existe desde C-01, se valida). FK `rol_id` con índice implícito.
**Racional**: Las queries más frecuentes son "usuarios de mi empresa activos" y "login por email". No se indexa por `rol_id` explícitamente porque la cardinalidad es baja (4 roles) y el índice de `empresa_id` ya filtra fuertemente.

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|------------|
| Un admin desactiva a otro admin y queda solo un admin que luego olvida su contraseña → lockout total | Seed data siempre asegura que exista al menos un usuario admin. En runtime, la regla "último admin" impide la desactivación. Si aún así ocurre, recuperación de contraseña (C-02) es la vía de escape. |
| Matriz de permisos en código se vuelve difícil de mantener si se añaden roles | Aceptado: requisito actual no prevee roles custom. Si cambia, se migra a tabla de permisos en una change futura (refactor planificado). |
| Frontend expone formulario de alta de usuario con contraseña temporal visible → screenshot/filtración | La contraseña temporal se muestra solo en el toast/modal de éxito del POST y nunca se almacena en estado global. El admin puede regenerarla (no implementado en v1, se puede agregar luego). |
| `require_role` dependency evaluada en cada request añade overhead | La matriz es un dict en memoria; lookup es O(1). No hay query a DB para permisos. Benchmarking se hará si hay problemas de performance. |

## Migration Plan

1. **Schema**: verificar que tabla `usuario` tiene FK a `rol` e índice `empresa_id`. No se requieren migrations destructivas.
2. **Seed**: ejecutar seed de usuario admin por defecto (idempotente).
3. **Deploy**: backend primero (nuevo router `/usuarios` y middleware RBAC no rompen endpoints existentes), luego frontend.
4. **Rollback**: eliminar router y dependencies; no hay datos críticos nuevos que requieran rollback de schema.

## Open Questions

- ¿Se permite que un Administrador cambie su propio rol? → **Respuesta**: No, a menos que exista otro admin activo. Esto evita auto-degradación accidental.
- ¿El endpoint `/usuarios/me` permite cambiar email? → **Respuesta**: Sí, pero se valida unicidad global. El email es el identificador de login.
- ¿Se necesita paginación en el listado de usuarios? → **Respuesta**: Sí, placeholder de paginación con `skip`/`limit` (una carnicería típica tiene <20 usuarios, pero se implementa por consistencia).
