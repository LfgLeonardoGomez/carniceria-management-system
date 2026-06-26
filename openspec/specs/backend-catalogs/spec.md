# backend-catalogs Specification

## Purpose
TBD - created by archiving change c-22-catalogos-permisos-fix. Update Purpose after archive.
## Requirements
### Requirement: Endpoint `GET /desposte/tipos` lista los tipos de corte

El sistema SHALL exponer un endpoint `GET /desposte/tipos` que retorna la lista de los 12 tipos de corte fijos del sistema, ordenados alfabéticamente por nombre.

#### Scenario: Endpoint devuelve los 12 tipos de corte
- **WHEN** un usuario autenticado con permiso `desposte:read` hace `GET /desposte/tipos`
- **THEN** el endpoint responde 200 con un array de 12 objetos `TipoCorteRead { id, nombre }`
- **AND** los nombres coinciden con el catálogo: Asado, Bola de lomo, Costilla, Cuadril, Lomo, Matambre, Molida, Nalga, Osobuco, Otros, Peceto, Vacío

#### Scenario: Endpoint requiere permiso de desposte
- **WHEN** un usuario sin permiso `desposte:read` hace `GET /desposte/tipos`
- **THEN** el endpoint responde 403

#### Scenario: Endpoint no filtra por empresa (catálogo global)
- **WHEN** un admin de la empresa A hace `GET /desposte/tipos`
- **THEN** recibe los mismos 12 tipos que un admin de la empresa B (la tabla `tipo_corte` es global)

