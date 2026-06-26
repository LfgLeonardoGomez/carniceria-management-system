## Why

El frontend BASILE tiene `App.tsx` que renderiza cada página directamente sin layout compartido. Cada página es responsable de su propio chrome, las rutas privadas no comparten navegación lateral, y el login se ve como un documento Word. Esto bloquea cualquier navegación coherente y filtra elementos del menú a roles que no deberían verlos. Necesitamos un layout base urgente para que las pantallas existentes vivan dentro de un shell con sidebar colapsable, header con identidad de empresa, y un login con branding mínimo.

## What Changes

- Crear `AppLayout` (sidebar + header + main) que envuelve **todas** las rutas privadas en `App.tsx`.
- Crear `Sidebar` colapsable, con estado persistido en `localStorage`, que filtra items del menú por rol usando la matriz confirmada (admin > encargado > cajero > vendedor).
- Crear `Header` fino con hamburguesa, nombre comercial de la empresa y dropdown de usuario (perfil / logout).
- Crear `LoginLayout` con card centrado, logo y color de marca `primary-600`, aplicado a `/login`, `/recuperar-contrasena`, `/restablecer-contrasena`.
- Crear `menuConfig.ts` declarando los items del menú agrupados en 4 secciones (Operaciones, Catálogo, Gestión, Administración), cada uno con `roles[]` explícitos.
- Iconos SVG inline (sin librerías nuevas).
- Cobertura de tests ligera: Sidebar (filtro por rol, collapse, active), Header (user name, logout), AppLayout (shell), LoginLayout (card).

**No** se refactoriza el contenido interno de las páginas — se respeta su estilo actual. Esto es un **BREAKING** solo en el sentido de que el árbol DOM de cada página cambia (ahora vive dentro de `<main>` con sidebar+header como hermanos); el comportamiento funcional y los tests de página existentes deben seguir pasando.

## Capabilities

### New Capabilities

- `frontend-layout`: shell de aplicación con sidebar colapsable filtrado por rol, header con identidad y dropdown de usuario, y login layout con branding mínimo.

### Modified Capabilities

Ninguna. Las páginas existentes no cambian su spec-level behavior — solo se monta su render dentro del nuevo layout. Los specs de `frontend-login`, `frontend-recover-password`, etc. siguen siendo válidos tal como están.

## Impact

**Archivos a crear**:
- `frontend/src/components/layout/AppLayout.tsx`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/components/layout/Header.tsx`
- `frontend/src/components/layout/LoginLayout.tsx`
- `frontend/src/components/layout/menuConfig.ts`
- `frontend/src/components/layout/icons.tsx` (SVG inline)
- `frontend/src/components/layout/AppLayout.test.tsx`
- `frontend/src/components/layout/Sidebar.test.tsx`
- `frontend/src/components/layout/Header.test.tsx`
- `frontend/src/components/layout/LoginLayout.test.tsx`

**Archivos a modificar**:
- `frontend/src/App.tsx` — envolver rutas privadas en `<AppLayout>`, públicas en `<LoginLayout>`, eliminar el `superadmin` route de Soporte? No, se mantiene porque no es parte del scope. Solo se envuelve.

**Sin nuevas dependencias**. Sin cambios de design tokens. Usa `primary-600` (`#dc2626`), `surface-*`, `shadow-card`, `font-sans` Inter, `@tailwindcss/forms` ya configurados.

**Scope explícito fuera**: mobile/tablet responsive, refactor de páginas, accesibilidad AA, animaciones.
