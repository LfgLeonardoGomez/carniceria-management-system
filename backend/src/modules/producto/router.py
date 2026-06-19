from typing import Optional

from fastapi import APIRouter, Depends, Request, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.modules.auth.dependencies import require_auth
from src.modules.producto import schemas
from src.modules.producto import service
from src.modules.producto import import_service
from src.common.rbac import require_role
from src.common.exceptions import ConflictException, BasileException

router = APIRouter()


# ---------------------------------------------------------------------------
# CategoriaProducto endpoints — MUST come before /{producto_id} routes
# ---------------------------------------------------------------------------
@router.post(
    "/categorias",
    response_model=schemas.CategoriaProductoPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("productos:create"))],
)
async def create_categoria(
    request: Request,
    payload: schemas.CategoriaProductoCreate,
    db: AsyncSession = Depends(get_db),
) -> schemas.CategoriaProductoPublic:
    empresa_id = request.state.empresa_id
    categoria = await service.crear_categoria(db, empresa_id, payload.nombre)
    return schemas.CategoriaProductoPublic.model_validate(categoria.model_dump())


@router.get(
    "/categorias",
    response_model=schemas.PaginatedCategoriaResponse,
    dependencies=[Depends(require_role("productos:read"))],
)
async def list_categorias(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> schemas.PaginatedCategoriaResponse:
    empresa_id = request.state.empresa_id
    categorias = await service.listar_categorias(db, empresa_id)
    return schemas.PaginatedCategoriaResponse(
        items=[schemas.CategoriaProductoPublic.model_validate(c.model_dump()) for c in categorias],
        total=len(categorias),
        skip=0,
        limit=len(categorias),
    )


@router.put(
    "/categorias/{categoria_id}",
    response_model=schemas.CategoriaProductoPublic,
    dependencies=[Depends(require_role("productos:update"))],
)
async def update_categoria(
    request: Request,
    categoria_id: str,
    payload: schemas.CategoriaProductoUpdate,
    db: AsyncSession = Depends(get_db),
) -> schemas.CategoriaProductoPublic:
    empresa_id = request.state.empresa_id
    import uuid
    if not payload.nombre:
        raise ConflictException("El nombre es requerido")
    categoria = await service.actualizar_categoria(
        db, empresa_id, uuid.UUID(categoria_id), payload.nombre
    )
    return schemas.CategoriaProductoPublic.model_validate(categoria.model_dump())


@router.delete(
    "/categorias/{categoria_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("productos:delete"))],
)
async def delete_categoria(
    request: Request,
    categoria_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    empresa_id = request.state.empresa_id
    import uuid
    await service.eliminar_categoria(db, empresa_id, uuid.UUID(categoria_id))


# ---------------------------------------------------------------------------
# Producto endpoints
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=schemas.ProductoPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("productos:create"))],
)
async def create_producto(
    request: Request,
    payload: schemas.ProductoCreate,
    db: AsyncSession = Depends(get_db),
) -> schemas.ProductoPublic:
    empresa_id = request.state.empresa_id
    producto = await service.crear_producto(
        db=db,
        empresa_id=empresa_id,
        plu=payload.plu,
        nombre=payload.nombre,
        categoria_id=payload.categoria_id,
        precio_publico=payload.precio_publico,
        precio_mayorista=payload.precio_mayorista,
        costo_por_kilo=payload.costo_por_kilo,
        stock_actual=payload.stock_actual,
        stock_minimo=payload.stock_minimo,
    )
    return schemas.ProductoPublic.model_validate(producto.model_dump())


@router.get(
    "",
    response_model=schemas.PaginatedProductoResponse,
    dependencies=[Depends(require_role("productos:read"))],
)
async def list_productos(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    categoria_id: Optional[str] = None,
    activo: Optional[bool] = True,
    db: AsyncSession = Depends(get_db),
) -> schemas.PaginatedProductoResponse:
    empresa_id = request.state.empresa_id
    cat_id = None
    if categoria_id:
        import uuid
        try:
            cat_id = uuid.UUID(categoria_id)
        except ValueError:
            cat_id = None

    productos, total = await service.listar_productos(
        db=db,
        empresa_id=empresa_id,
        skip=skip,
        limit=limit,
        search=search,
        categoria_id=cat_id,
        activo=activo,
    )
    return schemas.PaginatedProductoResponse(
        items=[schemas.ProductoPublic.model_validate(p.model_dump()) for p in productos],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{producto_id}",
    response_model=schemas.ProductoPublic,
    dependencies=[Depends(require_role("productos:read"))],
)
async def get_producto(
    request: Request,
    producto_id: str,
    db: AsyncSession = Depends(get_db),
) -> schemas.ProductoPublic:
    empresa_id = request.state.empresa_id
    import uuid
    producto = await service.obtener_producto(db, empresa_id, uuid.UUID(producto_id))
    return schemas.ProductoPublic.model_validate(producto.model_dump())


@router.put(
    "/{producto_id}",
    response_model=schemas.ProductoPublic,
    dependencies=[Depends(require_role("productos:update"))],
)
async def update_producto(
    request: Request,
    producto_id: str,
    payload: schemas.ProductoUpdate,
    db: AsyncSession = Depends(get_db),
) -> schemas.ProductoPublic:
    empresa_id = request.state.empresa_id
    import uuid
    producto = await service.actualizar_producto(
        db=db,
        empresa_id=empresa_id,
        producto_id=uuid.UUID(producto_id),
        plu=payload.plu,
        nombre=payload.nombre,
        categoria_id=payload.categoria_id,
        precio_publico=payload.precio_publico,
        precio_mayorista=payload.precio_mayorista,
        costo_por_kilo=payload.costo_por_kilo,
        stock_actual=payload.stock_actual,
        stock_minimo=payload.stock_minimo,
    )
    return schemas.ProductoPublic.model_validate(producto.model_dump())


@router.patch(
    "/{producto_id}/activo",
    response_model=schemas.ProductoPublic,
    dependencies=[Depends(require_role("productos:update"))],
)
async def toggle_producto_activo(
    request: Request,
    producto_id: str,
    payload: schemas.ProductoToggleActivo,
    db: AsyncSession = Depends(get_db),
) -> schemas.ProductoPublic:
    empresa_id = request.state.empresa_id
    import uuid
    if payload.activo:
        producto = await service.reactivar_producto(db, empresa_id, uuid.UUID(producto_id))
    else:
        producto = await service.desactivar_producto(db, empresa_id, uuid.UUID(producto_id))
    return schemas.ProductoPublic.model_validate(producto.model_dump())


@router.post(
    "/import",
    dependencies=[Depends(require_role("productos:create"))],
)
async def import_preview(
    request: Request,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise BasileException("Solo se aceptan archivos .xlsx", status_code=415)

    empresa_id = request.state.empresa_id
    file_data = await file.read()
    preview = await import_service.generar_preview(db, empresa_id, file_data)
    return {
        "session_id": preview.session_id,
        "total_filas": preview.total_filas,
        "filas_validas": [
            {
                "row_num": f.row_num,
                "plu": f.plu,
                "nombre": f.nombre,
                "categoria": f.categoria_nombre,
                "precio_publico": str(f.precio_publico),
                "precio_mayorista": str(f.precio_mayorista),
                "costo_por_kilo": str(f.costo_por_kilo),
                "stock_actual": str(f.stock_actual),
                "stock_minimo": str(f.stock_minimo) if f.stock_minimo else None,
            }
            for f in preview.filas_validas
        ],
        "filas_invalidas": [
            {
                "row_num": f.row_num,
                "plu": f.plu,
                "nombre": f.nombre,
                "errores": f.errores,
            }
            for f in preview.filas_invalidas
        ],
        "validas_count": len(preview.filas_validas),
        "invalidas_count": len(preview.filas_invalidas),
    }


@router.post(
    "/import/confirm",
    dependencies=[Depends(require_role("productos:create"))],
)
async def import_confirm(
    request: Request,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    empresa_id = request.state.empresa_id
    result = await import_service.confirmar_importacion(db, session_id, empresa_id)
    return result
