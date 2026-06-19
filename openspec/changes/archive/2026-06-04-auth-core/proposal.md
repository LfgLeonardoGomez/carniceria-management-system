# Proposal: auth-core (C-02)

## Qué
Implementar el núcleo de autenticación y autorización del sistema BASILE, incluyendo:
- Login con JWT (access + refresh tokens).
- Middleware de autenticación que inyecta `empresa_id` para aislamiento multi-tenant.
- Recuperación y restablecimiento de contraseña con tokens de un solo uso.
- Protección de rutas: todo endpoint excepto las rutas públicas requiere token válido.
- Rate limiting en endpoints de autenticación para mitigar ataques de fuerza bruta.

## Por qué
- **Bloqueante para todo el resto del sistema**: Sin auth no se puede garantizar RN-SEG-02 (filtrado por empresa_id) ni RN-SEG-03 (acceso restringido a la empresa del usuario).
- **Seguridad desde el día 1**: Aislamiento de datos entre empresas es crítico en un SaaS multi-tenant (carnicerías competidoras).
- **Base para auditoría**: El flujo de login genera `ultimo_acceso` y senta las bases para RN-AUD-01 (registro de usuario, acción, fecha/hora).

## Alcance
- Endpoints: `POST /auth/login`, `POST /auth/recover`, `POST /auth/reset`.
- Middleware FastAPI que inyecta `current_user` y `empresa_id` en request.state.
- Rate limiting por IP+email en auth.
- Tests unitarios y de integración con PostgreSQL real (testcontainers).

## Fuera de alcance
- Envío real de emails (se simula con log/console; el SMTP se define en C-XX).
- Gestión de usuarios / CRUD de usuarios (C-03 o posterior).
- Frontend de login / recuperación (C-XX o se asume que el SPA consume la API).

## Dependencias
- C-01-foundation-setup (modelos `Usuario`, `Rol`, `Empresa`, infraestructura DB ya disponible).

## Riesgos y mitigaciones
| Riesgo | Mitigación |
|--------|------------|
| Filtración de tenant (data leakage) | Middleware obligatorio que extrae `empresa_id` del JWT; RLS como capa adicional en PostgreSQL. |
| Robo de refresh token | HttpOnly cookie, Secure en producción, SameSite=Lax. |
| Fuerza bruta en login | Rate limiting 5 intentos / 60s por IP+email. |
| Enumeración de emails en recover | Respuesta genérica sin revelar existencia del email. |
