## 1. Login Page

- [x] 1.1 Create `frontend/src/pages/LoginPage.tsx` with email + password form, submit handler calling `POST /auth/login`, error display, and link to `/recuperar-contrasena`
- [x] 1.2 On login success: store `access_token` in `localStorage`, call `authStore.setToken` and `authStore.setUser`, redirect to `/`
- [x] 1.3 Handle error cases: invalid credentials (generic message), inactive account, network error
- [x] 1.4 Create `frontend/src/pages/LoginPage.test.tsx` — render form, fill fields, submit success, submit failure, navigation to recovery link

## 2. Password Recovery Request Page

- [x] 2.1 Create `frontend/src/pages/RecuperarContrasenaPage.tsx` with email form, submit handler calling `POST /auth/recover`, success/error message display, link back to `/login`
- [x] 2.2 Add client-side email format validation before API call
- [x] 2.3 Create `frontend/src/pages/RecuperarContrasenaPage.test.tsx` — render form, submit success, submit failure, invalid email validation, back-to-login link

## 3. Password Reset Page

- [x] 3.1 Create `frontend/src/pages/RestablecerContrasenaPage.tsx` that reads `?token=` from URL, renders new password + confirmation form, validates match and min length (8 chars)
- [x] 3.2 Submit handler calling `POST /auth/reset` with token and new password; on success redirect to `/login`
- [x] 3.3 Handle error cases: token expired/invalid, password mismatch, weak password
- [x] 3.4 Create `frontend/src/pages/RestablecerContrasenaPage.test.tsx` — render with token, submit success, password mismatch, weak password, invalid token error

## 4. Routing Integration

- [x] 4.1 Update `frontend/src/App.tsx`: replace `<div>Login</div>` with `<LoginPage />` on `/login`
- [x] 4.2 Add public route `/recuperar-contrasena` rendering `<RecuperarContrasenaPage />` (no auth required)
- [x] 4.3 Add public route `/restablecer-contrasena` rendering `<RestablecerContrasenaPage />` (no auth required)
- [x] 4.4 Verify `App.tsx` compiles and existing routing tests pass

## 5. Verification

- [x] 5.1 Run `npm run test` (or `vitest run`) in `frontend/` and confirm all new tests pass
- [x] 5.2 Run TypeScript compiler (`tsc --noEmit`) in `frontend/` and confirm no errors
- [x] 5.3 Manual smoke test: navigate to `/login`, `/recuperar-contrasena`, `/restablecer-contrasena?token=test` and verify rendering
