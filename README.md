# BASILE

SaaS multiempresa para gestión integral de carnicerías.

## Inicio rápido (Docker)

```bash
# 1. Copiar variables de entorno
cp .env.example .env
cp frontend/.env.example frontend/.env

# 2. Levantar servicios
docker-compose up --build

# 3. Verificar
# Backend health:  http://localhost:8000/health
# Frontend dev:    http://localhost:5173
# PostgreSQL:      localhost:5432
```

## Troubleshooting

- **Puertos ocupados**: asegurate de que los puertos `5432`, `8000` y `5173` estén libres.
- **Permisos en Windows/WSL**: ejecutá Docker Desktop con WSL2 backend.
- **Cambios no se reflejan**: el backend usa `--reload` y el frontend HMR de Vite.

## Estructura

- `backend/` — FastAPI + SQLModel/SQLAlchemy 2.0
- `frontend/` — React 18 + TypeScript + Vite
- `knowledge-base/` — Documentación de dominio
