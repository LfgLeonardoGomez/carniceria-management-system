# frontend-layout Specification

## Purpose
TBD - created by archiving change c-21-frontend-layout. Update Purpose after archive.
## Requirements
### Requirement: AppLayout shell
The system SHALL provide an `AppLayout` component that renders a `Sidebar`, a `Header`, and a `<main>` content area, and that mounts the routed page as children inside `<main>`. The component SHALL be the only wrapper used for authenticated routes in `App.tsx`.

#### Scenario: Private route renders inside AppLayout
- **WHEN** an authenticated user navigates to any private route (e.g. `/productos`, `/pos`, `/dashboard`)
- **THEN** the page renders inside `<AppLayout>` with the sidebar, header, and main content area visible

#### Scenario: Public route does not render AppLayout
- **WHEN** an unauthenticated user navigates to `/login`, `/recuperar-contrasena`, or `/restablecer-contrasena`
- **THEN** the page renders inside `LoginLayout` and the sidebar/header are NOT present

### Requirement: Sidebar collapse state persistence
The system SHALL persist the sidebar collapsed/expanded state in `localStorage` under the key `basile.sidebar.collapsed`. On mount, the sidebar SHALL read this key; on toggle, it SHALL write the new value.

#### Scenario: Sidebar starts collapsed
- **WHEN** the user previously collapsed the sidebar and `localStorage["basile.sidebar.collapsed"]` is `"true"`
- **THEN** on next mount the sidebar renders in icon-only (collapsed) mode

#### Scenario: Sidebar starts expanded
- **WHEN** `localStorage["basile.sidebar.collapsed"]` is `"false"` or missing
- **THEN** on next mount the sidebar renders expanded with labels visible

#### Scenario: Toggle persists
- **WHEN** the user clicks the collapse/expand toggle
- **THEN** the new state is written to `localStorage` and applied immediately

### Requirement: Sidebar role-based menu filtering
The sidebar SHALL render only menu items whose `roles` array includes the current user's effective role. The effective role SHALL follow the hierarchy `admin > encargado > cajero > vendedor`: when checking visibility, an item visible to a higher role is also visible to lower roles that appear in the `roles` array of that item. The sidebar SHALL read `user.rol` from `useAuthStore`.

#### Scenario: Admin sees all items
- **WHEN** the logged-in user has `rol === "admin"`
- **THEN** the sidebar shows every menu item declared in `menuConfig`

#### Scenario: Cajero sees only allowed items
- **WHEN** the logged-in user has `rol === "cajero"`
- **THEN** the sidebar shows only items where `roles` includes `cajero` (Dashboard, POS, Clientes, Cuentas Corrientes, Caja, Perfil) and no admin/encargado-only items

#### Scenario: Vendedor sees minimal items
- **WHEN** the logged-in user has `rol === "vendedor"`
- **THEN** the sidebar shows only items where `roles` includes `vendedor` (Dashboard, POS, Perfil)

#### Scenario: Encargado sees operations and catalog
- **WHEN** the logged-in user has `rol === "encargado"`
- **THEN** the sidebar shows all items except admin-only (Usuarios, Configuración Empresa)

### Requirement: Sidebar active route highlight
The sidebar SHALL visually highlight the menu item whose `path` matches the current `useLocation().pathname` (exact or prefix match for nested routes such as `/clientes/:id`).

#### Scenario: Active item has distinct styling
- **WHEN** the current path is `/productos`
- **THEN** the "Productos" item has the active background/text color class and other items do not

#### Scenario: Active item updates on navigation
- **WHEN** the user clicks "Clientes" from `/dashboard`
- **THEN** the new path `/clientes` highlights "Clientes" and removes highlight from the previous item

### Requirement: Header identity and user dropdown
The `Header` component SHALL display the company commercial name (from auth context, falling back to `"BASILE"`), and a user dropdown with the user's full name, a "Mi perfil" link to `/perfil`, and a "Cerrar sesión" action that calls `useAuthStore().logout()` and navigates to `/login`.

#### Scenario: Header shows company name
- **WHEN** the auth context provides `empresa.nombre_comercial`
- **THEN** the header renders that string

#### Scenario: Header shows BASILE fallback
- **WHEN** the auth context does not provide a company name
- **THEN** the header renders the literal string "BASILE"

#### Scenario: User dropdown shows user name
- **WHEN** the user is logged in
- **THEN** the header renders `${user.nombre} ${user.apellido}` in the dropdown trigger

#### Scenario: Logout clears session
- **WHEN** the user clicks "Cerrar sesión"
- **THEN** `useAuthStore().logout()` is called, `localStorage.removeItem("access_token")` is executed, and the user is redirected to `/login`

### Requirement: LoginLayout centered card with brand color
The `LoginLayout` component SHALL render a centered card on a `surface-50` background, with the BASILE logo/title at the top, the page content inside the card, and a `primary-600` accent (top border or logo color). The component SHALL be used by `/login`, `/recuperar-contrasena`, and `/restablecer-contrasena`.

#### Scenario: Login renders centered card
- **WHEN** the user navigates to `/login`
- **THEN** the page renders inside `LoginLayout` with a centered card, white surface, and primary-600 accent

#### Scenario: Recover and reset use same layout
- **WHEN** the user navigates to `/recuperar-contrasena` or `/restablecer-contrasena`
- **THEN** the page renders inside `LoginLayout` with identical chrome

### Requirement: Menu configuration is data-driven
The system SHALL define `menuConfig.ts` exporting `MenuItem` (fields: `label`, `path`, `icon`, `roles: Role[]`) and a `menuGroups` array grouping items under section titles. Sections SHALL be: `Operaciones`, `Catálogo`, `Gestión`, `Administración`. The sidebar SHALL render exclusively from this config — no hardcoded menu in the component.

#### Scenario: Menu items are defined in config
- **WHEN** the sidebar renders
- **THEN** it iterates `menuGroups` and renders items filtered by role

#### Scenario: Adding an item is a config change
- **WHEN** a new item is added to `menuConfig` with appropriate `roles`
- **THEN** the sidebar shows it for the listed roles without code changes to `Sidebar.tsx`

### Requirement: Sidebar usa el label "Venta" para la ruta /pos

El sidebar SHALL mostrar el item con `path = "/pos"` con `label = "Venta"` (alineado con la nomenclatura de dominio, no "POS"). El `path` y el componente `PosPage` no cambian.

#### Scenario: Item del POS usa el label "Venta"
- **WHEN** se renderiza el sidebar
- **THEN** el item con `path = "/pos"` muestra el texto "Venta" (no "POS")
- **AND** el `path` sigue siendo `/pos` (no se cambia la ruta)

#### Scenario: Tests del menuConfig siguen pasando
- **WHEN** se ejecuta `frontend/src/components/layout/menuConfig.test.ts`
- **THEN** todas las aserciones pasan (el test no valida labels, solo paths y roles)

