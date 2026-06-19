import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_ROOT = PROJECT_ROOT / "frontend"


def test_package_json_has_zustand_and_router():
    """Triangulate Task 3.2: dependencias base instaladas."""
    path = FRONTEND_ROOT / "package.json"
    data = json.loads(path.read_text())
    deps = data.get("dependencies", {})
    assert "zustand" in deps, "Falta zustand"
    assert "react-router-dom" in deps, "Falta react-router-dom"
    assert "axios" in deps, "Falta axios"


def test_app_tsx_uses_browser_router():
    """Triangulate Task 3.5: App.tsx usa BrowserRouter."""
    content = (FRONTEND_ROOT / "src" / "App.tsx").read_text()
    assert "BrowserRouter" in content, "App.tsx no usa BrowserRouter"
    assert "Routes" in content, "App.tsx no usa Routes"
    assert "Route" in content, "App.tsx no usa Route"


def test_auth_store_is_typed():
    """Triangulate Task 3.6: authStore tiene tipado TypeScript."""
    content = (FRONTEND_ROOT / "src" / "store" / "authStore.ts").read_text()
    assert "interface AuthState" in content, "authStore no define AuthState"
    assert "create<AuthState>" in content, "authStore no tipa create<>"


def test_no_class_components():
    """Triangulate spec: no hay componentes de clase."""
    src = FRONTEND_ROOT / "src"
    for tsx in src.rglob("*.tsx"):
        content = tsx.read_text()
        assert "extends Component" not in content, f"{tsx} tiene clase de componente"
        assert "extends React.Component" not in content, f"{tsx} tiene React.Component"


def test_vite_config_uses_define_config():
    """Triangulate Task 3.9: vite.config.ts usa defineConfig."""
    content = (FRONTEND_ROOT / "vite.config.ts").read_text()
    assert "defineConfig" in content, "vite.config.ts no usa defineConfig"
    assert "@vitejs/plugin-react" in content, "vite.config.ts no usa plugin-react"
