import os
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_docker_compose_exists_and_has_services():
    """Task 1.1: docker-compose.yml con postgres, backend, frontend."""
    path = PROJECT_ROOT / "docker-compose.yml"
    assert path.exists(), "docker-compose.yml no existe"
    content = path.read_text()
    assert "postgres:" in content, "No define servicio postgres"
    assert "backend:" in content, "No define servicio backend"
    assert "frontend:" in content, "No define servicio frontend"
    assert "5432:5432" in content, "PostgreSQL no expone puerto 5432"
    assert "8000:8000" in content, "Backend no expone puerto 8000"
    assert "5173:5173" in content, "Frontend no expone puerto 5173"


def test_backend_dockerfile_exists():
    """Task 1.2: Dockerfile para backend."""
    path = PROJECT_ROOT / "backend" / "Dockerfile"
    assert path.exists(), "backend/Dockerfile no existe"
    content = path.read_text()
    assert "python" in content.lower() or "fastapi" in content.lower() or "uvicorn" in content.lower(), \
        "Dockerfile de backend no referencia Python/FastAPI/uvicorn"
    assert "requirements.txt" in content, "Dockerfile no copia requirements.txt"


def test_frontend_dockerfile_exists():
    """Task 1.3: Dockerfile para frontend."""
    path = PROJECT_ROOT / "frontend" / "Dockerfile"
    assert path.exists(), "frontend/Dockerfile no existe"
    content = path.read_text()
    assert "node" in content.lower() or "vite" in content.lower() or "npm" in content.lower(), \
        "Dockerfile de frontend no referencia Node/Vite/npm"
    assert "package.json" in content, "Dockerfile no copia package.json"


def test_root_env_example_exists():
    """Task 1.4: .env.example en raíz con variables requeridas."""
    path = PROJECT_ROOT / ".env.example"
    assert path.exists(), ".env.example no existe en raíz"
    content = path.read_text()
    required = [
        "DATABASE_URL",
        "JWT_SECRET",
        "REFRESH_TOKEN_SECRET",
        "EMAIL_HOST",
        "EMAIL_PORT",
        "EMAIL_USER",
        "EMAIL_PASS",
        "EMAIL_FROM",
        "FRONTEND_URL",
        "PORT",
        "CORS_ORIGIN",
        "UPLOAD_PATH",
        "NODE_ENV",
    ]
    for var in required:
        assert var in content, f"Falta variable {var} en .env.example"


def test_frontend_env_example_exists():
    """Task 1.5: .env.example en frontend."""
    path = PROJECT_ROOT / "frontend" / ".env.example"
    assert path.exists(), "frontend/.env.example no existe"
    content = path.read_text()
    assert "VITE_API_URL" in content, "Falta VITE_API_URL en frontend/.env.example"


def test_gitignores_exist():
    """Task 1.6: .gitignore en raíz y frontend."""
    root_gitignore = PROJECT_ROOT / ".gitignore"
    frontend_gitignore = PROJECT_ROOT / "frontend" / ".gitignore"
    assert root_gitignore.exists(), ".gitignore no existe en raíz"
    assert frontend_gitignore.exists(), ".gitignore no existe en frontend/"
    for gi in [root_gitignore, frontend_gitignore]:
        content = gi.read_text()
        assert ".env" in content, f"{gi} no ignora .env"
        assert ".env.local" in content, f"{gi} no ignora .env.local"


def test_readme_has_docker_compose_instructions():
    """Task 1.7: README.md documenta docker-compose up."""
    path = PROJECT_ROOT / "README.md"
    assert path.exists(), "README.md no existe"
    content = path.read_text()
    assert "docker-compose up" in content or "docker compose up" in content, \
        "README no documenta docker-compose up"
    assert "localhost:8000" in content, "README no menciona backend localhost:8000"
    assert "localhost:5173" in content, "README no menciona frontend localhost:5173"
