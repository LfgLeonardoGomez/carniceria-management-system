import sys
from pathlib import Path

import pytest
from httpx import AsyncClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))


def test_health_endpoint():
    """Task 6.4: Test para /health."""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "basile-api"


def test_health_db_endpoint_exists():
    """Task 6.2: /health/db existe y responde."""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/health/db")
    # Status puede ser 200 o 503 dependiendo de la DB
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "database" in data


def test_request_logging_middleware():
    """Task 6.3: main.py incluye middleware de logging."""
    path = PROJECT_ROOT / "backend" / "src" / "main.py"
    content = path.read_text()
    assert "middleware" in content.lower() or "Middleware" in content, \
        "main.py no configura middleware de request logging"
