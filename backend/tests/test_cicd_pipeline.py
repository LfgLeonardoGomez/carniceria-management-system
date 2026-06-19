import yaml
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_ci_workflow_exists():
    """Task 8.1-8.5: CI/CD pipeline skeleton existe y tiene jobs requeridos."""
    path = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
    assert path.exists(), ".github/workflows/ci.yml no existe"

    data = yaml.safe_load(path.read_text())
    jobs = data.get("jobs", {})

    required_jobs = [
        "backend-lint",
        "backend-typecheck",
        "backend-test",
        "frontend-lint",
        "frontend-typecheck",
        "frontend-test",
    ]
    for job in required_jobs:
        assert job in jobs, f"Falta job {job} en ci.yml"

    # 8.4: PostgreSQL service en backend-test
    backend_test = jobs.get("backend-test", {})
    services = backend_test.get("services", {})
    assert "postgres" in services, "backend-test no tiene servicio postgres"

    # Validate YAML syntax (already done by yaml.safe_load)
    assert data.get("name") == "CI", "Workflow no se llama CI"
