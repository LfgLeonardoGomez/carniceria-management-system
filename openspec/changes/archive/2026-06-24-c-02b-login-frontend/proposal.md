## Why

El backend de autenticación fue completado en `c-02-auth-core` (endpoints `POST /auth/login`, `/auth/recover`, `/auth/reset`), pero el frontend quedó con un placeholder `<div>Login</div>` en `App.tsx`. Sin la interfaz de login, ningún usuario puede autenticarse y acceder a la aplicación, bloqueando toda la funcionalidad downstream. Es una dependencia crítica del camino crítico que debe cerrarse antes de continuar con features que requieren sesión.

## What Changes

- **Nueva página `LoginPage`** (`frontend/src/pages/LoginPage.tsx`): formulario de email + contraseña, integración con `POST /auth/login`, manejo de token, redirección al dashboard, link a recuperación de contraseña.
- **Nueva página `RecuperarContrasenaPage`** (`frontend/src/pages/RecuperarContrasenaPage.tsx`): formulario de email, integración con `POST /auth/recover`, mensajes de éxito/error, link de vuelta a login.
- **Nueva página `RestablecerContrasenaPage`** (`frontend/src/pages/RestablecerContrasenaPage.tsx`): lee `?token=` de URL, formulario de nueva contraseña + confirmación, integración con `POST /auth/reset`, redirección a login en éxito.
- **Actualización de `App.tsx`**: reemplaza el placeholder `<div>Login</div>` por `<LoginPage />` y agrega rutas públicas `/recuperar-contrasena` y `/restablecer-contrasena`.
- **Tests unitarios**: `LoginPage.test.tsx`, `RecuperarContrasenaPage.test.tsx`, `RestablecerContrasenaPage.test.tsx` usando Vitest + RTL + `MemoryRouter`.

## Capabilities

### New Capabilities
- `frontend-login`: Página de inicio de sesión con formulario, validación, llamada a API, gestión de token y redirección post-login.
- `frontend-recover-password`: Flujo completo de recuperación de contraseña (solicitud de email + restablecimiento con token).

### Modified Capabilities
- *(Ninguno — este change es puramente frontend sobre APIs existentes.)*

## Impact

- **Frontend**: `frontend/src/pages/LoginPage.tsx`, `frontend/src/pages/RecuperarContrasenaPage.tsx`, `frontend/src/pages/RestablecerContrasenaPage.tsx`, `frontend/src/App.tsx`, tests asociados.
- **Store**: Reutiliza `authStore` existente (`frontend/src/store/authStore.ts`) para estado de autenticación.
- **API client**: Reutiliza patrón axios existente (baseURL desde `VITE_API_URL`, interceptor de `Authorization`).
- **Backend**: Sin cambios — consume endpoints ya existentes de `c-02-auth-core`.
