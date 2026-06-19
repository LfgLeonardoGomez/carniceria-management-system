## ADDED Requirements

### Requirement: Sistema incluye rol superadmin con permisos globales
El sistema SHALL incluir el rol `superadmin` en la matriz RBAC con permisos explícitos globales, sin wildcard.

#### Scenario: Matriz con 5 roles
- **WHEN** el sistema inicia
- **THEN** la matriz RBAC contiene exactamente 5 roles (`superadmin`, `admin`, `encargado`, `cajero`, `vendedor`) con permisos definidos explícitos
- **AND** no es posible modificar la matriz en runtime

### Requirement: Dependency require_role maneja empresa_id NULL
El sistema SHALL permitir que `require_role` funcione correctamente para usuarios con `empresa_id = NULL` (superadmin).

#### Scenario: Superadmin accede a endpoint global
- **WHEN** un `superadmin` con `empresa_id = NULL` invoca un endpoint protegido con `require_role("empresas:create")`
- **THEN** la dependency permite continuar con la ejecución

#### Scenario: Superadmin accede a endpoint de tenant
- **WHEN** un `superadmin` con `empresa_id = NULL` invoca un endpoint protegido con `require_role("ventas:crud")`
- **THEN** la dependency permite continuar con la ejecución porque `superadmin` posee el permiso explícito

## MODIFIED Requirements

### Requirement: Sistema verifica permisos en cada request autenticado
El sistema SHALL verificar que el rol del usuario autenticado posea el permiso requerido para ejecutar un endpoint protegido antes de procesar la lógica de negocio.

#### Scenario: Acceso permitido
- **WHEN** un usuario autenticado con rol que tiene el permiso requerido invoca un endpoint protegido
- **THEN** el sistema ejecuta el endpoint y devuelve la respuesta correspondiente

#### Scenario: Acceso denegado por permisos
- **WHEN** un usuario autenticado con rol que NO tiene el permiso requerido invoca un endpoint protegido
- **THEN** el sistema responde con HTTP 403 Forbidden antes de ejecutar la lógica del endpoint

### Requirement: Dependency require_role verifica permisos contra matriz RBAC
El sistema SHALL exponer una dependency FastAPI `require_role(permiso: str)` que consulte la matriz de permisos inmutable en memoria y valide que el rol del usuario autenticado posea el permiso solicitado.

#### Scenario: Permiso presente en matriz
- **WHEN** `require_role("usuarios:crear")` se evalúa para un usuario con rol `superadmin`
- **THEN** la dependency permite continuar con la ejecución del endpoint

#### Scenario: Permiso ausente en matriz
- **WHEN** `require_role("empresas:delete")` se evalúa para un usuario con rol `admin`
- **THEN** la dependency responde con HTTP 403 Forbidden

### Requirement: Middleware inyecta objeto de usuario con permisos
El sistema SHALL extender la dependency `get_current_user` para que retorne un objeto que incluya, además de los datos del usuario, el conjunto de permisos asociados a su rol según la matriz RBAC.

#### Scenario: Inyección de usuario con permisos
- **WHEN** cualquier endpoint autenticado invoca `get_current_user`
- **THEN** el objeto recibido contiene `id`, `email`, `nombre`, `apellido`, `rol`, `empresa_id`, `activo` y la lista de `permisos` disponibles para ese rol
- **AND** si el usuario es `superadmin`, `empresa_id` puede ser `NULL`

### Requirement: Matriz RBAC es inmutable y definida en código
El sistema SHALL mantener la matriz de permisos como un diccionario Python inmutable (por ejemplo, constante en `common/rbac.py`) que asocie cada rol con sus permisos permitidos.

#### Scenario: Roles y permisos fijos
- **WHEN** el sistema inicia
- **THEN** la matriz RBAC contiene exactamente los 5 roles (`superadmin`, `admin`, `encargado`, `cajero`, `vendedor`) con los permisos definidos en la base de conocimiento (`03_actores_y_roles.md` y `DECISIONES/RBAC-SUPERADMIN-PENDIENTE.md`)
- **AND** no es posible modificar la matriz en runtime
- **AND** el rol `admin` NO tiene wildcard `*`

### Requirement: Endpoints existentes protegidos por RBAC
El sistema SHALL aplicar `require_role` a los endpoints de `C-03 empresa-config` para que solo usuarios con rol apropiado puedan gestionar la empresa.

#### Scenario: Creación de empresa protegida
- **WHEN** un usuario con rol distinto a `superadmin` intenta enviar POST `/empresas`
- **THEN** el sistema responde con HTTP 403 Forbidden

#### Scenario: Lectura de empresas según rol
- **WHEN** un `superadmin` envía GET `/empresas`
- **THEN** el sistema devuelve todas las empresas
- **WHEN** un `admin` envía GET `/empresas`
- **THEN** el sistema devuelve únicamente la empresa cuyo `id` coincide con `admin.empresa_id`
