#  This work is based on original code developed and copyrighted by TNO 2020.
#  Subsequent contributions are licensed to you by the developers of such code and are
#  made available to the Project under one or several contributor license agreements.
#
#  This work is licensed to you under the Apache License, Version 2.0.
#  You may obtain a copy of the license at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Contributors:
#      TNO         - Initial implementation
#  Manager:
#      TNO

import logging
import logging.config

from typing import List, Any
import structlog
from src.settings import FLASK_DEBUG
from structlog.threadlocal import merge_threadlocal

timestamper = structlog.processors.TimeStamper(fmt="iso")
shared_processors: List[Any] = [
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.stdlib.PositionalArgumentsFormatter(),
    timestamper,
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.UnicodeDecoder(),
]

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "colored": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(colors=True),
                "foreign_pre_chain": shared_processors,
            },
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(sort_keys=True),
                "foreign_pre_chain": shared_processors,
            },
        },
        "handlers": {
            "default": {
                "level": "INFO" if not FLASK_DEBUG else "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "colored" if FLASK_DEBUG else "json",
            }
        },
        "loggers": {
            "": {"handlers": ["default"], "level": "INFO"},
            "src": {
                "handlers": ["default"],
                "level": "INFO" if FLASK_DEBUG else "DEBUG",
                "propagate": False,
            },
        },
    }
)


structlog.configure(
    processors=[structlog.contextvars.merge_contextvars, merge_threadlocal]
    + shared_processors
    + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


def get_logger(name):
    return structlog.get_logger(name)
