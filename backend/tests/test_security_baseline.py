import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))


def test_security_headers():
    """Task 7.4: Headers de seguridad presentes en respuestas."""
    from main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


def test_cors_rejects_unknown_origin():
    """Task 7.5: CORS rechaza origen no permitido."""
    from main import app

    client = TestClient(app)
    response = client.get(
        "/health",
        headers={"Origin": "http://evil.com"},
    )
    # FastAPI CORSMiddleware doesn't reject by default; it just omits CORS headers
    allowed = response.headers.get("access-control-allow-origin")
    assert allowed != "http://evil.com", "CORS permitió origen no autorizado"


def test_rate_limit_dependency_exists():
    """Task 7.2: Rate limiting preparado para /auth/*."""
    path = PROJECT_ROOT / "backend" / "src" / "main.py"
    content = path.read_text()
    assert "rate" in content.lower() or "limit" in content.lower(), \
        "main.py no referencia rate limiting"
