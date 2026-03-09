"""Configuração de structured logging com structlog."""

import logging
import sys

import structlog
from asgi_correlation_id import correlation_id

from app.core.config import settings


def add_correlation_id(
    _logger: logging.Logger, _method_name: str, event_dict: dict
) -> dict:
    """Injeta correlation_id do request atual nos logs."""
    cid = correlation_id.get()
    if cid:
        event_dict["correlation_id"] = cid
    return event_dict


def setup_logging() -> None:
    """Configura structlog + stdlib logging."""
    is_local = settings.ENVIRONMENT == "local"
    log_level = logging.DEBUG if is_local else logging.INFO

    # Processors compartilhados
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_correlation_id,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if is_local:
        # Dev: output colorido e legível
        renderer = structlog.dev.ConsoleRenderer()
    else:
        # Prod: JSON para ferramentas de observabilidade
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)

    # Silenciar logs verbosos de libs
    for noisy in ("httpx", "httpcore", "asyncio", "apscheduler.executors"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
