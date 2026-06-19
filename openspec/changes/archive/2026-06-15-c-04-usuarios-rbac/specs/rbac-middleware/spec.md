## ADDED Requirements

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
- **WHEN** `require_role("usuarios:crear")` se evalúa para un usuario con rol Administrador
- **THEN** la dependency permite continuar con la ejecución del endpoint

#### Scenario: Permiso ausente en matriz
- **WHEN** `require_role("usuarios:crear")` se evalúa para un usuario con rol Vendedor
- **THEN** la dependency responde con HTTP 403 Forbidden

### Requirement: Middleware inyecta objeto de usuario con permisos
El sistema SHALL extender la dependency `get_current_user` para que retorne un objeto que incluya, además de los datos del usuario, el conjunto de permisos asociados a su rol según la matriz RBAC.

#### Scenario: Inyección de usuario con permisos
- **WHEN** cualquier endpoint autenticado invoca `get_current_user`
- **THEN** el objeto recibido contiene `id`, `email`, `nombre`, `apellido`, `rol`, `empresa_id`, `activo` y la lista de `permisos` disponibles para ese rol

### Requirement: Matriz RBAC es inmutable y definida en código
El sistema SHALL mantener la matriz de permisos como un diccionario Python inmutable (por ejemplo, constante en `common/rbac.py`) que asocie cada rol con sus permisos permitidos.

#### Scenario: Roles y permisos fijos
- **WHEN** el sistema inicia
- **THEN** la matriz RBAC contiene exactamente los 4 roles (Administrador, Encargado, Cajero, Vendedor) con los permisos definidos en la base de conocimiento (`03_actores_y_roles.md`)
- **AND** no es posible modificar la matriz en runtime

### Requirement: Endpoints existentes protegidos por RBAC
El sistema SHALL aplicar `require_role` a los endpoints de `C-03 empresa-config` para que solo usuarios con rol Administrador puedan gestionar la empresa.

#### Scenario: Empresa protegida
- **WHEN** un usuario con rol distinto a Administrador intenta acceder a endpoints CRUD de `/empresas`
- **THEN** el sistema responde con HTTP 403 Forbidden
