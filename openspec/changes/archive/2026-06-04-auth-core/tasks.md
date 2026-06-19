# Tasks: auth-core (C-02)

> TDD obligatorio: cada task con lógica de negocio requiere tests escritos **antes** del código productivo.

---

## Phase 0: Modelos de datos (SQLModel)

- [ ] **TASK-0.1** — Crear modelo `RefreshToken` en `app/modules/auth/models.py`:
  - `id` (PK, UUID)
  - `usuario_id` (FK → Usuario)
  - `jti` (string, único, identificador del token JWT)
  - `exp` (timestamp, expiración)
  - `revoked` (boolean, default false)
  - `created_at`, `updated_at`
  - Tests: crear instancia, unicidad jti, soft revoke.

- [ ] **TASK-0.2** — Crear modelo `TokenRecuperacion` en `app/modules/auth/models.py`:
  - `id` (PK, UUID)
  - `usuario_id` (FK → Usuario)
  - `token_hash` (string, hash del token raw)
  - `expiracion` (timestamp)
  - `usado` (boolean, default false)
  - `created_at`
  - Tests: crear instancia, expiración, uso único.

- [ ] **TASK-0.3** — Generar migración Alembic para `RefreshToken` y `TokenRecuperacion`:
  - `alembic revision --autogenerate -m "add auth tables"`
  - Verificar SQL generado offline.
  - Tests: migración aplica sin errores en testcontainer PostgreSQL.

## Phase 1: Infraestructura de seguridad

- [ ] **TASK-1.1** — Crear módulo `app/core/security.py` con funciones utilitarias:
  - `hash_password(plain: str) -> str` usando bcrypt (work factor 12).
  - `verify_password(plain: str, hashed: str) -> bool`.
  - `create_access_token(data: dict, expires_delta: timedelta | None = None) -> str` (HS256, secreto `JWT_SECRET_KEY`).
  - `create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str` (HS256, secreto `JWT_REFRESH_SECRET`).
  - `decode_token(token: str, secret: str, token_type: str) -> dict` (valida firma, exp, type).
  - Tests unitarios para cada función.

- [ ] **TASK-1.2** — Definir settings de JWT en `app/core/config.py`:
  - `JWT_SECRET_KEY`, `JWT_REFRESH_SECRET_KEY`, `JWT_ALGORITHM=HS256`, `ACCESS_TOKEN_EXPIRE_MINUTES=15`, `REFRESH_TOKEN_EXPIRE_DAYS=7`.
  - Validación: ambos secretos deben tener >= 32 caracteres; crash en startup si no.

---

## Phase 2: Endpoints de autenticación

- [ ] **TASK-2.1** — Implementar `POST /auth/login`:
  - Request: `LoginRequest` (EmailStr, contrasena).
  - Buscar `Usuario` por email en DB.
  - Verificar `activo = true`.
  - Validar contraseña con `verify_password`.
  - Generar access token (15 min) + refresh token (7 días).
  - **Persistir refresh token en DB**: crear registro `RefreshToken` con `jti`, `exp`, `revoked=false`.
  - Setear cookie `refresh_token` (HttpOnly, Secure=False en dev, SameSite=Lax).
  - Responder `LoginResponse` con access token y datos públicos del usuario.
  - Tests de integración: login exitoso, contraseña incorrecta, usuario inactivo, email inexistente; verificar que el refresh token queda persistido en DB.

- [ ] **TASK-2.2** — Implementar `EmailService` en `app/core/email.py`:
  - Clase `EmailService` con métodos: `send_recovery_email(to: str, token: str, frontend_url: str) -> bool`.
  - Usar `aiosmtplib` (SMTP async) para no bloquear el event loop.
  - Template Jinja2 para email de recuperación con branding BASILE.
  - Configuración vía env vars: `EMAIL_PROVIDER`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_TLS`.
  - Fallback: si envío falla, loguear CRITICAL y retornar `False` (el endpoint de recover responde 200 igual, pero el email no se envió).
  - Tests unitarios: mock de SMTP, verificar que el cuerpo contiene el link correcto.

- [ ] **TASK-2.3** — Implementar `POST /auth/recover`:
  - Request: `RecoverRequest` (EmailStr).
  - Buscar usuario por email.
  - Responder **siempre** `200 OK` con mensaje genérico (evitar enumeración de usuarios).
  - Si usuario existe: generar token con `secrets.token_urlsafe(32)`, hashearlo, guardar en tabla `TokenRecuperacion` con expiración 1h.
  - Enviar email vía `EmailService.send_recovery_email()`.
  - Tests de integración: respuesta genérica 200 para email existente y no existente; verificar que el token se genera y tiene expiración correcta; verificar que EmailService es llamado (mock).

- [ ] **TASK-2.4** — Implementar `POST /auth/reset`:
  - Request: `ResetRequest` (token, nueva_contrasena, confirmacion).
  - Validar que `nueva_contrasena == confirmacion`.
  - Validar fuerza de contraseña (mín 8 chars, 1 mayúscula, 1 minúscula, 1 número).
  - Buscar token por hash, validar expiración y `usado = false`.
  - Hashear nueva contraseña y actualizar `Usuario.contrasena_hash`.
  - Marcar token como usado.
  - Tests de integración: reset exitoso, token expirado, token ya usado, contraseña débil, confirmación no coincide.

- [ ] **TASK-2.5** — Implementar `POST /auth/refresh`:
  - Leer cookie `refresh_token`.
  - Decodificar refresh token (validar firma, exp, `type: refresh`).
  - Buscar `RefreshToken` en DB por `jti`, verificar `revoked = false`.
  - Generar nuevo access token (15 min).
  - **Generar nuevo refresh token**, invalidar el anterior (`revoked = true`).
  - Setear nueva cookie `refresh_token`.
  - Responder con nuevo access token.
  - Tests: refresh exitoso, token revocado, token expirado, reutilización de refresh token (debe fallar).

- [ ] **TASK-2.6** — Implementar `POST /auth/logout`:
  - Leer cookie `refresh_token`.
  - Buscar `RefreshToken` en DB por `jti`, marcar `revoked = true`.
  - Borrar cookie `refresh_token` (max-age=0).
  - Responder `204 No Content`.
  - Test: cookie se borra correctamente, token queda revocado en DB.

---

## Phase 3: Middleware y protección de rutas

- [ ] **TASK-3.1** — Crear dependency `get_current_user`:
  - Extraer token del header `Authorization: Bearer <token>`.
  - Decodificar y validar access token (firma, exp, `type: access`).
  - Buscar usuario en DB por `sub` claim.
  - Verificar `activo = true`.
  - Retornar instancia `Usuario`.
  - Tests de integración: token válido, token expirado, token malformado, usuario inactivo, token tipo refresh rechazado.

- [ ] **TASK-3.2** — Crear dependency `require_auth`:
  - Inyecta `current_user: Usuario = Depends(get_current_user)`.
  - Setea `request.state.current_user = current_user`.
  - Setea `request.state.empresa_id = current_user.empresa_id`.
  - Tests: verificar que request.state contiene empresa_id y current_user después de pasar el middleware.

- [ ] **TASK-3.3** — Proteger routers:
  - Agregar `dependencies=[Depends(require_auth)]` a todos los routers excepto auth público.
  - Verificar que rutas públicas (`/auth/login`, `/auth/recover`, `/auth/reset`) NO requieren auth.
  - Tests de integración: acceso a ruta protegida sin token → 401; con token válido → 200; con token de refresh en lugar de access → 403/401.

---

## Phase 4: Rate limiting

- [ ] **TASK-4.1** — Configurar rate limiting en endpoints de auth:
  - Instalar/configurar `slowapi` o middleware custom.
  - Regla: 5 intentos / 60s por clave `ip:email` en `POST /auth/login` y `POST /auth/recover`.
  - Responder `429 Too Many Requests` cuando se excede.
  - Tests: 5 intentos fallidos permitidos, 6to devuelve 429; esperar 60s y reintentar permitido.

---

## Phase 5: Integración y validación

- [ ] **TASK-5.1** — Ejecutar suite completa de tests:
  - `pytest tests/integration/test_auth.py` (o path correspondiente) debe pasar al 100%.
  - Coverage mínimo 90% del módulo `app/auth`.

- [ ] **TASK-5.2** — Verificar reglas de negocio:
  - RN-AU-01: login requiere email y contraseña válidos.
  - RN-AU-02: recuperación por email con enlace seguro de un solo uso.
  - RN-AU-03: roles ya existen en C-01 (no se modifica).
  - RN-SEG-02: middleware inyecta empresa_id en cada request autenticado.
  - RN-SEG-03: usuarios autentican con email/contraseña y acceden solo a su empresa.

- [ ] **TASK-5.3** — Actualizar documentación técnica:
  - Agregar endpoints a README de API o Swagger descriptions.
  - Documentar cookie `refresh_token` y header `Authorization` para consumidores del frontend.

---

## Definición de hecho (DoD)
- [ ] Todos los tests pasan (pytest, pytest-asyncio, testcontainers PostgreSQL).
- [ ] Coverage >= 90% en módulo auth.
- [ ] Ningún endpoint I/O-bound bloquea el event loop (async/await en todo el pipeline).
- [ ] Ningún request/response usa `dict` plano; todo es Pydantic BaseModel con `extra='forbid'`.
- [ ] Rate limiting activo en login y recover.
- [ ] Cookie `refresh_token` es HttpOnly y SameSite=Lax.
- [ ] El middleware inyecta `empresa_id` en `request.state` para todos los endpoints protegidos.
