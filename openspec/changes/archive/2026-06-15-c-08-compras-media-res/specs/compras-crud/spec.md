## ADDED Requirements

### Requirement: Compra se registra con datos obligatorios y cálculos automáticos
El sistema SHALL permitir registrar una compra de media res con los campos: fecha, proveedor_id, cantidad_medias_reses (>= 1), peso_total (> 0, kilos), costo_total (> 0, moneda), observaciones (opcional). El sistema SHALL calcular automáticamente `costo_por_kilo = costo_total / peso_total` con precisión de 3 decimales. El sistema SHALL validar división por cero (peso_total = 0) y rechazar la operación. Toda compra SHALL pertenecer a una empresa (`empresa_id`).

#### Scenario: Registro exitoso con datos mínimos
- **WHEN** un usuario con rol Administrador o Encargado envía POST `/compras` con `fecha`, `proveedor_id`, `cantidad_medias_reses`, `peso_total`, `costo_total` válidos
- **THEN** el sistema crea la compra, calcula `costo_por_kilo`, y devuelve 201 con el recurso completo incluyendo `costo_por_kilo`

#### Scenario: Cálculo automático de costo por kilo
- **WHEN** un usuario envía POST `/compras` con `peso_total = 100.500` y `costo_total = 50000.00`
- **THEN** el sistema calcula `costo_por_kilo = 497.512` (redondeo a 3 decimales) y lo almacena

#### Scenario: División por cero protegida
- **WHEN** un usuario envía POST `/compras` con `peso_total = 0`
- **THEN** el sistema devuelve 422 Unprocessable Entity con mensaje "peso_total debe ser mayor a 0"

#### Scenario: Proveedor inexistente
- **WHEN** un usuario envía POST `/compras` con `proveedor_id` que no existe en su empresa
- **THEN** el sistema devuelve 404 Not Found

#### Scenario: Rol sin permiso intenta registrar
- **WHEN** un usuario con rol Cajero o Vendedor envía POST `/compras`
- **THEN** el sistema devuelve 403 Forbidden

#### Scenario: Proveedor de otra empresa
- **WHEN** un usuario envía POST `/compras` con `proveedor_id` de otra empresa
- **THEN** el sistema devuelve 404 Not Found

### Requirement: Compra se actualiza manteniendo integridad y recalculando costos
El sistema SHALL permitir actualizar una compra existente. Las actualizaciones de `peso_total` o `costo_total` SHALL recalcular `costo_por_kilo`. El `proveedor_id` y `empresa_id` SHALL ser inmutables.

#### Scenario: Actualización exitosa con recálculo
- **WHEN** un usuario con rol Administrador o Encargado envía PUT `/compras/{id}` con `peso_total = 120.000` y `costo_total = 60000.00`
- **THEN** el sistema actualiza la compra y recalcula `costo_por_kilo = 500.000`

#### Scenario: Actualización de compra anulada
- **WHEN** un usuario envía PUT `/compras/{id}` de una compra con estado `anulada`
- **THEN** el sistema devuelve 409 Conflict con mensaje "No se puede modificar una compra anulada"

#### Scenario: Actualización de compra ya desposteada
- **WHEN** (post-C-09) un usuario envía PUT `/compras/{id}` de una compra que tiene despostes asociados
- **THEN** el sistema devuelve 409 Conflict con mensaje "No se puede modificar una compra ya desposteada"

### Requirement: Compra se anula (soft delete) preservando historial
El sistema SHALL permitir la anulación de una compra mediante cambio de estado a `anulada`. Nunca SHALL permitir eliminación física (RN-GLOBAL-02). La anulación SHALL preservar el historial del proveedor y SHALL revertir el movimiento de stock asociado.

#### Scenario: Anulación exitosa
- **WHEN** un usuario con rol Administrador o Encargado envía DELETE `/compras/{id}` de una compra sin despostes
- **THEN** el sistema marca estado `anulada`, genera movimiento de stock inverso (salida), y devuelve 204 No Content

#### Scenario: Anulación de compra ya desposteada
- **WHEN** (post-C-09) un usuario envía DELETE `/compras/{id}` de una compra con despostes asociados
- **THEN** el sistema devuelve 409 Conflict con mensaje "No se puede anular una compra ya desposteada"

#### Scenario: Anulación ya anulada
- **WHEN** un usuario envía DELETE `/compras/{id}` de una compra ya anulada
- **THEN** el sistema devuelve 409 Conflict

### Requirement: Compras se listan con filtros y paginación
El sistema SHALL proveer un endpoint de listado de compras filtrado por `empresa_id`. SHALL soportar filtros por `proveedor_id`, rango de fechas (`fecha_desde`, `fecha_hasta`), y estado. SHALL soportar paginación con `skip` y `limit`. El orden por defecto SHALL ser fecha descendente.

#### Scenario: Listado paginado con filtros
- **WHEN** un usuario envía GET `/compras?skip=0&limit=10&proveedor_id=abc&fecha_desde=2024-01-01&fecha_hasta=2024-12-31`
- **THEN** el sistema devuelve compras filtradas, paginadas, ordenadas por fecha descendente

#### Scenario: Listado excluye anuladas por defecto
- **WHEN** un usuario envía GET `/compras` sin parámetro de estado
- **THEN** el sistema devuelve solo compras con estado `activa`

#### Scenario: Listado incluye anuladas cuando se solicita
- **WHEN** un usuario envía GET `/compras?incluir_anuladas=true`
- **THEN** el sistema devuelve todas las compras de la empresa

#### Scenario: Aislamiento multi-tenant en listado
- **WHEN** un usuario de la empresa A solicita GET `/compras`
- **THEN** el sistema NO devuelve compras de la empresa B

### Requirement: Compra se consulta individualmente
El sistema SHALL permitir obtener una compra por su ID, validando que pertenezca a la empresa del usuario autenticado.

#### Scenario: Consulta exitosa
- **WHEN** un usuario envía GET `/compras/{id}` de una compra de su empresa
- **THEN** el sistema devuelve 200 con el recurso completo incluyendo datos del proveedor

#### Scenario: Consulta de compra anulada
- **WHEN** un usuario envía GET `/compras/{id}` de una compra anulada
- **THEN** el sistema devuelve 200 con el recurso completo incluyendo estado `anulada`

#### Scenario: Consulta de compra ajena
- **WHEN** un usuario envía GET `/compras/{id}` de una compra de otra empresa
- **THEN** el sistema devuelve 404 Not Found

### Requirement: Frontend provee grid, formulario y ficha de compras
El sistema frontend SHALL mostrar una pantalla de listado (grid) de compras con filtros por fecha y proveedor, paginación y botones de acción. SHALL permitir crear y editar compras mediante un formulario validado. SHALL mostrar una ficha de compra con detalle, costo por kilo destacado, y datos del proveedor.

#### Scenario: Acceso según rol
- **WHEN** un usuario con rol Administrador o Encargado navega a `/compras`
- **THEN** el sistema renderiza el grid de compras

#### Scenario: Rol sin acceso redirigido
- **WHEN** un usuario con rol Cajero o Vendedor intenta acceder a `/compras`
- **THEN** el sistema redirige a la página principal o muestra 403

#### Scenario: Formulario valida peso y costo en tiempo real
- **WHEN** un usuario ingresa `peso_total = 0` o `costo_total = 0` en el formulario
- **THEN** el frontend muestra error inmediato sin enviar al backend

#### Scenario: Ficha muestra costo por kilo calculado
- **WHEN** un usuario abre la ficha de una compra
- **THEN** el frontend muestra `costo_por_kilo` destacado junto con peso total y costo total
