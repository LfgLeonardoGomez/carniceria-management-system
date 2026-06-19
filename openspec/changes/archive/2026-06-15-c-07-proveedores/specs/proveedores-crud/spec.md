## ADDED Requirements

### Requirement: Proveedor se registra con datos obligatorios y opcionales
El sistema SHALL permitir registrar un proveedor con los campos: nombre (obligatorio), CUIT (opcional, 11 dígitos argentinos), teléfono (opcional), email (opcional), dirección (opcional). Todo proveedor SHALL pertenecer a una empresa (`empresa_id`) y no podrá ser compartido entre empresas (RN-PROV-01).

#### Scenario: Registro exitoso con datos mínimos
- **WHEN** un usuario con rol Administrador o Encargado envía un POST a `/proveedores` con solo `nombre` y `empresa_id` válido
- **THEN** el sistema crea el proveedor y devuelve 201 con el recurso creado

#### Scenario: Registro con CUIT inválido
- **WHEN** un usuario envía un POST a `/proveedores` con `cuit` que no tiene 11 dígitos numéricos
- **THEN** el sistema devuelve 422 Unprocessable Entity con mensaje de error en el campo `cuit`

#### Scenario: Registro duplicado de CUIT en la misma empresa
- **WHEN** un usuario envía un POST a `/proveedores` con un `cuit` que ya existe para la misma `empresa_id`
- **THEN** el sistema devuelve 409 Conflict con mensaje "CUIT ya registrado para esta empresa"

#### Scenario: Usuario sin permiso intenta registrar
- **WHEN** un usuario con rol Cajero o Vendedor envía un POST a `/proveedores`
- **THEN** el sistema devuelve 403 Forbidden

### Requirement: Proveedor se actualiza manteniendo integridad
El sistema SHALL permitir actualizar los datos de un proveedor existente. El `empresa_id` SHALL ser inmutable. El `cuit` actualizado SHALL seguir siendo único por empresa si se proporciona.

#### Scenario: Actualización exitosa
- **WHEN** un usuario con rol Administrador o Encargado envía PUT a `/proveedores/{id}` con datos válidos
- **THEN** el sistema actualiza el proveedor y devuelve 200 con el recurso actualizado

#### Scenario: Actualización de CUIT a valor duplicado
- **WHEN** un usuario envía PUT a `/proveedores/{id}` con un `cuit` que ya pertenece a otro proveedor de la misma empresa
- **THEN** el sistema devuelve 409 Conflict

### Requirement: Proveedor se elimina lógicamente
El sistema SHALL permitir la "eliminación" de un proveedor mediante baja lógica (`activo = false`). Nunca SHALL permitir eliminación física (RN-GLOBAL-02). La baja lógica SHALL preservar el historial de compras asociado.

#### Scenario: Baja lógica exitosa
- **WHEN** un usuario con rol Administrador o Encargado envía DELETE a `/proveedores/{id}`
- **THEN** el sistema marca `activo = false` y devuelve 204 No Content

#### Scenario: Listado excluye inactivos por defecto
- **WHEN** un usuario solicita GET `/proveedores` sin parámetro adicional
- **THEN** el sistema devuelve solo proveedores con `activo = true`

#### Scenario: Listado incluye inactivos cuando se solicita
- **WHEN** un usuario solicita GET `/proveedores?incluir_inactivos=true`
- **THEN** el sistema devuelve todos los proveedores de la empresa

### Requirement: Proveedores se listan con búsqueda y paginación
El sistema SHALL proveer un endpoint de listado de proveedores filtrado por `empresa_id` del usuario autenticado. SHALL soportar búsqueda por `nombre` (case-insensitive, partial match) y paginación con `skip` y `limit`.

#### Scenario: Listado paginado con búsqueda
- **WHEN** un usuario autenticado envía GET `/proveedores?skip=0&limit=20&nombre=carne`
- **THEN** el sistema devuelve los proveedores de su empresa cuyo nombre contiene "carne" (insensible a mayúsculas), paginados

#### Scenario: Aislamiento multi-tenant
- **WHEN** un usuario de la empresa A solicita GET `/proveedores`
- **THEN** el sistema NO devuelve proveedores de la empresa B

### Requirement: Proveedor se consulta individualmente
El sistema SHALL permitir obtener un proveedor por su ID, validando que pertenezca a la empresa del usuario autenticado.

#### Scenario: Consulta exitosa
- **WHEN** un usuario envía GET `/proveedores/{id}` de un proveedor de su empresa
- **THEN** el sistema devuelve 200 con el recurso completo

#### Scenario: Consulta de proveedor ajeno
- **WHEN** un usuario envía GET `/proveedores/{id}` de un proveedor de otra empresa
- **THEN** el sistema devuelve 404 Not Found (no 403, para evitar泄露 de existencia)

### Requirement: Historial de compras es inmutable y de solo lectura
El sistema SHALL proveer un endpoint `GET /proveedores/{id}/historial` que liste las compras de media res asociadas al proveedor. El historial SHALL ser inmutable (RN-PROV-02). Si la tabla `Compra` aún no existe, el endpoint SHALL devolver `[]` sin error.

#### Scenario: Proveedor sin compras
- **WHEN** un usuario consulta GET `/proveedores/{id}/historial` de un proveedor sin compras registradas
- **THEN** el sistema devuelve 200 con array vacío `[]`

#### Scenario: Proveedor con compras futuras
- **WHEN** (post-C-08) un usuario consulta GET `/proveedores/{id}/historial` de un proveedor con compras
- **THEN** el sistema devuelve 200 con lista de compras ordenadas por fecha descendente

#### Scenario: Aislamiento en historial
- **WHEN** un usuario consulta GET `/proveedores/{id}/historial` de un proveedor de otra empresa
- **THEN** el sistema devuelve 404 Not Found

### Requirement: Frontend provee grid, formulario y ficha de proveedores
El sistema frontend SHALL mostrar una pantalla de listado (grid) de proveedores con búsqueda, paginación y botones de acción. SHALL permitir crear y editar proveedores mediante un formulario validado. SHALL mostrar una ficha de proveedor con sus datos y un panel de historial de compras.

#### Scenario: Acceso según rol
- **WHEN** un usuario con rol Administrador o Encargado navega a `/proveedores`
- **THEN** el sistema renderiza el grid de proveedores

#### Scenario: Rol sin acceso redirigido
- **WHEN** un usuario con rol Cajero o Vendedor intenta acceder a `/proveedores`
- **THEN** el sistema redirige a la página principal o muestra 403

#### Scenario: Formulario valida CUIT en tiempo real
- **WHEN** un usuario escribe un CUIT inválido en el formulario de proveedor
- **THEN** el frontend muestra error inmediato sin enviar al backend

#### Scenario: Ficha muestra historial vacío
- **WHEN** un usuario abre la ficha de un proveedor
- **THEN** el frontend muestra los datos del proveedor y un panel de historial con mensaje "Sin compras registradas"
