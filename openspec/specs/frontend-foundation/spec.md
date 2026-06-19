# frontend-foundation Specification

## Purpose
TBD - created by archiving change c-01-foundation-setup. Update Purpose after archive.
## Requirements
### Requirement: React SPA con TypeScript strict
El sistema SHALL proveer una aplicación React 18+ usando TypeScript con `strict: true` en `tsconfig.json`.

#### Scenario: Proyecto compila sin errores de tipo
- **WHEN** se ejecuta `npm run build` o `npm run type-check`
- **THEN** no hay errores de TypeScript
- **AND** el archivo `tsconfig.json` tiene `"strict": true`
- **AND** no se usa `any` en código propio (librerías de terceros permiten `any` en `.d.ts`)

### Requirement: Estructura por features
El sistema SHALL organizar el frontend en `features/` por dominio de negocio.

#### Scenario: Directorios de features existen
- **WHEN** se inspecciona `frontend/src/`
- **THEN** existe `features/` con subdirectorios: `auth/`, `dashboard/`, `productos/`, `clientes/`, `proveedores/`, `compras/`, `desposte/`, `stock/`, `ventas/`, `caja/`, `gastos/`, `cuentas-corrientes/`, `reportes/`, `notifications/`
- **AND** existe `shared/` para componentes, hooks, utils, servicios y tipos reutilizables
- **AND** existe `store/` para estado global (Zustand)

### Requirement: Zustand para estado global
El sistema SHALL usar Zustand para estado global del frontend.

#### Scenario: Store de autenticación existe
- **WHEN** se inspecciona `frontend/src/store/`
- **THEN** existe al menos un store (ej. `authStore.ts`) que maneja estado global con Zustand
- **AND** el store tiene tipado TypeScript completo

### Requirement: Componentes funcionales con hooks
El sistema SHALL usar exclusivamente componentes funcionales y hooks de React; NUNCA componentes de clase.

#### Scenario: No hay componentes de clase
- **WHEN** se ejecuta `grep -r "extends Component" frontend/src/` o `grep -r "extends React.Component" frontend/src/`
- **THEN** no se encuentran resultados en código propio

