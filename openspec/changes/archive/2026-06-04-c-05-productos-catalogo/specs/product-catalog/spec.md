## ADDED Requirements

### Requirement: Crear producto
El sistema SHALL permitir la creación de un producto asociado a la empresa autenticada.

#### Scenario: Creación exitosa
- **WHEN** un usuario autenticado con rol Administrador o Encargado envía un request POST /productos con PLU, nombre, categoría_id, precio_publico, precio_mayorista, costo_por_kilo, stock_actual, stock_minimo
- **THEN** el sistema crea el producto, calcula el margen automáticamente, devuelve 201 Created y el producto con su margen calculado

#### Scenario: PLU duplicado en la misma empresa
- **WHEN** un usuario intenta crear un producto con un PLU que ya existe para su empresa_id
- **THEN** el sistema rechaza la operación con 409 Conflict y mensaje "PLU ya existe en esta empresa"

#### Scenario: Precios negativos
- **WHEN** un usuario envía precio_publico, precio_mayorista o costo_por_kilo menor que 0
- **THEN** el sistema rechaza la operación con 422 Unprocessable Entity

### Requirement: Editar producto
El sistema SHALL permitir la edición de un producto existente de la empresa autenticada.

#### Scenario: Edición exitosa
- **WHEN** un usuario autenticado envía PUT /productos/{id} con campos válidos
- **THEN** el sistema actualiza el producto, recalcula el margen si cambió precio_publico o costo_por_kilo, y devuelve 200 OK

#### Scenario: Editar producto de otra empresa
- **WHEN** un usuario intenta editar un producto cuyo empresa_id no coincide con el del usuario autenticado
- **THEN** el sistema devuelve 404 Not Found

### Requirement: Listar y buscar productos
El sistema SHALL permitir listar productos con paginación, búsqueda por PLU o nombre, y filtro por categoría.

#### Scenario: Búsqueda por PLU exacto
- **WHEN** un usuario envía GET /productos?search={plu}
- **THEN** el sistema devuelve productos cuyo PLU coincida exactamente o parcialmente con el término, filtrados por empresa_id, paginados

#### Scenario: Búsqueda por nombre parcial
- **WHEN** un usuario envía GET /productos?search={nombre_fragmento}
- **THEN** el sistema devuelve productos cuyo nombre contenga el fragmento (case-insensitive), filtrados por empresa_id, paginados

#### Scenario: Listado con paginación por defecto
- **WHEN** un usuario envía GET /productos sin parámetros de búsqueda
- **THEN** el sistema devuelve todos los productos activos de su empresa ordenados por nombre, paginados (page=1, page_size=20 por defecto)

### Requirement: Baja lógica de producto
El sistema SHALL permitir marcar un producto como inactivo sin eliminarlo físicamente.

#### Scenario: Desactivar producto
- **WHEN** un usuario envía PATCH /productos/{id} con { activo: false }
- **THEN** el sistema marca el producto como inactivo, devuelve 200 OK, y el producto ya no aparece en búsquedas por defecto

#### Scenario: Reactivar producto
- **WHEN** un usuario envía PATCH /productos/{id} con { activo: true }
- **THEN** el sistema marca el producto como activo y devuelve 200 OK

### Requirement: Calcular margen automáticamente
El sistema SHALL calcular y almacenar el margen de un producto cada vez que se crea o actualiza.

#### Scenario: Margen con precio público mayor que costo
- **WHEN** se crea o actualiza un producto con precio_publico = 1000.00 y costo_por_kilo = 600.00
- **THEN** el margen se calcula como 0.4000 (40.00%)

#### Scenario: Margen con precio público cero
- **WHEN** se crea o actualiza un producto con precio_publico = 0 y costo_por_kilo = 0
- **THEN** el margen se almacena como 0.0000 para evitar división por cero

### Requirement: Aislamiento multi-tenant de productos
El sistema SHALL garantizar que un producto solo sea visible y modificable por usuarios de su empresa.

#### Scenario: Acceso a producto de otra empresa
- **WHEN** un usuario autenticado consulta GET /productos/{id} de un producto perteneciente a otra empresa
- **THEN** el sistema devuelve 404 Not Found

#### Scenario: Listado filtrado por empresa
- **WHEN** un usuario autenticado solicita el listado de productos
- **THEN** el sistema solo devuelve productos cuyo empresa_id coincide con el del usuario autenticado
