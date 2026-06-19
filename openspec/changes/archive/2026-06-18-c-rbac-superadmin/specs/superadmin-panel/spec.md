## ADDED Requirements

### Requirement: Superadmin puede ver grid de empresas
El sistema SHALL mostrar en el panel de superadmin un listado de todas las empresas con su admin asignado, estado, y botón de impersonación.

#### Scenario: Visualización de empresas
- **WHEN** un `superadmin` navega a `/admin/soporte`
- **THEN** el frontend muestra un grid con todas las empresas, mostrando nombre, CUIT, admin asignado, y fecha de creación
- **AND** cada fila tiene un botón "Ingresar como admin"

### Requirement: Superadmin puede ver grid de usuarios globales
El sistema SHALL mostrar en el panel de superadmin un listado de todos los usuarios del sistema sin filtrar por empresa.

#### Scenario: Visualización de usuarios globales
- **WHEN** un `superadmin` navega a la pestaña "Usuarios" en `/admin/soporte`
- **THEN** el frontend muestra todos los usuarios con su rol, empresa (o "Global" si es superadmin), y estado activo/inactivo

### Requirement: Frontend detecta modo impersonación
El sistema SHALL mostrar un banner persistente cuando el usuario está operando con un JWT de impersonación.

#### Scenario: Banner de impersonación visible
- **WHEN** el frontend detecta `original_role = "superadmin"` en el JWT actual
- **THEN** muestra un banner superior indicando "Modo soporte: operando como admin de <nombre_empresa>"
- **AND** muestra un botón "Volver a superadmin" que cierra la sesión de impersonación y redirige al panel de superadmin

### Requirement: Rutas de superadmin están protegidas
El sistema SHALL restringir el acceso a `/admin/soporte` y `/admin/empresas` únicamente a usuarios con rol `superadmin`.

#### Scenario: Acceso denegado a no superadmin
- **WHEN** un usuario con rol `admin` intenta navegar a `/admin/soporte`
- **THEN** el frontend redirige a `/` o muestra página 403

#### Scenario: Acceso permitido a superadmin
- **WHEN** un usuario con rol `superadmin` navega a `/admin/soporte`
- **THEN** el frontend carga el panel de superadmin
