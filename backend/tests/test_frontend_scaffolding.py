import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_ROOT = PROJECT_ROOT / "frontend"


def test_frontend_package_json_exists():
    """Task 3.1: Proyecto React inicializado con Vite."""
    path = FRONTEND_ROOT / "package.json"
    assert path.exists(), "frontend/package.json no existe"
    data = json.loads(path.read_text())
    assert "react" in data.get("dependencies", {}), "No dependencia react"
    assert "react-dom" in data.get("dependencies", {}), "No dependencia react-dom"
    assert "vite" in data.get("devDependencies", {}), "No devDependency vite"


def test_tsconfig_strict():
    """Task 3.3: tsconfig.json con strict: true."""
    path = FRONTEND_ROOT / "tsconfig.json"
    assert path.exists(), "frontend/tsconfig.json no existe"
    data = json.loads(path.read_text())
    compiler_options = data.get("compilerOptions", {})
    assert compiler_options.get("strict") is True, "strict no es true"
    assert compiler_options.get("noImplicitAny") is True, "noImplicitAny no es true"


def test_frontend_directory_structure():
    """Task 3.4: Estructura por features y shared."""
    features = FRONTEND_ROOT / "src" / "features"
    domains = [
        "auth", "dashboard", "productos", "clientes", "proveedores",
        "compras", "desposte", "stock", "ventas", "caja",
        "gastos", "cuentas-corrientes", "reportes", "notifications",
    ]
    for domain in domains:
        assert (features / domain).is_dir(), f"Falta features/{domain}"

    shared = FRONTEND_ROOT / "src" / "shared"
    for sub in ["components", "hooks", "utils", "services", "types"]:
        assert (shared / sub).is_dir(), f"Falta shared/{sub}"

    store = FRONTEND_ROOT / "src" / "store"
    assert store.is_dir(), "Falta src/store"

    pages = FRONTEND_ROOT / "src" / "pages"
    assert pages.is_dir(), "Falta src/pages"

    styles = FRONTEND_ROOT / "src" / "styles"
    assert styles.is_dir(), "Falta src/styles"


def test_app_tsx_exists():
    """Task 3.5: App.tsx con routing base."""
    path = FRONTEND_ROOT / "src" / "App.tsx"
    assert path.exists(), "src/App.tsx no existe"
    content = path.read_text()
    assert "Router" in content or "Route" in content or "BrowserRouter" in content, \
        "App.tsx no parece tener routing"


def test_auth_store_exists():
    """Task 3.6: Zustand authStore.ts."""
    path = FRONTEND_ROOT / "src" / "store" / "authStore.ts"
    assert path.exists(), "src/store/authStore.ts no existe"
    content = path.read_text()
    assert "zustand" in content.lower() or "create" in content, \
        "authStore.ts no usa Zustand"


def test_api_types_exist():
    """Task 3.7: Tipos base de API."""
    path = FRONTEND_ROOT / "src" / "shared" / "types" / "api.ts"
    assert path.exists(), "src/shared/types/api.ts no existe"
    content = path.read_text()
    assert "ApiResponse" in content, "Falta tipo ApiResponse"
    assert "ApiError" in content, "Falta tipo ApiError"


def test_eslint_config_exists():
    """Task 3.8: ESLint config para React + TypeScript."""
    eslint_js = FRONTEND_ROOT / "eslint.config.js"
    eslint_json = FRONTEND_ROOT / ".eslintrc.json"
    eslint_cjs = FRONTEND_ROOT / ".eslintrc.cjs"
    assert any(p.exists() for p in [eslint_js, eslint_json, eslint_cjs]), \
        "No existe configuración de ESLint"


def test_vite_config_proxy():
    """Task 3.9: vite.config.ts con proxy al backend."""
    path = FRONTEND_ROOT / "vite.config.ts"
    assert path.exists(), "vite.config.ts no existe"
    content = path.read_text()
    assert "proxy" in content, "vite.config.ts no define proxy"
    assert "8000" in content, "proxy no apunta al puerto 8000 del backend"
