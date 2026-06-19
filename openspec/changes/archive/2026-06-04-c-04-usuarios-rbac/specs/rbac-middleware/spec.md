## ADDED Requirements

### Requirement: Middleware RBAC verifica permisos por recurso
El sistema SHALL validar que el rol del usuario autenticado tenga permiso sobre el recurso y operación solicitados antes de ejecutar el endpoint.

#### Scenario: Acceso permitido
- **WHEN** un usuario con rol Encargado envía una petición a un endpoint que requiere permiso de stock
- **AND** la matriz RBAC asigna permiso de stock al rol Encargado
- **THEN** el sistema procesa la petición normalmente

#### Scenario: Acceso denegado por rol
- **WHEN** un usuario con rol Vendedor envía una petición a un endpoint que requiere permiso de compras
- **AND** la matriz RBAC no asigna permiso de compras al rol Vendedor
- **THEN** el sistema responde con HTTP 403 Forbidden
- **AND** el mensaje indica permiso insuficiente

#### Scenario: Endpoint público no requiere RBAC
- **WHEN** se accede a /login, /recuperar-contrasena o /restablecer-contrasena
- **THEN** el middleware RBAC no se evalúa
- **AND** la petición procede sin autenticación

### Requirement: Matriz de permisos es inmutable en runtime
El sistema SHALL utilizar una matriz de permisos definida en código que no pueda ser modificada en runtime.

#### Scenario: Roles y permisos predefinidos
- **WHEN** el sistema inicia
- **THEN** la matriz RBAC contiene exactamente 4 roles: Administrador, Encargado, Cajero, Vendedor
- **AND** cada rol tiene asignados los permisos definidos en la matriz del KB

### Requirement: Claims JWT incluyen rol del usuario
El sistema SHALL incluir el nombre del rol del usuario en los claims del JWT access token.

#### Scenario: Token con rol correcto
- **WHEN** un usuario inicia sesión
- **THEN** el access token contiene el claim "rol" con el nombre de su rol asignado
- **AND** el middleware RBAC utiliza este claim para la verificación de permisos
