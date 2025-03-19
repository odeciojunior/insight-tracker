import logging
import sys
from typing import Any, Dict, Optional

import structlog
from structlog.types import Processor

from app.core.config import settings


def configure_logging() -> None:
    """
    Configura o sistema de logging para a aplicação.
    
    Em ambiente de desenvolvimento, usa um formato legível por humanos.
    Em produção, usa JSON para facilitar a ingestão em sistemas de monitoramento.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    
    # Processadores comuns para todos os ambientes
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Configuração específica baseada no ambiente
    if settings.APP_ENV == "development":
        # Formatação colorida e legível para desenvolvimento
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True, sort_keys=False),
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.dev.ConsoleRenderer(colors=True, sort_keys=False),
            ]
        )
    else:
        # Formatação JSON para produção
        processors = [
            *shared_processors,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ]
        )
    
    # Configurar structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configurar logging padrão
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
    
    # Reduzir verbosidade de alguns loggers externos
    for logger_name in ["uvicorn", "uvicorn.error", "fastapi"]:
        logging.getLogger(logger_name).handlers = []
        logging.getLogger(logger_name).propagate = True
    
    # Reduzir logs muito verbosos
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """
    Retorna um logger configurado para o módulo/contexto especificado.
    
    Args:
        name: Nome opcional do logger. Se não fornecido, infere do chamador.
    
    Returns:
        Um logger estruturado configurado para o contexto.
    """
    return structlog.get_logger(name)


def append_context_to_log(**kwargs: Any) -> None:
    """
    Adiciona contexto aos logs de forma global.
    
    Útil para adicionar informações como ID da requisição, usuário atual etc.
    
    Args:
        **kwargs: Pares chave-valor para adicionar ao contexto dos logs.
    """
    structlog.contextvars.clear_contextvars()
    for key, value in kwargs.items():
        structlog.contextvars.bind_contextvars(**{key: value})
