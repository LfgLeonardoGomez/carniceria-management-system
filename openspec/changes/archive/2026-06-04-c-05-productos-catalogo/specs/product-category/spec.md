## ADDED Requirements

### Requirement: Crear categoría de producto
El sistema SHALL permitir la creación de categorías de producto personalizables por empresa.

#### Scenario: Creación exitosa
- **WHEN** un usuario autenticado envía POST /categorias-producto con nombre válido
- **THEN** el sistema crea la categoría asociada a la empresa autenticada y devuelve 201 Created

#### Scenario: Nombre duplicado en la misma empresa
- **WHEN** un usuario intenta crear una categoría con un nombre que ya existe para su empresa
- **THEN** el sistema rechaza la operación con 409 Conflict

### Requirement: Listar categorías de producto
El sistema SHALL permitir listar las categorías de la empresa autenticada, incluyendo las seed iniciales.

#### Scenario: Listado con seed data
- **WHEN** un usuario autenticado solicita GET /categorias-producto
- **THEN** el sistema devuelve todas las categorías de su empresa (seed + personalizadas)

### Requirement: Seed inicial de categorías
El sistema SHALL crear automáticamente 5 categorías por defecto al registrar una nueva empresa.

#### Scenario: Creación de empresa con categorías seed
- **WHEN** se crea una nueva empresa en el sistema
- **THEN** el sistema crea automáticamente las categorías: Carne vacuna, Carne de cerdo, Pollo, Embutidos, Otros, asociadas a esa empresa

### Requirement: Editar categoría de producto
El sistema SHALL permitir renombrar una categoría personalizada de la empresa.

#### Scenario: Edición exitosa
- **WHEN** un usuario envía PUT /categorias-producto/{id} con un nuevo nombre válido
- **THEN** el sistema actualiza el nombre y devuelve 200 OK

#### Scenario: Editar categoría seed
- **WHEN** un usuario intenta editar una categoría seed del sistema
- **THEN** el sistema permite la edición del nombre (las seeds son copias por empresa, no globales)

### Requirement: Eliminar categoría de producto
El sistema SHALL permitir eliminar una categoría solo si no tiene productos asociados.

#### Scenario: Eliminación exitosa
- **WHEN** un usuario envía DELETE /categorias-producto/{id} y la categoría no tiene productos asociados
- **THEN** el sistema elimina la categoría y devuelve 204 No Content

#### Scenario: Eliminación con productos asociados
- **WHEN** un usuario intenta eliminar una categoría que tiene productos asociados
- **THEN** el sistema rechaza la operación con 409 Conflict y mensaje "La categoría tiene productos asociados"

### Requirement: Aislamiento multi-tenant de categorías
El sistema SHALL garantizar que las categorías solo sean visibles y modificables por usuarios de su empresa.

#### Scenario: Acceso a categoría de otra empresa
- **WHEN** un usuario consulta una categoría de otra empresa
- **THEN** el sistema devuelve 404 Not Found
