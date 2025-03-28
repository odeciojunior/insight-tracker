from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid

from app.core.config import settings
from app.core.logging import configure_logging, get_logger, append_context_to_log
from app.db import init_db

# Configurar logging antes de qualquer outra coisa
configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Configurar CORS
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Initialize database connections
init_db(app)

# Import and include routers
from app.api.router import api_router
app.include_router(api_router, prefix="/api")

from app.api.middleware import RateLimitMiddleware, RequestLoggingMiddleware

# Add middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

from fastapi.exceptions import RequestValidationError
from jose.exceptions import JWTError
from app.core.errors import (
    APIError,
    api_error_handler,
    validation_error_handler,
    jwt_error_handler
)

# Register error handlers
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(JWTError, jwt_error_handler)

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware para adicionar request_id e outras informações úteis aos logs"""
    request_id = str(uuid.uuid4())
    # Adicionar request_id ao contexto dos logs
    append_context_to_log(request_id=request_id)
    
    logger.info(
        "Request iniciada",
        path=request.url.path,
        method=request.method,
        client=request.client.host if request.client else None,
    )
    
    try:
        response = await call_next(request)
        logger.info(
            "Request finalizada",
            status_code=response.status_code,
        )
        return response
    except Exception as e:
        logger.exception("Erro não tratado durante o processamento da request")
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno do servidor", "request_id": request_id},
        )


@app.get("/")
async def root():
    """Endpoint raiz para verificar se a API está funcionando"""
    logger.info("Endpoint raiz acessado")
    return {"message": "Bem-vindo ao Insight Tracker API"}

from app.core.health import health_checker

@app.get("/health")
async def health_check():
    """Get detailed health status of the application."""
    db_status = await health_checker.check_databases()
    system_resources = health_checker.check_system_resources()
    process_info = health_checker.check_process_info()
    
    return {
        "status": "healthy" if all(db_status.values()) else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "databases": db_status,
        "system": system_resources,
        "process": process_info
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(
        f"Iniciando aplicação em modo de desenvolvimento",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
    )
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_RELOAD,
    )
