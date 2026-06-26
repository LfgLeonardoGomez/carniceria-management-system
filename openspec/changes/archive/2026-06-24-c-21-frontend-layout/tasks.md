## 1. Setup: tipos, config de menú e iconos

- [x] 1.1 Crear `frontend/src/components/layout/menuConfig.ts` con `Role` union, `MenuItem` interface y `menuGroups` (4 grupos: Operaciones, Catálogo, Gestión, Administración) cubriendo los 16 items del scope (Dashboard, POS, Productos, Stock, Compras, Despostes, Clientes, Proveedores, Cuentas Corrientes, Caja, Gastos, Reportes Ventas, Reportes Financieros, Rentabilidad, Usuarios, Configuración Empresa, Perfil). Asignar `roles[]` por item según la matriz confirmada.
- [x] 1.2 Crear `frontend/src/components/layout/icons.tsx` exportando 15-20 componentes SVG inline (`HomeIcon`, `ShoppingCartIcon`, `BoxIcon`, `WarehouseIcon`, `TruckIcon`, `ScissorsIcon`, `UsersIcon`, `AddressBookIcon`, `CashIcon`, `ReceiptIcon`, `ChartIcon`, `TrendingUpIcon`, `CogIcon`, `UserCogIcon`, `MenuIcon`, `LogoutIcon`, `ChevronLeftIcon`, `UserCircleIcon`). Todos `viewBox="0 0 24 24"`, `stroke="currentColor"`, default `w-5 h-5`.
- [x] 1.3 Crear helper `canSee(item, userRol)` que mapea `superadmin → admin` y devuelve true si el rol está en `item.roles`. Exportar desde `menuConfig.ts`.

## 2. Sidebar component

- [x] 2.1 Crear `frontend/src/components/layout/Sidebar.tsx` que lee `useAuthStore().user.rol`, filtra `menuGroups` con `canSee`, y renderiza la lista agrupada con `<NavLink>` de `react-router-dom`.
- [x] 2.2 Implementar estado de collapse con `useState` inicializado desde `localStorage["basile.sidebar.collapsed"]`. Toggle button al pie del sidebar que escribe al localStorage. Ancho `w-60` expandido, `w-16` colapsado (solo iconos con `title` attr).
- [x] 2.3 Estilizar con Tailwind: fondo `bg-white`, `border-r border-surface-200`, items activos con `bg-primary-50 text-primary-700`, hover con `hover:bg-surface-100`. Section headers en `text-xs uppercase tracking-wider text-surface-500 font-semibold`.
- [x] 2.4 Crear `frontend/src/components/layout/Sidebar.test.tsx` cubriendo: (a) admin ve todos los items, (b) cajero ve solo items permitidos (no ve Usuarios ni Reportes Financieros), (c) click en toggle cambia width y persiste en localStorage, (d) `<NavLink>` activo tiene la clase `bg-primary-50`.

## 3. Header component

- [x] 3.1 Crear `frontend/src/components/layout/Header.tsx` con altura `h-14`, fondo `bg-white border-b border-surface-200`. Layout flex: izquierda = botón hamburguesa (toggle sidebar via prop o store local), centro = nombre de empresa (placeholder `BASILE` por ahora con `// TODO: conectar empresa context`), derecha = dropdown de usuario.
- [x] 3.2 Dropdown: trigger con `${user.nombre} ${user.apellido}` + `UserCircleIcon`. Menú con dos items: "Mi perfil" (link a `/perfil`) y "Cerrar sesión" (button que llama `useAuthStore().logout()`, `localStorage.removeItem("access_token")`, `navigate("/login")`).
- [x] 3.3 Dropdown: click-outside para cerrar. Implementar con `useState` + `useRef` + listener de `mousedown`. No usar librería.
- [x] 3.4 Crear `frontend/src/components/layout/Header.test.tsx` cubriendo: (a) renderiza `${nombre} ${apellido}` del store, (b) click en "Cerrar sesión" llama `logout()` del store y navega a `/login`.

## 4. AppLayout shell

- [x] 4.1 Crear `frontend/src/components/layout/AppLayout.tsx` con la estructura flex: `<div className="flex h-screen bg-surface-50">` → `<Sidebar />` + `<div className="flex-1 flex flex-col overflow-hidden">` → `<Header />` + `<main className="flex-1 overflow-auto p-6">{children}</main>`.
- [x] 4.2 Sidebar y Header necesitan compartir el estado de collapse. **Decisión**: lifting state a `AppLayout` — `AppLayout` mantiene `collapsed` state, pasa `collapsed` y `onToggle` a `Sidebar`. `Header` recibe `onToggle` para el botón hamburguesa. Modificar `Sidebar` para usar props en vez de estado interno.
- [x] 4.3 Crear `frontend/src/components/layout/AppLayout.test.tsx` con un test: children renderizan dentro de `<main>` y sidebar/header están en el DOM.

## 5. LoginLayout

- [x] 5.1 Crear `frontend/src/components/layout/LoginLayout.tsx` con la card centrada: `min-h-screen bg-surface-50 flex items-center justify-center p-4` → `card bg-white rounded-lg shadow-card border-t-4 border-primary-600 p-8 max-w-md w-full` → header con `<h1 className="text-2xl font-bold text-primary-600 mb-6">BASILE</h1>` + children.
- [x] 5.2 Crear `frontend/src/components/layout/LoginLayout.test.tsx` con un test: renderiza children dentro de la card y la card tiene clase `border-primary-600`.

## 6. Integración en App.tsx

- [x] 6.1 Modificar `frontend/src/App.tsx`: crear componente `PrivateShell` que envuelve `<PrivateRoute>` con `<AppLayout>`, y `PublicShell` que envuelve `/login`, `/recuperar-contrasena`, `/restablecer-contrasena` con `<LoginLayout>`. Reemplazar los `<PrivateRoute>` sueltos y los `<Route path="/login" .../>` por las versiones envueltas.
- [x] 6.2 Verificar que los tests existentes de páginas (`LoginPage.test.tsx`, `PerfilPage.test.tsx`, etc.) siguen pasando — no se cambió la lógica de las páginas, solo el árbol DOM que las contiene.

## 7. Verificación final

- [x] 7.1 Correr `pnpm test` (o `npm test`) en `frontend/` y confirmar que todos los tests nuevos + existentes pasan.
- [x] 7.2 Correr `pnpm type-check` y confirmar 0 errores TypeScript.
- [x] 7.3 Correr `pnpm lint` y confirmar 0 warnings/errors.
- [x] 7.4 Smoke check manual: levantar dev server, login como admin → ver sidebar completo; login como cajero → ver subset; colapsar sidebar → refrescar → sigue colapsado.
