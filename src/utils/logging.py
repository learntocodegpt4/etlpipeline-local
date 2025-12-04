"""Logging utilities with structured logging support"""

import logging
import sys
from pathlib import Path
from typing import Any, Optional

import structlog
from structlog.processors import JSONRenderer, TimeStamper

# Global logger cache
_loggers: dict = {}


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False,
) -> None:
    """Setup structured logging configuration"""

    # Create logs directory if needed
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure standard library logging
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
        handlers=handlers,
        force=True,
    )

    # Structlog processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            JSONRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.processors.ExceptionPrettyPrinter(),
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance"""
    if name not in _loggers:
        _loggers[name] = structlog.get_logger(name)
    return _loggers[name]


class LogContext:
    """Context manager for adding temporary context to logs"""

    def __init__(self, **kwargs: Any):
        self.context = kwargs
        self._tokens: list = []

    def __enter__(self) -> "LogContext":
        for key, value in self.context.items():
            token = structlog.contextvars.bind_contextvars(**{key: value})
            self._tokens.append((key, token))
        return self

    def __exit__(self, *args: Any) -> None:
        for key, _ in self._tokens:
            structlog.contextvars.unbind_contextvars(key)


# Initialize with default settings
setup_logging()
