## ADDED Requirements

### Requirement: Create a client
The system SHALL allow authorized users to create a client record within their tenant.

#### Scenario: Successful client creation
- **WHEN** an authorized user submits a valid client payload to `POST /clientes`
- **THEN** the system creates the client with `empresa_id` set to the user's tenant
- **AND** returns the created client with a generated `id`

#### Scenario: Rejected client creation without tenant
- **WHEN** an unauthenticated or cross-tenant request attempts to create a client
- **THEN** the system rejects the request with `403 Forbidden`

### Requirement: Update a client
The system SHALL allow authorized users to update client fields within their tenant.

#### Scenario: Successful client update
- **WHEN** an authorized user submits a valid update payload to `PUT /clientes/{id}`
- **THEN** the system updates the client fields
- **AND** returns the updated client

#### Scenario: Update rejected for cross-tenant client
- **WHEN** an authorized user attempts to update a client belonging to another tenant
- **THEN** the system rejects the request with `404 Not Found`

### Requirement: Delete (deactivate) a client
The system SHALL allow authorized users to deactivate a client (soft delete) within their tenant.

#### Scenario: Successful client deactivation
- **WHEN** an authorized user sends `DELETE /clientes/{id}`
- **THEN** the system sets `activo = false`
- **AND** the client remains in the database for historical reference

### Requirement: List clients with filters
The system SHALL return a paginated list of clients filtered by tenant and optional query parameters.

#### Scenario: List all clients for tenant
- **WHEN** an authorized user sends `GET /clientes`
- **THEN** the system returns only clients where `empresa_id` matches the user's tenant
- **AND** supports pagination via `limit` and `offset`

#### Scenario: Filter clients by type
- **WHEN** an authorized user sends `GET /clientes?tipo_cliente=mayorista`
- **THEN** the system returns only clients of that type within the tenant

#### Scenario: Search clients by name or CUIT
- **WHEN** an authorized user sends `GET /clientes?q=Gomez`
- **THEN** the system returns clients matching the search term in `nombre`, `apellido`, `razon_social`, or `cuit`

### Requirement: Get client detail
The system SHALL return the full profile of a single client including current balance.

#### Scenario: Retrieve client detail
- **WHEN** an authorized user sends `GET /clientes/{id}`
- **THEN** the system returns the client object with fields: `id`, `nombre`, `apellido`, `razon_social`, `cuit`, `telefono`, `email`, `direccion`, `tipo_cliente`, `limite_cuenta_corriente`, `saldo_actual`, `activo`, `created_at`, `updated_at`

### Requirement: Retrieve client purchase history
The system SHALL return a paginated list of sales associated with a client.

#### Scenario: Successful history retrieval
- **WHEN** an authorized user sends `GET /clientes/{id}/historial`
- **THEN** the system returns sales where `cliente_id = {id}` and `empresa_id` matches the tenant
- **AND** results are ordered by `fecha` descending
- **AND** pagination is supported via `limit` and `offset`

#### Scenario: History for non-existent client
- **WHEN** an authorized user requests history for a client that does not exist or belongs to another tenant
- **THEN** the system returns `404 Not Found`

### Requirement: Expose current account balance
The system SHALL expose `saldo_actual` as part of the client read response.

#### Scenario: Client with zero balance
- **WHEN** a client has no cuenta corriente movements
- **THEN** `saldo_actual` is `0.00`

#### Scenario: Client with positive balance (debt)
- **WHEN** a client has outstanding debt
- **THEN** `saldo_actual` reflects the debt amount

### Requirement: Enforce RBAC on client endpoints
The system SHALL enforce role-based access control on all `/clientes` endpoints.

#### Scenario: Administrator full access
- **WHEN** a user with role `Administrador` accesses any `/clientes` endpoint
- **THEN** all CRUD operations are permitted

#### Scenario: Encargado limited access
- **WHEN** a user with role `Encargado` accesses `/clientes`
- **THEN** they may create, read, and update clients but NOT delete

#### Scenario: Cajero limited access
- **WHEN** a user with role `Cajero` accesses `/clientes`
- **THEN** they may create, read, and update clients but NOT delete

#### Scenario: Vendedor denied access
- **WHEN** a user with role `Vendedor` accesses `/clientes`
- **THEN** the system returns `403 Forbidden`

### Requirement: Multi-tenant isolation for client data
The system SHALL ensure client data is strictly isolated by tenant.

#### Scenario: Tenant isolation enforced
- **WHEN** any query or mutation targets the `cliente` table
- **THEN** the system always filters by `empresa_id` derived from the authenticated user's JWT claim
- **AND** a row-level security policy on `cliente` prevents cross-tenant access at the database level

#### Scenario: Cross-tenant read blocked
- **WHEN** an authenticated user from tenant A attempts to read `GET /clientes/{id}` where the client belongs to tenant B
- **THEN** the system returns `404 Not Found`
