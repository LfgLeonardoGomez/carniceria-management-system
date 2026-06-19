# Design: auth-core (C-02)

## 1. Arquitectura general

```
┌──────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Frontend   │──────│  FastAPI     │──────│  PostgreSQL     │
│   (React)    │      │  /auth/*     │      │  (async pg)     │
└──────────────┘      └──────────────┘      └─────────────────┘
         │                     │
         │              ┌───────┴───────┐
         │              │  JWT Handler  │
         │              │  (PyJWT)      │
         │              └───────────────┘
         │                     │
         │              ┌───────┴───────┐
         │              │ Rate Limiter  │
         │              │ (in-memory +  │
         │              │  slowapi)     │
         │              └───────────────┘
```

## 2. JWT Strategy

### Dual token
- **Algoritmo de firma**: **HS256** (simétrico). Decisión: simplicidad para monolito v1.0. Migración a RS256 se evalúa si escala a microservicios.
- **Access token**: JWT firmado (HS256), expira en **15 minutos**, transportado en **header `Authorization: Bearer <token>`**.
- **Refresh token**: JWT firmado con `secret` distinto (`JWT_REFRESH_SECRET`), expira en **7 días**, transportado en **cookie `refresh_token` HttpOnly, Secure, SameSite=Lax**.

### Claims obligatorios
```json
{
  "sub": "<user_id>",
  "empresa_id": "<empresa_id>",
  "rol": "<rol_nombre>",
  "iat": <timestamp>,
  "exp": <timestamp>,
  "type": "access" | "refresh"
}
```

### Flujo de login
1. Cliente envía `POST /auth/login` con `{email, contrasena}`.
2. API busca `Usuario` por email.
3. Valida contraseña con `bcrypt`.
4. Verifica `activo = true`.
5. Genera access token (15 min) y refresh token (7 días).
6. Setea cookie `refresh_token` (HttpOnly).
7. Responde con access token + datos básicos del usuario.

### Flujo de refresh (con rotación obligatoria)
1. Cliente envía solicitud con cookie `refresh_token`.
2. API valida refresh token (firma, expiración, `type: refresh`).
3. Genera nuevo access token (15 min).
4. **Genera nuevo refresh token**, invalida el anterior (tabla `RefreshToken` con `jti`, `exp`, `revoked`).
5. Setea nueva cookie `refresh_token`.

### Flujo de logout
1. Cliente envía `POST /auth/logout`.
2. API borra cookie `refresh_token` (max-age=0).
3. Cliente descarta access token del state (frontend).

## 3. Middleware de autenticación y multi-tenant

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    ...

async def require_auth(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
):
    request.state.empresa_id = current_user.empresa_id
    request.state.current_user = current_user
```

- El middleware se registra como **dependency** en los routers protegidos (`dependencies=[Depends(require_auth)]`).
- No se usa `dict` plano para bodies → Pydantic `BaseModel` con `extra='forbid'`.
- Inyección de `db: AsyncSession`, `current_user`, `tenant (empresa_id)` en cada router protegido.

### Protección de rutas públicas
Las rutas públicas se definen en el router de auth sin el dependency `require_auth`:
- `POST /auth/login`
- `POST /auth/recover`
- `POST /auth/reset`

Todo otro router incluye `dependencies=[Depends(require_auth)]`.

## 4. Recuperación de contraseña

### Token de recuperación
- Generado aleatoriamente con `secrets.token_urlsafe(32)`.
- Hash del token almacenado en DB (`TokenRecuperacion` o campo en `Usuario`): `token_hash`, `expiracion`, `usado`.
- Expiración: **1 hora** desde la generación.
- Uso único: una vez consumido, `usado = true`.

### Flujo
1. `POST /auth/recover` con `{email}`.
2. API busca usuario por email.
3. **Independientemente de si existe**, responde `200 OK` con mensaje genérico (evita enumeración de usuarios).
4. Si existe, genera token, guarda hash + expiración, envía email vía `EmailService`.
5. `POST /auth/reset` con `{token, nueva_contrasena, confirmacion}`.
6. API busca token por hash, valida expiración y `usado = false`.
7. Valida fuerza de contraseña (mín 8 chars, 1 mayúscula, 1 minúscula, 1 número).
8. Hashea nueva contraseña con bcrypt.
9. Actualiza `Usuario.contrasena_hash`, marca token como usado.

## 5. Rate Limiting

- Librería: `slowapi` (wrapper de limits para ASGI/FastAPI) o implementación custom con Redis (se decide slowapi por simplicidad en dev; Redis se introduce en fase DevOps).
- Regla: **5 intentos por IP+email en 60 segundos** para `POST /auth/login` y `POST /auth/recover`.
- Si se excede: `429 Too Many Requests`.
- Clave de rate limit: `f"auth:{ip}:{email}"`.

## 6. Email Service (SMTP genérico, enterprise-grade)

### Requerimiento de negocio
El proyecto está **vendido y en producción**. El envío de emails (recuperación de contraseña) debe ser **confiable, trackeable y con fallback**.

### Arquitectura: `EmailService` con SMTP genérico
- **Provider configurable** vía env var `EMAIL_PROVIDER`. Soporta: `resend` (default), `brevo`, `mailgun`, `smtp_generic`.
- **Transport**: protocolo SMTP estándar (port 587 STARTTLS o 465 SSL). Cada provider expone credenciales SMTP; no usamos APIs REST propietarias para no acoplarnos.
- **Configuración**:
  ```
  EMAIL_PROVIDER=resend
  SMTP_HOST=smtp.resend.com
  SMTP_PORT=587
  SMTP_USER=resend
  SMTP_PASSWORD=<api_key>
  SMTP_FROM=noreply@basile.app
  SMTP_TLS=true
  ```
- **Fallback**: si el envío falla (timeout, 5xx, credenciales inválidas), se loguea el error con nivel `CRITICAL` y se almacena el email en cola de reintentos (`email_queue` tabla o Redis en fase futura). Para v1.0: log crítico + alerta al admin (pantalla de health checks).
- **Template**: email de recuperación usa Jinja2 template con branding BASILE (no genérico). Asunto: "Recuperá tu contraseña — BASILE". Link: `${FRONTEND_URL}/restablecer-contrasena?token={token}`.
- **Tests**: en tests de integración se usa `SMTP_PROVIDER=mock` (in-memory capture) para no enviar emails reales.

### Decisión de provider (v1.0)
- **Default**: Resend (3000 emails/mes free, signup sin burocracia).
- **Alternativas listas**: Brevo (300/día), Mailgun, cualquier SMTP genérico.
- **Por qué no SendGrid**: el usuario fue rechazado por Twilio/SendGrid. SMTP genérico evita vendor lock-in.

## 7. Modelos Pydantic

```python
class LoginRequest(BaseModel):
    email: EmailStr
    contrasena: str
    model_config = ConfigDict(extra='forbid')

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioPublic

class RecoverRequest(BaseModel):
    email: EmailStr
    model_config = ConfigDict(extra='forbid')

class ResetRequest(BaseModel):
    token: str
    nueva_contrasena: str = Field(..., min_length=8)
    confirmacion: str
    model_config = ConfigDict(extra='forbid')
```

## 8. Seguridad adicional

- **bcrypt** para hashing de contraseñas (work factor 12).
- **No se usa `float` para dinero** → no aplica directamente a auth, pero se reafirma la regla global.
- **Zero trust**: input validation en frontend y backend.
- **RLS en PostgreSQL**: aunque el middleware filtra por `empresa_id`, las tablas de negocio tendrán RLS como capa de seguridad adicional (se activa en change de schema correspondiente).

## 9. Testing strategy

- **Unitarios**: hashing de bcrypt, generación/validación de JWT, rate limit key builder.
- **Integración** (pytest + pytest-asyncio + testcontainers):
  - login exitoso → access token válido, cookie refresh presente.
  - login fallido → 401, sin tokens.
  - login usuario inactivo → 403.
  - claims del access token → `sub`, `empresa_id`, `rol` correctos.
  - middleware → inyección de `empresa_id` en request.state.
  - rate limiting → 5 intentos, 6to devuelve 429.
  - recuperación completa → genera token, resetea contraseña, token queda usado.
  - recuperación con token expirado → 400.
  - enumeración de emails → respuesta genérica 200 aunque no exista.
