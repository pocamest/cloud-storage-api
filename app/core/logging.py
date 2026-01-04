import sys
from logging.config import dictConfig

from app.core.config import settings


def setup_logging() -> None:
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "{levelname} {asctime} {name} {module} {message}",
                "style": "{",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "default",
            },
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": settings.log_level,
            },
        },
    }

    dictConfig(LOGGING_CONFIG)
