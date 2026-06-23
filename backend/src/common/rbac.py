"""Matriz de permisos RBAC inmutable.

Los 5 roles del sistema y sus permisos sobre recursos/operaciones.
La matriz está definida en código porque los roles son estáticos por diseño.

Roles:
  superadmin — acceso global, gestión de empresas y admins
  admin      — administrador de una empresa (tenant)
  encargado  — gestión de stock, compras, desposte
  cajero     — ventas y caja
  vendedor   — ventas
"""

from fastapi import Request

from src.common.exceptions import ForbiddenException

# ---------------------------------------------------------------------------
# Matriz inmutable: rol -> conjunto de permisos (formato "recurso:operacion")
# NINGÚN rol tiene wildcard "*". Todos los permisos son explícitos.
# ---------------------------------------------------------------------------
def normalize_rol(rol_nombre: str | None) -> str | None:
    """Normaliza un nombre de rol al formato canónico de PERMISSION_MATRIX.

    Mapea variantes de casing y nombres en español/castellano
    a los keys lowercase usados internamente.
    """
    if not rol_nombre:
        return None
    lowered = rol_nombre.strip().lower()
    mapping = {
        "administrador": "admin",
        "admin": "admin",
        "encargado": "encargado",
        "cajero": "cajero",
        "vendedor": "vendedor",
        "superadmin": "superadmin",
    }
    return mapping.get(lowered)


PERMISSION_MATRIX: dict[str, set[str]] = {
    "superadmin": {
        "empresas:create",
        "empresas:read",
        "empresas:update",
        "empresas:delete",
        "empresas:admin",
        "usuarios:create",
        "usuarios:read",
        "usuarios:update",
        "usuarios:delete",
        "soporte:impersonate",
        "auditoria:read",
    },
    "admin": {
        "empresas:admin",
        "usuarios:create",
        "usuarios:read",
        "usuarios:update",
        "usuarios:delete",
        "stock:read",
        "stock:update",
        "stock:create",
        "ventas:create",
        "ventas:read",
        "compras:create",
        "compras:read",
        "desposte:create",
        "desposte:read",
        "clientes:create",
        "clientes:read",
        "clientes:update",
        "clientes:delete",
        "proveedores:create",
        "proveedores:read",
        "proveedores:update",
        "proveedores:delete",
        "productos:create",
        "productos:read",
        "productos:update",
        "productos:delete",
        "cuenta-corriente:read",
        "cuenta-corriente:update",
        "reportes:read",
        "gastos:create",
        "gastos:read",
        "caja:operate",
    },
    "encargado": {
        "stock:read",
        "stock:update",
        "stock:create",
        "ventas:create",
        "ventas:read",
        "compras:create",
        "compras:read",
        "desposte:create",
        "desposte:read",
        "clientes:create",
        "clientes:read",
        "clientes:update",
        "proveedores:create",
        "proveedores:read",
        "proveedores:update",
        "productos:create",
        "productos:read",
        "productos:update",
        "cuenta-corriente:read",
        "cuenta-corriente:update",
        "reportes:read",
        "gastos:create",
        "gastos:read",
        "caja:operate",
    },
    "cajero": {
        "ventas:create",
        "ventas:read",
        "caja:operate",
        "clientes:create",
        "clientes:read",
        "productos:read",
        # C-14 PO Decision: cajero can register payments (KB US-015)
        "cuenta-corriente:read",
        "cuenta-corriente:update",
    },
    "vendedor": {
        "ventas:create",
        "ventas:read",
        "productos:read",
    },
}


def has_permission(rol_nombre: str, permiso: str) -> bool:
    """Verifica si un rol tiene un permiso específico según la matriz.

    Solo permisos explícitos — no hay wildcard.
    """
    canonical = normalize_rol(rol_nombre)
    if not canonical or not permiso:
        return False
    perms = PERMISSION_MATRIX.get(canonical)
    if perms is None:
        return False
    return permiso in perms


def require_role(permiso: str):
    """Factory de dependency FastAPI que valida permiso RBAC.

    Uso:
        @router.post("/usuarios", dependencies=[Depends(require_role("usuarios:create"))])
    """
    async def _require_role(request: Request) -> None:
        current_user = getattr(request.state, "current_user", None)
        if current_user is None:
            raise ForbiddenException(f"Permiso insuficiente: {permiso}")

        rol_nombre = None
        if hasattr(current_user, "rol") and current_user.rol is not None:
            rol_nombre = current_user.rol.nombre
        elif hasattr(current_user, "rol_nombre"):
            rol_nombre = current_user.rol_nombre

        canonical = normalize_rol(rol_nombre)
        if not canonical or not has_permission(canonical, permiso):
            raise ForbiddenException(f"Permiso insuficiente: {permiso}")

    return _require_role
