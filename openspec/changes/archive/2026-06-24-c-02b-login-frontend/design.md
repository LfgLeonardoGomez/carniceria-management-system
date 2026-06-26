## Context

El backend de autenticación (`c-02-auth-core`) expone tres endpoints públicos:
- `POST /auth/login` → responde `{ access_token, token_type }` (refresh token via httponly cookie)
- `POST /auth/recover` → inicia flujo de recuperación por email
- `POST /auth/reset` → restablece contraseña con token de un solo uso

El frontend tiene:
- `authStore` (Zustand) con `user`, `token`, `isAuthenticated`, `setUser`, `setToken`, `logout`
- Axios con interceptor que lee `access_token` de `localStorage`
- `App.tsx` con placeholder `<div>Login</div>` en ruta `/login`
- Rutas protegidas por `PrivateRoute` / `AdminRoute` / `SuperadminRoute`

## Goals / Non-Goals

**Goals:**
- Implementar la pantalla de login funcional con manejo de errores y redirección.
- Implementar flujo de recuperación de contraseña (solicitud + restablecimiento).
- Integrar con `authStore` y API existentes sin modificar backend.
- Cubrir las tres páginas con tests unitarios (RTL + Vitest).

**Non-Goals:**
- No se modifica el backend ni se agregan nuevos endpoints.
- No se implementa "recordarme" / persistencia de sesión más allá de `localStorage` del access token.
- No se implementa diseño visual custom (se usa lo que ya existe en el proyecto).
- No se tocan las reglas de RBAC ni los guards de ruta.

## Decisions

1. **Almacenamiento de token**: Access token en `localStorage` (patrón ya usado por el interceptor de axios existente). Refresh token queda en httponly cookie manejado por el backend — el frontend no lo toca.
2. **Redirección post-login**: `useNavigate` de React Router v6 hacia `/` después de `setToken` + `setUser`.
3. **Validación de contraseña en restablecimiento**: Se valida en frontend que nueva contraseña y confirmación coincidan antes de enviar al backend. Longitud mínima 8 caracteres (consistente con backend).
4. **Manejo de errores de API**: Se muestra `error.response.data.detail` si existe; fallback genérico para evitar leakage de información (especialmente en login, consistente con RN-AU-01).
5. **Organización de páginas**: Las tres páginas van en `frontend/src/pages/` (convención existente del proyecto) y no en `features/auth/` porque son entrypoints de routing globales, no features anidadas.
6. **Tests**: `MemoryRouter` con `initialEntries` para simular rutas con query params (`?token=`). Se mockea `authStore` como constante estable para evitar re-renderizados inesperados en tests.

## Risks / Trade-offs

- **Risk**: `localStorage` para access token es vulnerable a XSS.  
  → *Mitigation*: Es el patrón ya establecido en el proyecto. Una mejora futura sería httpOnly cookie para access token también, pero eso requiere cambios backend y no está en scope.
- **Risk**: El backend puede devolver errores de validación en español o inglés dependiendo de la config.  
  → *Mitigation*: Se normaliza mostrando `detail` si existe; si no, mensaje genérico fijo en español.
