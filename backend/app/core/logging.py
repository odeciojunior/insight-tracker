import logging
import sys
from typing import Any, Dict, Optional

import structlog
from structlog.types import Processor

from app.core.config import settings


def configure_logging() -> None:
    """Configure structured logging for the application."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    
    # Common processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Environment-specific configuration
    if settings.APP_ENV == "development":
        processors = [*shared_processors, structlog.dev.ConsoleRenderer(colors=True)]
        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processor=structlog.dev.ConsoleRenderer(colors=True)
        )
    else:
        # Production JSON formatting
        processors = [*shared_processors, structlog.processors.JSONRenderer()]
        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processor=structlog.processors.JSONRenderer()
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)
    
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


def setup_logging() -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=settings.LOG_LEVEL,
    )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.LOG_FORMAT == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(settings.LOG_LEVEL)),
        cache_logger_on_first_use=True,
    )
