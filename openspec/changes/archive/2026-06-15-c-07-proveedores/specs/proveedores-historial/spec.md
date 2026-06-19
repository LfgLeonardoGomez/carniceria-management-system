## ADDED Requirements

### Requirement: Historial de compras de proveedor es inmutable y consultable
El sistema SHALL proveer un endpoint `GET /proveedores/{id}/historial` que devuelva el historial completo de compras de media res asociadas a un proveedor. Este historial SHALL ser inmutable: ninguna operación de modificación o eliminación de compras SHALL afectar el historial ya registrado (RN-PROV-02). El historial SHALL estar filtrado por `empresa_id` del usuario autenticado.

#### Scenario: Historial vacío para proveedor nuevo
- **WHEN** un usuario con permisos consulta GET `/proveedores/{id}/historial` de un proveedor que aún no tiene compras
- **THEN** el sistema devuelve 200 con un array vacío `[]` y metadatos de paginación con `total: 0`

#### Scenario: Historial con compras registradas
- **WHEN** (post-C-08) un usuario consulta GET `/proveedores/{id}/historial` de un proveedor con compras previas
- **THEN** el sistema devuelve 200 con array de compras ordenadas por fecha descendente (más reciente primero), cada elemento incluyendo: `id`, `fecha`, `cantidad_medias_reses`, `peso_total`, `costo_total`, `costo_por_kilo`, `observaciones`

#### Scenario: Paginación del historial
- **WHEN** un usuario envía GET `/proveedores/{id}/historial?skip=0&limit=10`
- **THEN** el sistema devuelve solo las 10 compras más recientes y metadatos `total`, `skip`, `limit`

#### Scenario: Aislamiento multi-tenant en historial
- **WHEN** un usuario de la empresa A consulta GET `/proveedores/{id}/historial` donde el proveedor `{id}` pertenece a la empresa B
- **THEN** el sistema devuelve 404 Not Found

#### Scenario: Rol sin permiso de lectura
- **WHEN** un usuario con rol Vendedor consulta GET `/proveedores/{id}/historial`
- **THEN** el sistema devuelve 403 Forbidden

### Requirement: Datos del historial son inmutables
El sistema SHALL garantizar que los registros de compra en el historial de un proveedor no puedan ser modificados ni eliminados físicamente. Cualquier anulación de compra (post-C-08) SHALL generar un registro de anulación separado sin alterar el historial original (RN-PROV-02, RN-GLOBAL-01).

#### Scenario: Anulación de compra no borra del historial
- **WHEN** (post-C-08) una compra asociada a un proveedor es anulada
- **THEN** el historial del proveedor sigue mostrando la compra original con estado `anulada` y la razón de anulación en un campo separado

#### Scenario: Proveedor dado de baja lógica conserva historial
- **WHEN** un proveedor con `activo = false` es consultado en su historial
- **THEN** el sistema sigue devolviendo todas las compras históricas asociadas
