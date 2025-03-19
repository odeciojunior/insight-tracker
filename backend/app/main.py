from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid

from app.core.config import settings
from app.core.logging import configure_logging, get_logger, append_context_to_log

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


@app.get("/health")
async def health_check():
    """Endpoint para verificação de saúde da API"""
    logger.debug("Health check realizado")
    return {"status": "healthy"}


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
