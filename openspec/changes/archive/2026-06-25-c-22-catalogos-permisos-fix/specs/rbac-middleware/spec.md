# Delta Spec — rbac-middleware (c-22)

## ADDED Requirements

### Requirement: Rol `desposte` reconocido por la matriz RBAC

El sistema SHALL reconocer el rol `desposte` en `PERMISSION_MATRIX` y en `normalize_rol` con permisos limitados al módulo de desposte + lectura de productos y stock.

#### Scenario: normalize_rol acepta el nombre "desposte"
- **WHEN** se llama `normalize_rol("desposte")`
- **THEN** retorna `"desposte"`

#### Scenario: has_permission valida permisos del rol desposte
- **WHEN** se consulta `has_permission("desposte", "desposte:read")`
- **THEN** retorna `True`
- **WHEN** se consulta `has_permission("desposte", "ventas:create")`
- **THEN** retorna `False`

### Requirement: Endpoints de desposte usan el string singular `desposte:*`

Los endpoints del módulo de desposte SHALL usar el string de permiso `desposte:<operacion>` (singular) — alineado con `PERMISSION_MATRIX`. El string `despostes:*` (plural) está deprecado y no debe usarse en código nuevo.

#### Scenario: Router de desposte usa strings singulares
- **WHEN** se inspecciona `backend/src/modules/desposte/router.py`
- **THEN** todas las llamadas a `require_role(...)` usan `desposte:read`, `desposte:create`, o `desposte:update` (singular)

#### Scenario: GET /desposte no devuelve 403 para admin
- **WHEN** un usuario con rol admin hace `GET /desposte`
- **THEN** el endpoint responde 200 con la lista de despostes de su empresa
