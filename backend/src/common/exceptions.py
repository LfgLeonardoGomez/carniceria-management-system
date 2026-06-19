from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class BasileException(Exception):
    """Base exception for domain errors."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundException(BasileException):
    def __init__(self, message: str = "Recurso no encontrado") -> None:
        super().__init__(message, status_code=404)


class UnauthorizedException(BasileException):
    def __init__(self, message: str = "No autorizado") -> None:
        super().__init__(message, status_code=401)


class ForbiddenException(BasileException):
    def __init__(self, message: str = "Acceso denegado") -> None:
        super().__init__(message, status_code=403)


class ConflictException(BasileException):
    def __init__(self, message: str = "Conflicto de datos") -> None:
        super().__init__(message, status_code=409)


def basile_exception_handler(request: Request, exc: BasileException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )


def add_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(BasileException, basile_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
