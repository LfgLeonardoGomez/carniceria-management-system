import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import AsyncSessionLocal

router = APIRouter()


@router.get("")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "basile-api"}


@router.get("/db")
async def health_db() -> JSONResponse:
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        return JSONResponse(
            status_code=200,
            content={"status": "ok", "database": "connected"},
        )
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unreachable"},
        )
