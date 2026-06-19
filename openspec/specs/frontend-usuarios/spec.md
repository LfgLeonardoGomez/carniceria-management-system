# Purpose

TBD: Define the purpose of the frontend-usuarios capability.

## Requirements

### Requirement: Pantalla de gestión de usuarios accesible solo para Administrador
El sistema SHALL mostrar la pantalla de gestión de usuarios únicamente cuando el usuario autenticado tenga rol Administrador. En caso contrario, el usuario debe ser redirigido a otra ruta (por ejemplo, `/dashboard` o `/perfil`).

#### Scenario: Acceso permitido para Administrador
- **WHEN** un usuario con rol Administrador navega a `/usuarios`
- **THEN** el sistema renderiza la pantalla de gestión de usuarios

#### Scenario: Acceso denegado para no administrador
- **WHEN** un usuario con rol Cajero navega a `/usuarios`
- **THEN** el sistema redirige a `/dashboard` y no renderiza la pantalla de gestión

### Requirement: Grid de usuarios con paginación y filtros
El sistema SHALL mostrar un grid de usuarios que liste: nombre completo, email, rol, estado (activo/inactivo), y fecha de creación. Debe soportar paginación y filtros por rol y estado.

#### Scenario: Listado de usuarios
- **WHEN** un Administrador accede a `/usuarios`
- **THEN** el grid muestra los usuarios de la empresa paginados, con opciones de filtrar por rol y estado activo

### Requirement: Formulario de alta de usuario con generación de contraseña temporal
El sistema SHALL proporcionar un formulario de alta de usuario con campos: nombre, apellido, email, rol. Al guardar, debe mostrar un modal con la contraseña temporal generada, visible una sola vez.

#### Scenario: Alta exitosa con contraseña temporal
- **WHEN** un Administrador completa el formulario de alta y presiona "Guardar"
- **THEN** el sistema envía POST `/usuarios`, y al recibir la respuesta exitosa muestra un modal con la contraseña temporal y un botón para copiarla al portapapeles
- **AND** al cerrar el modal, la contraseña temporal ya no es visible en ninguna parte de la UI

#### Scenario: Validación de email duplicado
- **WHEN** un Administrador ingresa un email ya existente en el formulario de alta
- **THEN** el sistema muestra un error visual indicando que el email ya está registrado (tras recibir 409 del backend)

### Requirement: Formulario de edición de usuario
El sistema SHALL permitir editar nombre, apellido, email, rol y estado activo de un usuario existente mediante un formulario accesible desde el grid.

#### Scenario: Edición de usuario
- **WHEN** un Administrador selecciona "Editar" en un usuario del grid
- **THEN** el sistema abre el formulario de edición precargado con los datos actuales
- **AND** al guardar, envía PATCH `/usuarios/{id}` y actualiza el grid

#### Scenario: Desactivación de usuario
- **WHEN** un Administrador desmarca el estado "Activo" en el formulario de edición y guarda
- **THEN** el sistema envía PATCH `/usuarios/{id}` con `activo = false` y actualiza el estado en el grid
- **AND** si el usuario es el último Administrador, muestra un error indicando la operación no está permitida

### Requirement: Pantalla de perfil propio
El sistema SHALL mostrar una pantalla `/perfil` donde cualquier usuario autenticado pueda ver y editar su nombre, apellido y contraseña.

#### Scenario: Visualización de perfil
- **WHEN** cualquier usuario autenticado navega a `/perfil`
- **THEN** el sistema muestra sus datos personales y un formulario para editar nombre, apellido y contraseña

#### Scenario: Cambio de contraseña desde perfil
- **WHEN** un usuario ingresa su contraseña actual, la nueva contraseña y la confirmación
- **THEN** el sistema envía PATCH `/usuarios/me` y muestra un mensaje de éxito o error según la respuesta

### Requirement: Store Zustand para estado de usuarios
El sistema SHALL mantener un store Zustand dedicado al dominio de usuarios que gestione el listado, el usuario seleccionado, y los estados de carga y error.

#### Scenario: Estado global de usuarios
- **WHEN** la pantalla de usuarios se carga
- **THEN** el store Zustand obtiene el listado desde el backend y lo mantiene disponible para componentes
- **AND** cualquier mutación (alta, edición, desactivación) actualiza el store y refleja los cambios en el grid sin recargar la página completa

### Requirement: Protección de rutas por rol en el router
El sistema SHALL proteger las rutas del frontend evaluando el rol del usuario autenticado antes de renderizar componentes. Las rutas protegidas deben ser configurables en el router de la aplicación.

#### Scenario: Router protegido
- **WHEN** el router evalúa una ruta marcada como `requireAdmin: true`
- **THEN** verifica que el usuario tenga rol Administrador; si no, redirige a `/dashboard`
