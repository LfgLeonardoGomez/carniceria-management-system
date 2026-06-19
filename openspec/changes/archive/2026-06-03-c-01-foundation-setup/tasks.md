## 1. Docker y Entorno de Desarrollo

- [x] 1.1 Crear `docker-compose.yml` con servicios: `postgres` (14+), `backend` (FastAPI + uvicorn reload), `frontend` (Vite dev server)
- [x] 1.2 Crear `Dockerfile` para backend (Python 3.11+ slim, multistage opcional)
- [x] 1.3 Crear `Dockerfile` para frontend (Node 20+ alpine)
- [x] 1.4 Crear `.env.example` en raíz del proyecto con todas las variables: `DATABASE_URL`, `JWT_SECRET`, `REFRESH_TOKEN_SECRET`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USER`, `EMAIL_PASS`, `EMAIL_FROM`, `FRONTEND_URL`, `PORT`, `CORS_ORIGIN`, `UPLOAD_PATH`, `NODE_ENV`
- [x] 1.5 Crear `.env.example` en `frontend/` con: `VITE_API_URL`
- [x] 1.6 Agregar `.env` y `.env.local` a `.gitignore` en raíz y frontend
- [x] 1.7 Documentar en `README.md` el comando `docker-compose up --build` y troubleshooting básico

## 2. Backend FastAPI — Scaffolding

- [x] 2.1 Crear `backend/requirements.txt` con: `fastapi>=0.100`, `uvicorn[standard]`, `sqlmodel>=0.0.14`, `sqlalchemy>=2.0`, `psycopg[binary,pool]>=3.1`, `alembic`, `pydantic[email]`, `python-dotenv`, `python-json-logger`
- [x] 2.2 Crear `backend/requirements-dev.txt` con: `pytest>=7.0`, `pytest-asyncio`, `httpx`, `factory-boy`, `testcontainers`, `ruff`, `mypy`
- [x] 2.3 Crear estructura de directorios en `backend/src/`: `modules/{auth,empresa,usuario,producto,cliente,proveedor,compra,desposte,stock,venta,caja,gasto,cuenta-corriente,reporte,auditoria,notificacion}/`, `common/`, `config/`, `database/migrations/`, `database/seeds/`
- [x] 2.4 Crear `backend/src/main.py` con app FastAPI, inclusión de routers base, middleware de logging y CORS
- [x] 2.5 Crear `backend/src/config/settings.py` con Pydantic Settings (carga desde `.env`) y validación de variables obligatorias
- [x] 2.6 Crear `backend/src/config/database.py` con `create_async_engine`, `AsyncSession` factory y función `get_db()` para inyección de dependencias
- [x] 2.7 Crear `backend/src/common/logging.py` con formatter JSON para logs estructurados
- [x] 2.8 Crear `backend/src/common/exceptions.py` con excepciones base del dominio y handler global para FastAPI
- [x] 2.9 Configurar `backend/pyproject.toml` (o `setup.cfg`) para `pytest` con `asyncio_mode = auto`

## 3. Frontend React — Scaffolding

- [x] 3.1 Inicializar proyecto React con Vite (`npm create vite@latest frontend -- --template react-ts`)
- [x] 3.2 Instalar dependencias base: `react@18`, `react-dom@18`, `zustand`, `react-router-dom`, `axios` (o `fetch` wrapper tipado)
- [x] 3.3 Configurar `frontend/tsconfig.json` con `"strict": true` y `"noImplicitAny": true`
- [x] 3.4 Crear estructura de directorios en `frontend/src/`: `features/{auth,dashboard,productos,clientes,proveedores,compras,desposte,stock,ventas,caja,gastos,cuentas-corrientes,reportes,notifications}/`, `shared/{components,hooks,utils,services,types}/`, `store/`, `pages/`, `styles/`
- [x] 3.5 Crear `frontend/src/App.tsx` con routing base y layout principal
- [x] 3.6 Crear `frontend/src/store/authStore.ts` como ejemplo de Zustand con tipado TypeScript
- [x] 3.7 Crear `frontend/src/shared/types/api.ts` con tipos base para respuestas del backend (ApiResponse, ApiError)
- [x] 3.8 Crear `.eslintrc` o `eslint.config.js` con reglas recomendadas para React + TypeScript strict
- [x] 3.9 Crear `frontend/vite.config.ts` con proxy al backend en dev (`/api → http://localhost:8000`)

## 4. Base de Datos y Alembic

- [x] 4.1 Crear `backend/alembic.ini` apuntando a `DATABASE_URL`
- [x] 4.2 Configurar `backend/src/database/migrations/env.py` con `AsyncEngine` y metadata de SQLModel/SQLAlchemy
- [x] 4.3 Crear modelo SQLModel `Empresa` en `backend/src/modules/empresa/models.py` con todos los campos del KB
- [x] 4.4 Crear modelo SQLModel `Rol` en `backend/src/modules/auth/models.py` (o `usuario/models.py`) con campos del KB
- [x] 4.5 Crear modelo SQLModel `Usuario` en `backend/src/modules/auth/models.py` (o `usuario/models.py`) con campos del KB, FK a `Empresa` y `Rol`
- [x] 4.6 Generar migración inicial con `alembic revision --autogenerate -m "initial schema"` y verificar que incluye `empresa`, `rol`, `usuario`
- [x] 4.7 Aplicar migración con `alembic upgrade head` y verificar tablas en PostgreSQL
- [x] 4.8 Agregar índices obligatorios: `empresa_id` en `usuario`, `email` único en `usuario`

## 5. Seed Data

- [x] 5.1 Crear `backend/src/database/seeds/run.py` como entrypoint para ejecutar seeds
- [x] 5.2 Crear `backend/src/database/seeds/roles.py` que inserta: Administrador, Encargado, Cajero, Vendedor (idempotente)
- [x] 5.3 Crear `backend/src/database/seeds/categorias_producto.py` que inserta: Carne vacuna, Carne de cerdo, Pollo, Embutidos, Otros (idempotente)
- [x] 5.4 Crear `backend/src/database/seeds/tipos_corte.py` que inserta los 12 cortes de desposte (idempotente)
- [x] 5.5 Crear `backend/src/database/seeds/categorias_gasto.py` que inserta las 11 categorías de gasto (idempotente)
- [x] 5.6 Ejecutar seeds y verificar en PostgreSQL que todos los datos están presentes
- [x] 5.7 Escribir test de integración que ejecuta seeds y valida conteo de registros insertados

## 6. Health Checks y Monitoreo

- [x] 6.1 Crear `backend/src/modules/health/router.py` con `GET /health` que retorna `{ "status": "ok", "service": "basile-api" }`
- [x] 6.2 Crear `GET /health/db` que ejecuta una query simple `SELECT 1` con `AsyncSession` y retorna estado de conexión
- [x] 6.3 Agregar middleware de logging en `main.py` que loguea cada request en JSON con: timestamp, método, path, status_code, duration_ms
- [x] 6.4 Escribir test para `/health` que verifica status 200 y body correcto
- [x] 6.5 Escribir test para `/health/db` que verifica status 200 cuando DB está up y 503 cuando está down (mock opcional)

## 7. Seguridad Base

- [x] 7.1 Configurar CORS en `main.py` usando `CORSMiddleware` de FastAPI con origen desde `CORS_ORIGIN` (variable de entorno)
- [x] 7.2 Crear dependencia `RateLimit` o middleware preparado para limitar requests en `/auth/*` (5 intentos / 60s por IP+email)
- [x] 7.3 Agregar headers de seguridad en responses: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`
- [x] 7.4 Escribir test que verifica headers de seguridad en respuesta de cualquier endpoint
- [x] 7.5 Escribir test que verifica CORS rechaza origen no permitido

## 8. CI/CD Pipeline Skeleton

- [x] 8.1 Crear `.github/workflows/ci.yml` con jobs: `backend-lint` (ruff), `backend-typecheck` (mypy), `backend-test` (pytest)
- [x] 8.2 Agregar job `frontend-lint` (eslint) y `frontend-typecheck` (tsc --noEmit) al workflow
- [x] 8.3 Configurar job `frontend-test` (vitest) en el workflow
- [x] 8.4 Usar `services` de GitHub Actions para levantar PostgreSQL en job de backend-test
- [x] 8.5 Verificar que el workflow pasa en push/PR (ejecutar `act` localmente si está disponible, o validar sintaxis YAML)

## 9. Tests de Integración y Validación Final

- [x] 9.1 Escribir test de conexión a DB: crear engine, conectar, ejecutar `SELECT 1`, cerrar
- [x] 9.2 Escribir test de seed data completa: ejecutar todos los seeds y validar conteo exacto de registros por tabla
- [x] 9.3 Escribir test de health check: verificar `/health` y `/health/db` desde cliente HTTP
- [x] 9.4 Escribir test de estructura de proyecto: verificar que existen directorios y archivos críticos
- [x] 9.5 Ejecutar `docker-compose up --build` y validar manualmente que backend responde en `:8000`, frontend en `:5173`, y PostgreSQL en `:5432`
- [x] 9.6 Ejecutar `pytest` en backend y confirmar que todos los tests pasan
- [x] 9.7 Ejecutar `npm run test` en frontend y confirmar que pasa al menos un test de ejemplo
