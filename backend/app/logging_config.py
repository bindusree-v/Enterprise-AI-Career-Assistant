"""
Structured logging configuration using structlog.
Outputs JSON in production, colored console in development.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

from app.config import get_settings


def add_app_context(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add application-level context to every log entry."""
    settings = get_settings()
    event_dict["app"] = settings.app_name
    event_dict["version"] = settings.app_version
    event_dict["env"] = settings.app_env
    return event_dict


def configure_logging() -> None:
    """Configure structlog for the application."""
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_app_context,
    ]

    if settings.is_production:
        # JSON output for production (machine-readable)
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Pretty colored output for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Also configure stdlib logging to route through structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )


def get_logger(name: str = __name__) -> Any:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
