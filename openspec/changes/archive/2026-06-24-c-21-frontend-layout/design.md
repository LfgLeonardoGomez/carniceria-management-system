## Context

`frontend/src/App.tsx` renderiza cada página sin layout compartido. No hay navegación lateral, no hay header, y `/login` se ve como un documento plano. El estado de autenticación vive en `useAuthStore` (`user.rol`, `user.nombre`, `user.apellido`). Tailwind ya tiene la paleta BASILE (`primary-*`, `surface-*`, `meat-*`) y el plugin `@tailwindcss/forms` instalado. No se agregan dependencias.

`useAuthStore.user.rol` actualmente es `string` (no hay union types), y existe el rol `superadmin` (para `/admin/soporte`). El scope actual solo cubre `admin | encargado | cajero | vendedor`; `superadmin` se trata como `admin` para visibilidad de menú.

## Goals / Non-Goals

**Goals:**
- Crear un shell compartido para rutas autenticadas.
- Sidebar colapsable con persistencia y filtrado por rol.
- Header con identidad de empresa y dropdown de usuario.
- Login visualmente presentable con branding mínimo.
- Cero dependencias nuevas. Cero cambios de design tokens.

**Non-Goals:**
- Responsive (mobile/tablet).
- Refactor del contenido interno de páginas.
- Accesibilidad AA completa (solo roles ARIA básicos).
- Animaciones, transiciones, drag-to-resize.
- Nuevo sistema de iconos / librería SVG.
- Cambio en el `useAuthStore` (la lectura de `empresa.nombre_comercial` se hace por contexto separado si no existe, o fallback a "BASILE").

## Decisions

### D1. Estructura de archivos: `frontend/src/components/layout/`
Convención: cada componente de layout en su archivo, con su `.test.tsx` al lado. Un `icons.tsx` con todos los SVGs inline exporta componentes funcionales pequeños (1 viewBox, 1 path).

**Por qué**: cero magia, fácil de testear, fácil de borrar. `menuConfig.ts` separado para que añadir un item sea 1 línea.

### D2. Persistencia de collapse en `localStorage`, no en store
El estado de collapse es UI-only y no necesita ser global ni leído por otros componentes. Se encapsula dentro de `Sidebar.tsx` con un `useState` inicializado desde `localStorage`.

**Alternativa considerada**: Zustand store. Descartada por overkill — el collapse es propiedad de un solo componente y se quiere mantener el shell sin acoplar a un store nuevo.

### D3. Filtrado por rol en el componente Sidebar, no en `menuConfig`
`menuConfig.ts` declara `roles: Role[]` por item. `Sidebar` hace el filtro en render con un helper `canSee(item, userRol)`. Esto permite derivar items en tests sin mockear nada del store.

**Alternativa**: filtrar en `menuConfig` (ej. `getVisibleMenu(rol)`). Descartada porque acopla config a lógica de negocio y complica tests.

### D4. Roles como union type local en el módulo
`Role = 'admin' | 'encargado' | 'cajero' | 'vendedor'`. Se declara en `menuConfig.ts` y se re-exporta. `superadmin` se mapea a `admin` en el helper `canSee` para que superadmin vea todo (consistente con `AdminRoute` actual en `App.tsx`).

**Por qué**: aunque `useAuthStore.user.rol` es `string` en TS, definimos el union local para que el config sea type-safe. El cast `as Role` se hace en un único punto (el helper).

### D5. Header obtiene nombre de empresa con fallback, no toca `useAuthStore`
El `Header` lee `empresa?.nombre_comercial` desde un `useEmpresaContext()` o prop. Si no existe, renderiza `"BASILE"`. **No se modifica `useAuthStore`** en este change.

**Razón**: alcance mínimo. Si el contexto de empresa no está en la KB actual, el fallback `"BASILE"` cubre la entrega y queda como TODO marcado en código.

### D6. Iconos SVG inline en `icons.tsx`
15-20 iconos pequeños (Home, ShoppingCart, Box, Truck, Users, etc.), uno por item del menú, todos con `viewBox="0 0 24 24"` y `stroke="currentColor"`. Tamaño por defecto `w-5 h-5`.

**Por qué**: cero dependencias, consistentes, y se tree-shakean fácil. Es el patrón estándar de Headless UI / shadcn.

### D7. AppLayout con flexbox, sidebar fija + main scrollable
```tsx
<div className="flex h-screen bg-surface-50">
  <Sidebar />
  <div className="flex-1 flex flex-col overflow-hidden">
    <Header />
    <main className="flex-1 overflow-auto p-6">{children}</main>
  </div>
</div>
```

Sidebar: `w-60` expandido, `w-16` colapsado (solo iconos). Header: `h-14`. Main: padding generoso pero sin tocar el contenido de las páginas.

### D8. LoginLayout = centered card con primary-600 top border
```tsx
<div className="min-h-screen bg-surface-50 flex items-center justify-center p-4">
  <div className="w-full max-w-md bg-white rounded-lg shadow-card border-t-4 border-primary-600 p-8">
    <h1 className="text-2xl font-bold text-primary-600 mb-6">BASILE</h1>
    {children}
  </div>
</div>
```

**Razón**: implementación mínima de "no se vea como Word". El `border-t-4 border-primary-600` da la marca sin sobre-diseñar.

### D9. Tests: cobertura mínima, no exhaustiva
- `Sidebar.test.tsx`: 4 tests (admin ve todo, cajero ve subset, toggle persiste, active route highlight).
- `Header.test.tsx`: 2 tests (user name renderiza, logout limpia y redirige).
- `AppLayout.test.tsx`: 1 test (children renderizan dentro de `<main>`).
- `LoginLayout.test.tsx`: 1 test (card renderiza con `primary-600` accent).

Mock de `useAuthStore` con un helper `mockAuthStore(user)`. No se mockea `react-router-dom` salvo cuando se necesita `MemoryRouter`.

## Risks / Trade-offs

- **R1**: Páginas existentes pueden tener CSS que asume ancho completo o posición absoluta → pueden verse peor dentro del shell. **Mitigación**: aceptar que la estética interna es fea (declarado en scope); refactor visual se hace en changes posteriores. Si alguna página rompe funcionalmente (no solo visual), se ajusta su contenedor (`<div className="p-6">` extra) sin tocar lógica.
- **R2**: `useAuthStore.user.rol` es `string` en TS, no `Role`. Casts en runtime. **Mitigación**: helper único `canSee` con cast explícito; tests cubren los 4 roles.
- **R3**: `superadmin` puede no estar contemplado en la matriz → se mapea a `admin` en `canSee`. Si el comportamiento esperado es distinto, queda como follow-up.
- **R4**: No hay empresa context todavía → header muestra siempre "BASILE". **Mitigación**: fallback explícito, código marcado con TODO para que el siguiente change conecte el contexto de empresa.
- **R5**: Cambiar `App.tsx` envuelve TODAS las rutas. Si el dev tenía un branch abierto, hay merge conflict. **Mitigación**: cambio aislado, trivial de mergear.

## Open Questions

- ¿Existe ya `empresa.nombre_comercial` en algún contexto/store del frontend? Búsqueda rápida no lo encontró. Si no existe, queda TODO en `Header.tsx` y se entrega con fallback.
- ¿`superadmin` debe tener el mismo menú que `admin`? Asumimos sí (consistente con `AdminRoute`).
- ¿El dropdown de usuario debe mostrar email además del nombre? Asumimos no (solo nombre), para mantener scope.
