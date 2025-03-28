from typing import Dict, Any, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from jose.exceptions import JWTError

from app.core.logging import get_logger

logger = get_logger(__name__)

class APIError(Exception):
    """Base API error class."""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API errors."""
    logger.error(
        f"API error: {exc.message}",
        status_code=exc.status_code,
        path=request.url.path,
        details=exc.details
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
            "path": request.url.path
        }
    )

async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    logger.error(
        "Validation error",
        path=request.url.path,
        errors=[{"loc": err["loc"], "msg": err["msg"]} for err in exc.errors()]
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "path": request.url.path
        }
    )

async def jwt_error_handler(request: Request, exc: JWTError) -> JSONResponse:
    """Handle JWT validation errors."""
    logger.error(
        f"JWT error: {str(exc)}",
        path=request.url.path
    )
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "Invalid authentication credentials",
            "path": request.url.path
        },
        headers={"WWW-Authenticate": "Bearer"}
    )
